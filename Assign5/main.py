import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from src.routes.triage import router as triage_router

load_dotenv()

app = FastAPI(
    title="Support Triage API with LLM Integration",
    description="Backend API for customer support classification powered by structured LLM responses.",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    field_name = ".".join(str(loc) for loc in errors[0]["loc"]) if errors else "body"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": f"Validation failed for field '{field_name}'",
            "field": field_name,
            "errors": errors
        }
    )

app.include_router(triage_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "stub_mode": os.environ.get("LLM_STUB", "0") == "1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
