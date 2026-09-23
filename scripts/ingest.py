#!/usr/bin/env python3
"""Upload everything in data/personal/ into a private 'Personal' knowledge base.
The assistant then retrieves from it when answering (RAG)."""
import os, sys, pathlib, requests, urllib3
urllib3.disable_warnings()  # local self-signed cert

ROOT = pathlib.Path(__file__).resolve().parent.parent
env = dict(l.strip().split("=", 1) for l in (ROOT / ".env").read_text().splitlines()
           if "=" in l and not l.startswith("#"))
BASE = os.environ.get("BASE_URL", "https://localhost:8443")
KB_NAME = "Personal"

s = requests.Session(); s.verify = False
r = s.post(f"{BASE}/api/v1/auths/signin",
           json={"email": env["ADMIN_EMAIL"], "password": env["ADMIN_PASSWORD"]})
r.raise_for_status()
s.headers["Authorization"] = f"Bearer {r.json()['token']}"

kbs = s.get(f"{BASE}/api/v1/knowledge/").json()
kbs = kbs if isinstance(kbs, list) else kbs.get("items", [])
kb = next((k for k in kbs if k["name"] == KB_NAME), None)
if not kb:
    kb = s.post(f"{BASE}/api/v1/knowledge/create",
                json={"name": KB_NAME, "description": "My personal information"}).json()
print("Knowledge base:", kb["id"])

files = [p for p in (ROOT / "data/personal").rglob("*") if p.is_file() and p.name != "README.txt"]
if not files:
    sys.exit("Nothing in data/personal/ yet. Add .txt/.md/.pdf/.docx files first.")
for p in files:
    with open(p, "rb") as f:
        up = s.post(f"{BASE}/api/v1/files/", files={"file": (p.name, f)})
    if not up.ok:
        print("FAILED upload:", p.name, up.text[:200]); continue
    add = s.post(f"{BASE}/api/v1/knowledge/{kb['id']}/file/add", json={"file_id": up.json()["id"]})
    print("OK " if add.ok else "FAILED", p.name)
print("Done. In the chat, type # and pick 'Personal' to use it, or attach it to a custom model.")
