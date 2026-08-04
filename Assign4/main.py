"""FastAPI entry point for the Supabase Auth assignment."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from supabase import Client, create_client

load_dotenv()
app = FastAPI(title="Supabase Auth API", version="1.0.0")


@lru_cache
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(status_code=503, detail="Supabase is not configured.")
    return create_client(url, key)


def get_client() -> Client:
    return get_supabase()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=72)


def serialize_user(user: Any) -> dict[str, Any] | None:
    return None if user is None else {"id": str(user.id), "email": user.email}


def serialize_session(session: Any) -> dict[str, Any] | None:
    if session is None:
        return None
    return {"access_token": session.access_token, "token_type": session.token_type, "expires_at": session.expires_at}


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["auth"])
def signup(credentials: Credentials, client: Client = Depends(get_client)) -> dict[str, Any]:
    try:
        result = client.auth.sign_up(credentials.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to create account.") from exc
    return {"user": serialize_user(result.user), "session": serialize_session(result.session), "message": "Check your email to confirm the account if confirmation is enabled."}


@app.get("/", tags=["system"])
def root() -> dict[str, Any]:
    return {"name": "Supabase Auth API", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config", tags=["system"])
def config_status() -> dict[str, bool]:
    return {"supabase_configured": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))}