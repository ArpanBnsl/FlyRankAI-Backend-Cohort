import json
import logging
import sys
import datetime
from typing import Dict, Any

# Configure standard logger to stdout following Twelve-Factor App principles
logger = logging.getLogger("llm_cost_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_cost_event(
    prompt_version: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float,
    repair_count: int,
    status: str = "success"
):
    """
    Logs structured JSON line detailing call metrics and estimated cost.
    """
    log_entry = {
        "event": "llm_call",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "duration_ms": round(duration_ms, 2),
        "repair_count": repair_count,
        "status": status
    }
    logger.info(json.dumps(log_entry))
