import json
import os
import re
import time
import random
from pathlib import Path
from typing import Dict, Any, Tuple
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError, BadRequestError
from pydantic import ValidationError

from src.llm.schema import TriageResponse, get_stub_response
from src.llm.quarantine import log_quarantine
from src.llm.logger import log_cost_event

PROMPT_VERSION = "v1"
PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / f"triage-{PROMPT_VERSION}.md"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RETRY_ATTEMPTS = 3

class LLMDisabledException(Exception):
    """Raised when kill switch LLM_ENABLED=false is active."""
    pass

class LLMTimeoutException(Exception):
    """Raised when API call times out."""
    pass

def is_llm_enabled() -> bool:
    val = os.environ.get("LLM_ENABLED", "true").lower()
    return val in ("1", "true", "yes", "on")

def load_prompt_template() -> str:
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"Prompt template not found at {PROMPT_FILE_PATH}")
    return PROMPT_FILE_PATH.read_text(encoding="utf-8")

def get_openai_client() -> OpenAI:
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    # Explicitly override default 10-min timeout and default retries
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        max_retries=0
    )

def extract_json_str(text: str) -> str:
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            return match.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and start < end:
        return cleaned[start:end+1]
    return cleaned

def parse_and_validate(raw_text: str) -> TriageResponse:
    json_str = extract_json_str(raw_text)
    data = json.loads(json_str)
    return TriageResponse(**data)

def _execute_api_call_with_retries(client: OpenAI, model: str, messages: list) -> Any:
    """
    Executes chat completion with explicit exponential backoff + jitter retries
    for 429, 5xx, and timeouts ONLY. Never retries on 400, 401, or 403.
    """
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            return client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=messages
            )
        except (AuthenticationError, BadRequestError) as e:
            # 401, 403, 400: Do NOT retry! Fail immediately.
            raise e
        except (APITimeoutError, APIConnectionError, RateLimitError, APIError) as e:
            status_code = getattr(e, "status_code", None)
            # Retriable errors: RateLimit (429), 5xx server errors, timeouts, connection errors
            is_retriable = (
                isinstance(e, (APITimeoutError, APIConnectionError, RateLimitError)) or
                (status_code and status_code >= 500)
            )
            if not is_retriable or attempt == MAX_RETRY_ATTEMPTS:
                if isinstance(e, APITimeoutError):
                    raise LLMTimeoutException("LLM API request timed out after 30.0 seconds.")
                raise e
            
            # Check Retry-After header if present
            retry_after = None
            if hasattr(e, "response") and e.response is not None:
                headers = getattr(e.response, "headers", {})
                retry_after_hdr = headers.get("retry-after") or headers.get("Retry-After")
                if retry_after_hdr:
                    try:
                        retry_after = float(retry_after_hdr)
                    except ValueError:
                        pass
            
            if retry_after is not None:
                sleep_time = retry_after
            else:
                # Exponential backoff with jitter: 1s, 2s, 4s + jitter
                base_backoff = 2 ** (attempt - 1)
                jitter = random.uniform(0.1, 0.5)
                sleep_time = base_backoff + jitter

            time.sleep(sleep_time)

def call_llm_with_repair(user_text: str) -> Tuple[TriageResponse, Dict[str, Any]]:
    """
    Orchestrates kill switch, explicit timeouts, retry policy,
    repair retry loop, structured cost logging, and quarantine.
    """
    # 1. Kill switch check
    if not is_llm_enabled():
        raise LLMDisabledException("LLM features are currently disabled by kill switch.")

    system_prompt = load_prompt_template()
    client = get_openai_client()
    model = os.environ.get("LLM_MODEL", "openrouter/free")

    user_payload = json.dumps({"user_input": user_text})
    start_time = time.time()
    
    primary_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Categorize the following customer message:\n{user_payload}"}
    ]

    # Primary call with retries
    response = _execute_api_call_with_retries(client, model, primary_messages)

    raw_content = response.choices[0].message.content or ""
    total_prompt_tokens = response.usage.prompt_tokens if response.usage else 0
    total_completion_tokens = response.usage.completion_tokens if response.usage else 0

    try:
        validated = parse_and_validate(raw_content)
        duration_ms = (time.time() - start_time) * 1000.0
        log_cost_event(
            prompt_version=PROMPT_VERSION,
            model=model,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            duration_ms=duration_ms,
            repair_count=0
        )
        metadata = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "duration_ms": duration_ms,
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "repair_count": 0
        }
        return validated, metadata
    except (json.JSONDecodeError, ValidationError, Exception) as first_error:
        error_msg = str(first_error)
        
        # Repair attempt
        repair_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Categorize the following customer message:\n{user_payload}"},
            {"role": "assistant", "content": raw_content},
            {
                "role": "user",
                "content": (
                    f"Your previous answer was rejected for the following validation error:\n"
                    f"{error_msg}\n\n"
                    f"Please return ONLY a valid, corrected JSON object matching the required schema."
                )
            }
        ]

        repair_response = _execute_api_call_with_retries(client, model, repair_messages)

        repair_raw_content = repair_response.choices[0].message.content or ""
        if repair_response.usage:
            total_prompt_tokens += repair_response.usage.prompt_tokens
            total_completion_tokens += repair_response.usage.completion_tokens

        duration_ms = (time.time() - start_time) * 1000.0

        try:
            validated = parse_and_validate(repair_raw_content)
            log_cost_event(
                prompt_version=PROMPT_VERSION,
                model=model,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                duration_ms=duration_ms,
                repair_count=1
            )
            metadata = {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
                "duration_ms": duration_ms,
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "repair_count": 1
            }
            return validated, metadata
        except (json.JSONDecodeError, ValidationError, Exception) as second_error:
            log_cost_event(
                prompt_version=PROMPT_VERSION,
                model=model,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                duration_ms=duration_ms,
                repair_count=1,
                status="failed"
            )
            log_quarantine(
                input_text=user_text,
                raw_output=repair_raw_content,
                error_details=f"Primary error: {error_msg} | Repair error: {str(second_error)}",
                prompt_version=PROMPT_VERSION,
                repair_attempted=True
            )
            raise ValueError(f"Output failed schema validation after 1 repair retry: {str(second_error)}")
