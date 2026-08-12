import os
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from openai import AuthenticationError, APIError

from src.llm.schema import TriageRequest, TriageResponse, get_stub_response
from src.llm.client import (
    call_llm_with_repair,
    LLMDisabledException,
    LLMTimeoutException
)

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

    try:
        validated_response, metadata = call_llm_with_repair(validated_request.text)
        return validated_response
    except LLMDisabledException as kill_sw_err:
        # Kill switch active: return deterministic fallback response with 503 or 200 fallback
        fallback = get_stub_response()
        fallback.reason = "Kill switch active (LLM_ENABLED=false): Returning deterministic fallback."
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": str(kill_sw_err),
                "fallback": fallback.model_dump()
            }
        )
    except LLMTimeoutException as timeout_err:
        # 504 Gateway Timeout when model call times out
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "detail": str(timeout_err),
                "error": "GATEWAY_TIMEOUT"
            }
        )
    except AuthenticationError as auth_err:
        # 401 Unauthorized (invalid key, never retried)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": f"LLM Provider Authentication Failed: {str(auth_err)}",
                "error": "UNAUTHORIZED"
            }
        )
    except ValueError as val_err:
        # 422 HTTP status code for output schema validation failure after repair attempt
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": f"Model output validation failed: {str(val_err)}",
                "error": "UNPROCESSABLE_ENTITY",
                "quarantined": True
            }
        )
    except APIError as api_err:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "detail": f"Upstream LLM Provider Error: {str(api_err)}",
                "error": "BAD_GATEWAY"
            }
        )
