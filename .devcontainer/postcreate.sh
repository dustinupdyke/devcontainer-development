#!/usr/bin/env bash
set -euo pipefail

# One-time provisioning. Runs once at container create and survives stop/start,
# so durable, filesystem-level setup belongs here.

# Install socat once; poststart.sh's Ollama-bridge proxy relies on it.
if ! command -v socat >/dev/null 2>&1; then
  sudo apt-get update -qq && sudo apt-get install -y -qq socat >/dev/null
fi
