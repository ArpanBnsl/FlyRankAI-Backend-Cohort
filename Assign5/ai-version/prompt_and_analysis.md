# Bonus Stage: The AI Rematch & Comparative Analysis

## 1. Specification Prompt Used for AI Generation

```text
Build a FastAPI Python endpoint `POST /triage` that takes a customer support message text and returns clean structured JSON classification.
Requirements:
1. Input schema: JSON body with `text` string (1-2000 chars). Reject invalid input with HTTP 400 naming the field.
2. Output schema: JSON object with category (billing|bug|feature|other), urgency (low|normal|high), confidence (0.0-1.0), and reason (string).
3. Prompt: Store system prompt in `prompts/triage-v1.md`. Send system prompt as system role and user text as user role.
4. Robustness: Parse output, validate against Pydantic schema. If validation fails, retry ONCE with error message. If second attempt fails, return HTTP 422 and log to `logs/quarantine.jsonl`.
5. Production Readiness: Set explicit client timeout to 30.0s. Implement retries ONLY for 429/5xx/timeouts (never 400/401/403). Log token metrics to stdout. Add kill switch `LLM_ENABLED=false`. Add `LLM_STUB=1` offline mode.
```

---

## 2. Comparative Analysis ("AI vs Me")

| Feature / Aspect | Hand-Crafted Solution | AI-Generated Solution | Key Observation |
|---|---|---|---|
| **Client Timeout** | Explicitly set to `30.0s` on `OpenAI` client instance. | Left default SDK timeout (10 minutes) or omitted timeout parameter. | AI frequently forgets default SDK timeout is 10 minutes, exposing API to hung HTTP connections. |
| **Retry Policy** | Set `max_retries=0` on client; explicitly retried ONLY 429/5xx/timeouts with exponential backoff & jitter. | Used default SDK retries or caught generic `Exception` and retried 401 invalid API key errors. | AI retried unrecoverable 401 auth errors, burning daily quota pointlessly. |
| **Prompt Injection Protection** | Encoded user content as JSON string (`json.dumps({"user_input": text})`) inside user role. | Concatenated user string directly into user prompt or system prompt. | Hand-crafted approach isolates untrusted text so user content cannot break out of JSON framing. |
| **Quarantine & Failure Path** | Logged full payload + prompt version + raw output + error to `logs/quarantine.jsonl` and returned 422. | Either returned `500 Internal Server Error` or swallowed error and returned fake fallback without logging. | Hand-crafted approach quarantines bad data cleanly without crashing or faking success. |
| **Kill Switch & Stub Mode** | Cleanly separated `LLM_ENABLED` (530/fallback) and `LLM_STUB` (fake schema-valid object). | Combined stub and kill switch into a single flag or ignored environment flags. | Granular control allows offline dev/testing (`LLM_STUB`) separately from emergency operational kill switch (`LLM_ENABLED`). |

---

## 3. Rematch Prompt & Refinement
Upon updating the prompt with explicit negative constraints ("Do NOT retry on 401, do NOT use default 10-minute timeout"), the generated code correctly set `timeout=30.0` and `max_retries=0`. This demonstrates that AI code quality is directly bounded by the precision of the specification.
