#!/usr/bin/env bash
set -euo pipefail

# This script runs everytime the container is started.

# Wait for the inner Docker daemon (DinD) to come up
for i in $(seq 1 30); do
  docker info >/dev/null 2>&1 && break
  sleep 1
done

# --- Ollama bridge -----------------------------------------------------------
# Nested containers can't reliably route to Docker Desktop's host alias.
# Instead: socat listens on 11434 in THIS devcontainer and relays to the real
# host. Nested containers reach the devcontainer via host-gateway (bridge GW).
# (socat itself is installed once in postcreate.sh.)
if ! pgrep -f "socat.*11434" >/dev/null 2>&1; then
  nohup socat TCP-LISTEN:11434,fork,reuseaddr,bind=0.0.0.0 \
    TCP:host.docker.internal:11434 >/tmp/ollama-proxy.log 2>&1 &
fi
ADD_HOST="--add-host=host.docker.internal:host-gateway"
# -----------------------------------------------------------------------------

# --- Shared RAG network ------------------------------------------------------
# User-defined bridge network so containers resolve each other by name via
# Docker's built-in DNS. This lets n8n reach Qdrant at http://qdrant:6333
# (the default bridge does NOT provide name resolution).
RAG_NET="rag"
if ! docker network inspect "$RAG_NET" >/dev/null 2>&1; then
  docker network create "$RAG_NET" >/dev/null
fi
# -----------------------------------------------------------------------------

# --- Open WebUI ---
if ! docker container inspect open-webui >/dev/null 2>&1; then
  docker run -d \
    -p 3000:8080 \
    $ADD_HOST \
    -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    -v open-webui:/app/backend/data \
    --name open-webui \
    --restart always \
    ghcr.io/open-webui/open-webui:v0.10.2
else
  docker start open-webui >/dev/null
fi

# --- n8n ---
if ! docker container inspect n8n >/dev/null 2>&1; then
  docker run -d \
    -p 5678:5678 \
    $ADD_HOST \
    --network "$RAG_NET" \
    -e GENERIC_TIMEZONE="America/New_York" \
    -e TZ="America/New_York" \
    -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
    -e N8N_RUNNERS_ENABLED=true \
    -e N8N_SECURE_COOKIE=false \
    -v n8n_data:/home/node/.n8n \
    --name n8n \
    --restart always \
    docker.n8n.io/n8nio/n8n:2.30.2
else
  docker start n8n >/dev/null
fi
# Ensure n8n is on the RAG network even if it was created before this network
# existed (idempotent; no-op if already attached).
docker network connect "$RAG_NET" n8n 2>/dev/null || true

# --- Qdrant (vector DB for RAG) ---
# REST + web dashboard on 6333. No API key by default (local classroom use).
# In n8n, create a Qdrant credential with URL http://qdrant:6333 (key blank).
if ! docker container inspect qdrant >/dev/null 2>&1; then
  docker run -d \
    -p 6333:6333 \
    --network "$RAG_NET" \
    -v qdrant_storage:/qdrant/storage \
    --name qdrant \
    --restart always \
    qdrant/qdrant:v1.18.2
else
  docker start qdrant >/dev/null
fi

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "Devcontainer ready. Let's build! 🚀🚀🚀"
