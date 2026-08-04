"""All PostgreSQL access for the task API lives in this module."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured. Copy .env.example to .env first.")
    return database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(_database_url(), row_factory=dict_row)


def initialize_database() -> None:
    """Create the schema and add example rows only when the table is empty."""
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
            """)
        cursor.execute("SELECT COUNT(*) AS count FROM tasks")
        if cursor.fetchone()["count"] == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [("task 1", False), ("task 2", True), ("task 3", False)],
            )
