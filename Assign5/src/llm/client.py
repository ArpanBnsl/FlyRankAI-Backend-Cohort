import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple
from openai import OpenAI

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

def call_llm_raw(user_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Loads prompt v1, sends user text as a separate user message,
    and calls the model with temperature=0.0.
    Returns (raw_content, usage_metadata).
    """
    system_prompt = load_prompt_template()
    client = get_openai_client()
    model = os.environ.get("LLM_MODEL", "openrouter/free")

    # Safely JSON encode user input to protect against system prompt injection
    user_payload = json.dumps({"user_input": user_text})

    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Categorize the following customer message:\n{user_payload}"}
        ]
    )

    content = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0,
        "model": model,
        "prompt_version": PROMPT_VERSION
    }
    return content, usage
