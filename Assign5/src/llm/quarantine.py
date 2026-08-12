import json
import datetime
from pathlib import Path
from typing import Dict, Any

QUARANTINE_FILE_PATH = Path(__file__).parent.parent.parent / "logs" / "quarantine.jsonl"

def log_quarantine(input_text: str, raw_output: str, error_details: str, prompt_version: str, repair_attempted: bool = False):
    """
    Logs failed or unrepairable model outputs to logs/quarantine.jsonl.
    """
    QUARANTINE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "input_text": input_text,
        "raw_output": raw_output,
        "error": error_details,
        "repair_attempted": repair_attempted
    }
    with open(QUARANTINE_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
