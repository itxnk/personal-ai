#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v docker >/dev/null || { echo "Install Docker first: https://docs.docker.com/get-docker/"; exit 1; }

if [ ! -f .env ]; then
  cp .env.example .env
  read -rp "Admin email: " email
  sed -i "s|^ADMIN_EMAIL=.*|ADMIN_EMAIL=${email}|" .env
  sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '=+/')|" .env
  sed -i "s|^WEBUI_SECRET_KEY=.*|WEBUI_SECRET_KEY=$(openssl rand -hex 32)|" .env
  chmod 600 .env
  echo "Created .env with fresh secrets (chmod 600)."
fi

set -a; source .env; set +a
mkdir -p data/personal data/ollama data/webui data/caddy
chmod 700 data

docker compose up -d
echo "Pulling models (first run downloads several GB)..."
docker compose exec ollama ollama pull "$CHAT_MODEL"
docker compose exec ollama ollama pull "$EMBED_MODEL"

echo
echo "Ready: https://localhost:8443"
echo "Login: $ADMIN_EMAIL  /  password is in .env (ADMIN_PASSWORD)"
echo "Next: put your files in data/personal/ then run: python3 scripts/ingest.py"
