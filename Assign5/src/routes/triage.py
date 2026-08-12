import os
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.llm.schema import TriageRequest, TriageResponse, get_stub_response
from src.llm.client import call_llm_raw

router = APIRouter()

@router.post(
    "/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    summary="Triage customer support message"
)
async def triage_message(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid JSON body provided.", "field": "body"}
        )

    try:
        validated_request = TriageRequest(**body)
    except ValidationError as e:
        errors = e.errors()
        field_name = ".".join(str(loc) for loc in errors[0]["loc"]) if errors else "text"
        error_msg = errors[0]["msg"] if errors else "Invalid input data."
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"Validation failed for field '{field_name}': {error_msg}",
                "field": field_name,
                "errors": errors
            }
        )

    # Check stub mode
    stub_mode = os.environ.get("LLM_STUB", "0") == "1"
    if stub_mode:
        return get_stub_response()

    # Stage 2: Call model directly with prompt v1
    raw_content, usage = call_llm_raw(validated_request.text)
    
    # Simple parse for Stage 2 (Stage 3 adds strict validation & repair)
    import json
    cleaned_content = raw_content.strip()
    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.strip("`")
        if cleaned_content.startswith("json"):
            cleaned_content = cleaned_content[4:].strip()
    
    try:
        parsed_json = json.loads(cleaned_content)
        return TriageResponse(**parsed_json)
    except Exception:
        # Fallback for Stage 2 before Stage 3 repair pipeline
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"raw_output": raw_content, "usage": usage}
        )
