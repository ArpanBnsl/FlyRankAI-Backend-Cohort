import os
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.llm.schema import TriageRequest, TriageResponse, get_stub_response

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
        # Extract offending field name
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

    # Place holder for model call in subsequent stages
    return get_stub_response()
