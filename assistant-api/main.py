from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/app/data")
DB_PATH = DATA_DIR / "assistant.db"
WEB_PATH = APP_DIR / "static" / "index.html"

app = FastAPI(title="Personal AI Assistant API", version="0.1.0")


def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_at TEXT NOT NULL,
            notes TEXT DEFAULT '',
            done INTEGER DEFAULT 0
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_at TEXT,
            priority TEXT DEFAULT 'normal',
            done INTEGER DEFAULT 0
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            ends_at TEXT,
            location TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )"""
    )
    conn.commit()
    return conn


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    due_at: str
    notes: str = ""


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    due_at: Optional[str] = None
    priority: str = "normal"


class EventIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    starts_at: str
    ends_at: Optional[str] = None
    location: str = ""
    notes: str = ""


class DoneIn(BaseModel):
    done: bool = True


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "personal-ai-assistant"}


@app.get("/api/reminders")
def reminders():
    conn = db()
    rows = conn.execute("SELECT * FROM reminders ORDER BY due_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/reminders")
def create_reminder(item: ReminderIn):
    conn = db()
    cur = conn.execute(
        "INSERT INTO reminders(title,due_at,notes) VALUES(?,?,?)",
        (item.title, item.due_at, item.notes),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reminders WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.patch("/api/reminders/{item_id}")
def complete_reminder(item_id: int, item: DoneIn):
    conn = db()
    cur = conn.execute("UPDATE reminders SET done=? WHERE id=?", (int(item.done), item_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Reminder not found")
    return {"ok": True}


@app.get("/api/tasks")
def tasks():
    conn = db()
    rows = conn.execute("SELECT * FROM tasks ORDER BY done, due_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/tasks")
def create_task(item: TaskIn):
    conn = db()
    cur = conn.execute(
        "INSERT INTO tasks(title,due_at,priority) VALUES(?,?,?)",
        (item.title, item.due_at, item.priority),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.patch("/api/tasks/{item_id}")
def complete_task(item_id: int, item: DoneIn):
    conn = db()
    cur = conn.execute("UPDATE tasks SET done=? WHERE id=?", (int(item.done), item_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Task not found")
    return {"ok": True}


@app.get("/api/events")
def events():
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY starts_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/events")
def create_event(item: EventIn):
    conn = db()
    cur = conn.execute(
        "INSERT INTO events(title,starts_at,ends_at,location,notes) VALUES(?,?,?,?,?)",
        (item.title, item.starts_at, item.ends_at, item.location, item.notes),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM events WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/notifications/due")
def due_notifications():
    now = datetime.now(timezone.utc).isoformat()
    conn = db()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE done=0 AND due_at <= ? ORDER BY due_at",
        (now,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/call")
def prepare_call(name: str, phone: str):
    # Android/iOS can turn this into a call after explicit user confirmation.
    return {
        "name": name,
        "phone": phone,
        "tel_url": f"tel:{phone}",
        "requires_confirmation": True,
    }


@app.get("/")
def assistant_web():
    return FileResponse(WEB_PATH)
