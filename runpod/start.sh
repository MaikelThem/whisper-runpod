#!/usr/bin/env bash
set -uo pipefail
echo "[whisper-runpod] boot $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[whisper-runpod] python=$(command -v python3) $($(command -v python3) --version 2>&1)"
echo "[whisper-runpod] handler=/handler.py"
exec python3 -u /handler.py
