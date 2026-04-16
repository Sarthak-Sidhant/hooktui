import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from hooktui.models import WebhookRequest

def get_db_path() -> Path:
    config_dir = Path.home() / ".config" / "hooktui"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "data.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT NOT NULL,
                query_params TEXT NOT NULL,
                body TEXT,
                timestamp TEXT NOT NULL,
                client_ip TEXT
            )
        """)

def save_request(req: WebhookRequest) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO requests (id, method, url, headers, query_params, body, timestamp, client_ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.id,
                req.method,
                req.url,
                json.dumps(req.headers),
                json.dumps(req.query_params),
                req.body,
                req.timestamp.isoformat(),
                req.client_ip,
            ),
        )

def get_all_requests() -> list[WebhookRequest]:
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM requests ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        
    requests = []
    for row in rows:
        requests.append(
            WebhookRequest(
                id=row["id"],
                method=row["method"],
                url=row["url"],
                headers=json.loads(row["headers"]),
                query_params=json.loads(row["query_params"]),
                body=row["body"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                client_ip=row["client_ip"],
            )
        )
    return requests

def delete_request(req_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM requests WHERE id = ?", (req_id,))

def clear_requests() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM requests")
