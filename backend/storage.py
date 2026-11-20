"""Small SQLite repository. An atomic transaction serializes project mutations."""

import json
import os
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

active_database = ContextVar("active_database", default=None)
expected_version = ContextVar("expected_version", default=None)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(prefix):
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def database_path():
    path = Path(active_database.get() or os.getenv("DATABASE_PATH", "data/requirements.db"))
    return path if path.is_absolute() else PROJECT_ROOT / path


@contextmanager
def connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version VALUES (1);
        CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, document TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, role TEXT NOT NULL, expires REAL NOT NULL);
        """)


@contextmanager
def transaction():
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        yield conn


def get_project(conn, project_id):
    row = conn.execute("SELECT document FROM projects WHERE id=?", (project_id,)).fetchone()
    return json.loads(row[0]) if row else None


def save_project(conn, project):
    timestamp = datetime.now(timezone.utc)
    previous = datetime.fromisoformat(project["updated_at"])
    project["updated_at"] = max(timestamp, previous + timedelta(microseconds=1)).isoformat()
    conn.execute(
        "INSERT INTO projects(id, document) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET document=excluded.document",
        (project["id"], json.dumps(project)),
    )


def audit(project, user, action, details):
    project["audit"].append(
        dict(id=uid("AUD"), at=now(), actor=user["name"], role=user["role"], action=action, details=details)
    )


def run(project, agent, inputs, outcome, confidence=0.65, evidence=None, provider="local-rules-v1"):
    project["runs"].append(
        dict(
            id=uid("RUN"),
            at=now(),
            agent=agent,
            version="1.0",
            provider=provider,
            input_ids=inputs,
            outcome=outcome,
            confidence=confidence,
            evidence=evidence or [],
        )
    )


def new_project(name, description, jurisdiction, synthetic=False):
    return dict(
        id=uid("PRJ"),
        name=name,
        description=description,
        jurisdiction=jurisdiction,
        synthetic=synthetic,
        created_at=now(),
        updated_at=now(),
        sources=[],
        requirements=[],
        flags=[],
        questions=[],
        mappings=[],
        sdlc=None,
        audit=[],
        runs=[],
        mode="deterministic demo",
    )
