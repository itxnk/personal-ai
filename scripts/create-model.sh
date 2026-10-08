#!/usr/bin/env bash
# Build a custom Ollama model "personal-assistant" whose system prompt comes from data/personal/system.md
# (git-ignored; start from examples/system.example.md). Facts about you live in the RAG knowledge base.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

SYS=data/personal/system.md
[ -f "$SYS" ] || { echo "Create $SYS first (copy examples/system.example.md and edit it)."; exit 1; }

docker compose exec -T ollama sh -c "cat > /tmp/Modelfile" <<MODELFILE
FROM ${CHAT_MODEL}
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
SYSTEM """$(cat "$SYS")"""
MODELFILE
docker compose exec ollama ollama create personal-assistant -f /tmp/Modelfile
echo "Done. Pick 'personal-assistant' in Open WebUI and attach the Personal knowledge base."
