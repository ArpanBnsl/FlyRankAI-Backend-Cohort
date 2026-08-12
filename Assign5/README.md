# Support Triage API with LLM Integration

**FlyRank Internship · Backend Track · Week 7 · Assignment A17**

## Overview
This production-grade API endpoint (`POST /triage`) takes messy, unstructured customer support text, queries a Large Language Model (LLM), and returns clean, validated JSON. It features strict input validation, schema enforcement, repair retry loops, cost logging, a kill switch, and an offline stub mode.

## Provider Flexibility & Configuration
Three environment variables define the provider and model configuration:
- `LLM_BASE_URL`: Base URL of the OpenAI-compatible provider (e.g., `https://openrouter.ai/api/v1` or `http://localhost:11434/v1/`)
- `LLM_API_KEY`: API Key for authentication
- `LLM_MODEL`: Model identifier (e.g., `openrouter/free` or `gemma3:1b`)

Because the application relies solely on standard environment variables and the official OpenAI client SDK, swapping providers (e.g., switching between OpenRouter hosted API and Ollama local LLM) requires zero code changes—only updating three values in `.env`.

## Setup & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```
3. Start the server (with `LLM_STUB=1` for offline stub testing):
   ```bash
   LLM_STUB=1 uvicorn main:app --port 8000
   ```

## Runnable Curl Commands

### 1. Valid Request (200 OK)
```bash
curl -X POST "http://localhost:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{"text": "I was double charged on my invoice #1042 for the annual subscription."}'
```

**Expected Response (Schema Valid JSON):**
```json
{
  "category": "bug",
  "urgency": "high",
  "confidence": 0.95,
  "reason": "Stub mode active: Identified login error as a critical bug."
}
```

### 2. Deliberately Invalid Request (400 Bad Request)
Missing required `text` field:
```bash
curl -X POST "http://localhost:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Expected Response (400 Bad Request):**
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
