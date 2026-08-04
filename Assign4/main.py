"""FastAPI entry point for the Supabase Auth assignment."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from supabase import Client, create_client

load_dotenv()

app = FastAPI(title="Supabase Auth API", version="1.0.0")


@lru_cache
def get_supabase() -> Client:
    """Build a client from server-side configuration without exposing secrets."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
        )
    return create_client(url, key)


def get_client() -> Client:
    return get_supabase()


@app.get("/", tags=["system"])
def root() -> dict[str, Any]:
    return {"name": "Supabase Auth API", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config", tags=["system"])
def config_status() -> dict[str, bool]:
    """Expose only whether the required server configuration is present."""
    return {
        "supabase_configured": bool(
            os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")
        )
    }
