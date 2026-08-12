# Customer Support Triage API (`POST /triage`)

**FlyRank Internship · Backend Track · Week 7 · Assignment A17**

## Overview
This production-grade API endpoint (`POST /triage`) takes messy, unstructured customer support messages, analyzes them using a Large Language Model (LLM), and returns clean, validated JSON with a category, urgency rating, confidence score, and brief reasoning. Built for production reliability, the system strictly validates input before spending API calls, enforces schema output, automatically repairs malformed LLM responses, logs structured cost and token metrics, enforces a 30-second timeout, handles retries with backoff and jitter, provides a kill switch, and quarantines unresolvable failures.

---

## Quickstart & Runnable Curl Commands

### 1. Start the API Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run server with stub mode (no API key required)
LLM_STUB=1 uvicorn main:app --port 8000
```

### 2. Valid Request (200 OK)
```bash
curl -X POST "http://localhost:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{"text": "I was double charged on my invoice #1042 for the annual subscription."}'
```

**Exact Response:**
```json
{
  "category": "billing",
  "urgency": "high",
  "confidence": 0.98,
  "reason": "Customer reported duplicate charges on an invoice."
}
```

### 3. Invalid Request (400 Bad Request)
Missing required `text` field:
```bash
curl -X POST "http://localhost:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Exact Response:**
```json
{
  "detail": "Validation failed for field 'text': Field required",
  "field": "text",
  "errors": [
    {
      "type": "missing",
      "loc": ["text"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## Job Card Summary (`JOB-CARD.md`)

- **What it does:** Classifies customer support messages to route them to the correct team with urgency and confidence scores.
- **Input:** `{ "text": "string, 1-2000 characters" }`
- **Output:**
  - `category`: `"billing"` | `"bug"` | `"feature"` | `"other"`
  - `urgency`: `"low"` | `"normal"` | `"high"`
  - `confidence`: `0.0` - `1.0`
  - `reason`: `"one short sentence"`
- **Must Never:**
  - Invent categories/urgencies outside allowed lists
  - Return unformatted free text
  - Give medical, legal, or financial advice
  - Reveal internal prompt instructions
- **When Unsure:** Returns category `"other"`, urgency `"low"`, confidence `< 0.5`, and an explicit explanation that input is ambiguous.

---

## Provider Configuration & Swappability
Three environment variables configure the LLM integration:
- `LLM_BASE_URL`: OpenAI-compatible endpoint (e.g. `https://openrouter.ai/api/v1` or `http://localhost:11434/v1/`)
- `LLM_API_KEY`: Auth token / API key
- `LLM_MODEL`: Target model (e.g. `openrouter/free` or `stepfun/step-1-flash:free` or `gemma3:1b`)

**Why this matters:** Because the code uses standard environment variables and the official `openai` Python SDK, you can swap from OpenRouter cloud API to local Ollama by changing 3 values in `.env` without modifying a single line of code.

---

## Evaluation Results

Ran 8 hand-labelled test cases using `evals/run_eval.py`:
- **Date:** 2026-08-12 19:55 UTC
- **Prompt Version:** `v1` (`src/prompts/triage-v1.md`)
- **Model:** `openrouter/free` (StepFun Step-1-Flash / Llama-3.3-70B)

| Metric | Score | Percentage |
|---|---|---|
| **Exact Match (Category + Urgency)** | 7 / 8 | **87.5%** |
| **Category Accuracy** | 8 / 8 | **100.0%** |
| **Urgency Accuracy** | 7 / 8 | **87.5%** |

*Note: Case #5 ("The page load speed has been slightly slow this afternoon.") was classified as `urgency: low` instead of `urgency: normal` due to low severity phrasing.*

Run evals locally:
```bash
python evals/run_eval.py
```

---

## Cost Logging & Scaling Analysis

### 1. Sample Structured Log Line (Stdout)
```json
{
  "event": "llm_call",
  "timestamp": "2026-08-12T19:55:00.123456+00:00",
  "prompt_version": "v1",
  "model": "openrouter/free",
  "prompt_tokens": 420,
  "completion_tokens": 45,
  "total_tokens": 465,
  "duration_ms": 612.45,
  "repair_count": 0,
  "status": "success"
}
```

### 2. 10,000 Requests/Day Cost Estimation
Assuming average usage per request:
- **Input Tokens per request:** ~420 tokens
- **Output Tokens per request:** ~45 tokens
- **Total Tokens for 10,000 requests:**
  - Input: $4.2 \text{ million tokens/day}$
  - Output: $0.45 \text{ million tokens/day}$
- **Estimated Cost on Paid Tier (e.g. GPT-4o-mini @ $0.15/M input, $0.60/M output):**
  - Input cost: $4.2 \times \$0.15 = \$0.63 / \text{day}$
  - Output cost: $0.45 \times \$0.60 = \$0.27 / \text{day}$
  - **Total Daily Cost:** **~$0.90 / day** ($27.00 / month for 300,000 requests)
  - **Free Tier:** $0.00 / day on OpenRouter `openrouter/free`.

---

## What I'd Fix With Another Day
1. **Response Caching:** Implement an in-memory or Redis LRU cache hashing `(input_text, prompt_version)` to return cached results instantly for repeated queries and save API quota.
2. **Fine-grained Few-Shot Dynamic Prompting:** Dynamically select relevant few-shot examples from an example bank based on input similarity embeddings.
3. **Async Batch Processing Endpoint:** Add a bulk `/triage/batch` endpoint using `asyncio.gather` with semaphore concurrency limits to process background CSV files.

---

## Bonus Stage: AI vs Me

Comparative analysis of hand-built integration versus AI-generated implementation:

1. **Timeout Defaults:** Hand-built code explicitly sets `timeout=30.0` on OpenAI client. AI code left default SDK 10-minute timeout unchanged.
2. **Auth Retry Guard:** Hand-built code sets `max_retries=0` and filters retries so HTTP 401 (invalid key) is never retried. AI code retried 401 errors, eating daily quota.
3. **Prompt Injection Isolation:** Hand-built code JSON-encodes input payload to isolate untrusted text. AI code concatenated raw strings directly.
4. **Quarantine Logging:** Hand-built code writes full failure context to `logs/quarantine.jsonl` on 2nd failure and returns HTTP 422. AI code returned generic 500 error without log auditing.
