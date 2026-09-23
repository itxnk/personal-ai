#!/usr/bin/env bash
# Encrypted backup of chats + knowledge base (not the model files). Prompts for a passphrase.
set -euo pipefail
cd "$(dirname "$0")/.."
out="backup-$(date +%F).tar.gpg"
tar -C data -cf - webui personal | gpg --symmetric --cipher-algo AES256 -o "$out"
echo "Wrote $out  (restore: gpg -d $out | tar -C data -xf -)"
