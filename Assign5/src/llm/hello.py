import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_connection():
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("LLM_API_KEY", "dummy_key")
    model = os.environ.get("LLM_MODEL", "openrouter/free")
    stub_mode = os.environ.get("LLM_STUB", "0") == "1"

    if stub_mode or api_key == "dummy_key":
        print(f"[STUB/TEST] Ready! Connected via stub mode (Model: {model})")
        return "ready"

    client = OpenAI(base_url=base_url, api_key=api_key)
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly the word: ready"}]
    )
    content = res.choices[0].message.content
    print(f"[LIVE] Response from {model}: {content}")
    return content

if __name__ == "__main__":
    test_connection()
