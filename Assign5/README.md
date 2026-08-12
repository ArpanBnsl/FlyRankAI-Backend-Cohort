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
1. Clone repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```
3. Test provider connectivity:
   ```bash
   python -m src.llm.hello
   ```
