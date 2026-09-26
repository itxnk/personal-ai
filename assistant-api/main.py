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

app = FastAPI(
    title="Personal AI Assistant Tools",
    version="0.2.0",
    description=(
        "Private personal-assistant tools for Open WebUI. "
        "The LLM can use these endpoints to manage reminders, tasks, "
        "calendar events, and prepare phone calls."
    ),
)


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
    title: str = Field(min_length=1, max_length=300, description="Short reminder title.")
    due_at: str = Field(
        description="ISO-8601 datetime, preferably with timezone, e.g. 2026-09-27T09:00:00+05:00."
    )
    notes: str = Field(default="", max_length=2000, description="Optional reminder notes.")


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=300, description="Task title.")
    due_at: Optional[str] = Field(
        default=None,
        description="Optional ISO-8601 due datetime with timezone."
    )
    priority: str = Field(
        default="normal",
        description="Task priority such as low, normal, high, or urgent."
    )


class EventIn(BaseModel):
    title: str = Field(min_length=1, max_length=300, description="Calendar event title.")
    starts_at: str = Field(description="ISO-8601 event start datetime with timezone.")
    ends_at: Optional[str] = Field(default=None, description="Optional ISO-8601 event end datetime.")
    location: str = Field(default="", max_length=500, description="Optional event location.")
    notes: str = Field(default="", max_length=2000, description="Optional event notes.")


class DoneIn(BaseModel):
    done: bool = True


@app.get(
    "/api/health",
    operation_id="assistant_health",
    summary="Check personal assistant health",
)
def health():
    return {"status": "ok", "service": "personal-ai-assistant"}


@app.get(
    "/api/reminders",
    operation_id="list_reminders",
    summary="List reminders",
    description="Use this when the user asks what reminders they have or what reminders are scheduled.",
)
def reminders():
    conn = db()
    rows = conn.execute("SELECT * FROM reminders ORDER BY due_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post(
    "/api/reminders",
    operation_id="create_reminder",
    summary="Create a reminder",
    description="Create a reminder for the user. Convert the requested time to an ISO-8601 datetime with timezone.",
)
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


@app.patch(
    "/api/reminders/{item_id}",
    operation_id="complete_reminder",
    summary="Complete or reopen a reminder",
)
def complete_reminder(item_id: int, item: DoneIn):
    conn = db()
    cur = conn.execute("UPDATE reminders SET done=? WHERE id=?", (int(item.done), item_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Reminder not found")
    return {"ok": True, "id": item_id, "done": item.done}


@app.get(
    "/api/tasks",
    operation_id="list_tasks",
    summary="List tasks",
    description="Use this when the user asks about their tasks or to-do list.",
)
def tasks():
    conn = db()
    rows = conn.execute("SELECT * FROM tasks ORDER BY done, due_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post(
    "/api/tasks",
    operation_id="create_task",
    summary="Create a task",
    description="Create a task for the user's to-do list.",
)
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


@app.patch(
    "/api/tasks/{item_id}",
    operation_id="complete_task",
    summary="Complete or reopen a task",
)
def complete_task(item_id: int, item: DoneIn):
    conn = db()
    cur = conn.execute("UPDATE tasks SET done=? WHERE id=?", (int(item.done), item_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "Task not found")
    return {"ok": True, "id": item_id, "done": item.done}


@app.get(
    "/api/events",
    operation_id="list_events",
    summary="List calendar events",
    description="Use this when the user asks what events or appointments they have.",
)
def events():
    conn = db()
    rows = conn.execute("SELECT * FROM events ORDER BY starts_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post(
    "/api/events",
    operation_id="create_event",
    summary="Create a calendar event",
    description="Create a local calendar event for the user.",
)
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


@app.get(
    "/api/agenda",
    operation_id="get_agenda",
    summary="Get the user's agenda",
    description="Return reminders, tasks, and calendar events together. Use this for questions like 'what do I have today?' or 'show my schedule'.",
)
def agenda():
    conn = db()
    reminders_rows = conn.execute(
        "SELECT * FROM reminders WHERE done=0 ORDER BY due_at"
    ).fetchall()
    tasks_rows = conn.execute(
        "SELECT * FROM tasks WHERE done=0 ORDER BY due_at"
    ).fetchall()
    events_rows = conn.execute(
        "SELECT * FROM events ORDER BY starts_at"
    ).fetchall()
    conn.close()
    return {
        "reminders": [dict(r) for r in reminders_rows],
        "tasks": [dict(r) for r in tasks_rows],
        "events": [dict(r) for r in events_rows],
    }


@app.get(
    "/api/notifications/due",
    operation_id="get_due_notifications",
    summary="Get due reminders",
    description="Return reminders that are due and not completed.",
)
def due_notifications():
    now = datetime.now(timezone.utc).isoformat()
    conn = db()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE done=0 AND due_at <= ? ORDER BY due_at",
        (now,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get(
    "/api/call",
    operation_id="prepare_call",
    summary="Prepare a phone call",
    description=(
        "Prepare a tel: link for a phone call. Never claim that a call was placed. "
        "This endpoint only prepares the call and requires explicit user confirmation."
    ),
)
def prepare_call(name: str, phone: str):
    return {
        "name": name,
        "phone": phone,
        "tel_url": f"tel:{phone}",
        "requires_confirmation": True,
    }


@app.get("/")
def assistant_web():
    return FileResponse(WEB_PATH)
