import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple
from openai import OpenAI
from pydantic import ValidationError

from src.llm.schema import TriageResponse
from src.llm.quarantine import log_quarantine

PROMPT_VERSION = "v1"
PROMPT_FILE_PATH = Path(__file__).parent.parent / "prompts" / f"triage-{PROMPT_VERSION}.md"

def load_prompt_template() -> str:
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"Prompt template not found at {PROMPT_FILE_PATH}")
    return PROMPT_FILE_PATH.read_text(encoding="utf-8")

def get_openai_client() -> OpenAI:
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    return OpenAI(base_url=base_url, api_key=api_key)

def extract_json_str(text: str) -> str:
    """Strips markdown code blocks and extracts raw JSON string."""
    cleaned = text.strip()
    if "```" in cleaned:
        # Match content inside ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            return match.group(1).strip()
    # Fallback to finding first '{' and last '}'
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and start < end:
        return cleaned[start:end+1]
    return cleaned

def parse_and_validate(raw_text: str) -> TriageResponse:
    json_str = extract_json_str(raw_text)
    data = json.loads(json_str)
    return TriageResponse(**data)

def call_llm_with_repair(user_text: str) -> Tuple[TriageResponse, Dict[str, Any]]:
    """
    Calls the LLM, validates output against TriageResponse schema.
    If parsing or schema validation fails, performs EXACTLY ONE repair retry.
    If repair also fails, logs to quarantine and raises ValueError.
    Returns (validated_response, metadata).
    """
    system_prompt = load_prompt_template()
    client = get_openai_client()
    model = os.environ.get("LLM_MODEL", "openrouter/free")

    user_payload = json.dumps({"user_input": user_text})

    # Primary attempt
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Categorize the following customer message:\n{user_payload}"}
        ]
    )

    raw_content = response.choices[0].message.content or ""
    total_prompt_tokens = response.usage.prompt_tokens if response.usage else 0
    total_completion_tokens = response.usage.completion_tokens if response.usage else 0
    repair_count = 0

    try:
        validated = parse_and_validate(raw_content)
        metadata = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "repair_count": 0
        }
        return validated, metadata
    except (json.JSONDecodeError, ValidationError, Exception) as first_error:
        error_msg = str(first_error)
        repair_count = 1
        
        # Repair attempt: send broken output + error back to model
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

        repair_response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=repair_messages
        )

        repair_raw_content = repair_response.choices[0].message.content or ""
        if repair_response.usage:
            total_prompt_tokens += repair_response.usage.prompt_tokens
            total_completion_tokens += repair_response.usage.completion_tokens

        try:
            validated = parse_and_validate(repair_raw_content)
            metadata = {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "repair_count": 1
            }
            return validated, metadata
        except (json.JSONDecodeError, ValidationError, Exception) as second_error:
            # Second attempt failed -> log to quarantine
            log_quarantine(
                input_text=user_text,
                raw_output=repair_raw_content,
                error_details=f"Primary error: {error_msg} | Repair error: {str(second_error)}",
                prompt_version=PROMPT_VERSION,
                repair_attempted=True
            )
            raise ValueError(f"Output failed schema validation after 1 repair retry: {str(second_error)}")
