import json
import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure root workspace is in import path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from src.llm.client import call_llm_with_repair, PROMPT_VERSION
from src.llm.schema import get_stub_response

EVAL_CASES_PATH = Path(__file__).parent / "cases.json"

def run_eval():
    if not EVAL_CASES_PATH.exists():
        print(f"Eval cases file not found at {EVAL_CASES_PATH}")
        sys.exit(1)

    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    stub_mode = os.environ.get("LLM_STUB", "0") == "1"
    print(f"=== Running LLM Triage Eval Set (Prompt: {PROMPT_VERSION}, Mode: {'STUB' if stub_mode else 'LIVE'}) ===")
    print(f"Date: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    total = len(cases)
    passed_category = 0
    passed_urgency = 0
    exact_matches = 0
    failures = []

    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        exp_cat = case["expected_category"]
        exp_urg = case["expected_urgency"]

        if stub_mode:
            res = get_stub_response()
        else:
            try:
                res, _ = call_llm_with_repair(user_input)
            except Exception as e:
                print(f"[FAIL] Case #{case_id}: Exception raised: {e}")
                failures.append({
                    "id": case_id,
                    "input": user_input,
                    "expected": f"cat={exp_cat}, urg={exp_urg}",
                    "actual": f"EXCEPTION: {str(e)}"
                })
                continue

        cat_match = (res.category.value == exp_cat)
        urg_match = (res.urgency.value == exp_urg)
        exact_match = cat_match and urg_match

        if cat_match:
            passed_category += 1
        if urg_match:
            passed_urgency += 1
        if exact_match:
            exact_matches += 1
            print(f"[PASS] Case #{case_id}: Category='{res.category.value}', Urgency='{res.urgency.value}', Confidence={res.confidence}")
        else:
            print(f"[FAIL] Case #{case_id}: Expected (cat='{exp_cat}', urg='{exp_urg}'), Got (cat='{res.category.value}', urg='{res.urgency.value}')")
            failures.append({
                "id": case_id,
                "input": user_input,
                "expected": f"cat={exp_cat}, urg={exp_urg}",
                "actual": f"cat={res.category.value}, urg={res.urgency.value}"
            })

    print("\n=== Eval Summary ===")
    print(f"Total Test Cases: {total}")
    print(f"Exact Matches (Category & Urgency): {exact_matches}/{total} ({exact_matches/total*100:.1f}%)")
    print(f"Category Accuracy: {passed_category}/{total} ({passed_category/total*100:.1f}%)")
    print(f"Urgency Accuracy: {passed_urgency}/{total} ({passed_urgency/total*100:.1f}%)")

    if failures:
        print("\nFailed Cases:")
        for f_item in failures:
            print(f"  - Case #{f_item['id']} Input: '{f_item['input']}' | Expected: {f_item['expected']} | Actual: {f_item['actual']}")

    return exact_matches, total

if __name__ == "__main__":
    run_eval()
