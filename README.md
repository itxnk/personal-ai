# personal-ai

A private, self-hosted, ChatGPT-style assistant that knows *your* information. Nothing leaves your machine.

| Piece | Job |
|---|---|
| **Ollama** | Runs the LLM locally |
| **Open WebUI** | ChatGPT-like interface + knowledge base (RAG) over your files |
| **Caddy** | HTTPS in front of everything |

## Quick start
```bash
git clone <your-repo-url> personal-ai && cd personal-ai
./scripts/setup.sh            # generates secrets, starts containers, pulls models
cp ~/my-notes/* data/personal/
python3 scripts/ingest.py     # loads your files into the "Personal" knowledge base
```
Open **https://localhost:8443** (accept the local certificate). In a chat, type `#` and choose **Personal**, or attach it to a custom model under *Workspace → Models* so it is always used.

Requirements: Docker, ~16 GB RAM for the 8B model (GPU strongly recommended). Change `CHAT_MODEL` in `.env` for a bigger or smaller model.

## "Training" on your data: what's realistic
Training a huge model from scratch takes millions of dollars of GPUs. What works:
1. **RAG (included)**: your files are indexed and retrieved at question time. Best for facts about you, easy to update or delete.
2. **LoRA fine-tuning (later, optional)**: teaches style and habits, not reliable facts. Use Unsloth or Axolotl on a GPU with your exported chats. Load the result into Ollama via a Modelfile.

## Security model
- No ports exposed except `127.0.0.1:8443`; Ollama and the UI are only on internal Docker networks.
- Sign-up disabled; a single admin created from `.env` (chmod 600, git-ignored).
- Telemetry and external APIs off; secure, strict cookies; HSTS and security headers.
- `no-new-privileges`, and Caddy drops all capabilities except the one it needs.
- `data/` is git-ignored. **Never commit personal files or `.env`.**
- Turn on **full-disk encryption** (BitLocker/LUKS/FileVault) so data at rest is protected; run `scripts/backup.sh` for GPG-encrypted backups.
- Remote access: use WireGuard or Tailscale rather than opening a port to the internet.
- Keep images current: `docker compose pull && docker compose up -d`.

## Commands
```bash
docker compose ps        # running processes
docker compose logs -f   # logs
docker compose down      # stop
```
# personal-ai
