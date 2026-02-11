#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Docker Exam Pipeline Runner
# - Project: docker-exam
# - Purpose: one-command, reproducible run for the exam submission artifacts
#
# What this script does (high level):
# 1) Resets to a clean state (stops compose project, removes stray "api", frees port 8000)
# 2) Starts the compose stack (API + test container(s))
# 3) Waits for the auth test container to finish
# 4) Prints auth test logs to the terminal (for quick verification)
# 5) Copies the aggregated shared log to ./log.txt (exam requirement)
# 6) Shuts everything down again (avoids port/container conflicts on rerun)
# ==============================================================================

PROJECT_NAME="docker-exam"
TIMESTAMP_FMT="+%Y-%m-%d %H:%M:%S"

printf '\n========================================================================================\n'
printf '   *** Docker Exam Pipeline (project: %s) — START %s ***\n' "${PROJECT_NAME}" "$(date "${TIMESTAMP_FMT}")"
printf '========================================================================================\n'

# ------------------------------------------------------------------------------
# 1) Clean start (idempotent)
# - make reset:
#   - stops compose project (if running)
#   - removes stray container named "api" (if it exists)
#   - frees host port 8000 (if any container publishes it)
# ------------------------------------------------------------------------------
make reset

# ------------------------------------------------------------------------------
# 2) Start stack (detached) + show status
# - make start-project: docker compose up -d
# - make ps:           docker compose ps
# ------------------------------------------------------------------------------
make start-project
make ps

# ------------------------------------------------------------------------------
# 3) Run + wait for authentication tests + show logs
# - make wait-auth: blocks until auth_test exits (exit code drives pipeline)
# - make logs-auth: prints last lines of auth_test logs for visibility
# ------------------------------------------------------------------------------
make wait-auth
make logs-auth


# ------------------------------------------------------------------------------
# 3) Run + wait for authorization tests + show logs
# ------------------------------------------------------------------------------
make wait-authz
make logs-authz

# ------------------------------------------------------------------------------
# 4) Create submission snapshot log.txt (exam requirement)
# - shared/api_test.log is written by the test container when LOG=1
# ------------------------------------------------------------------------------
if [ -f "./shared/api_test.log" ]; then
  cp ./shared/api_test.log ./log.txt
  printf '# Copied aggregated log: ./shared/api_test.log -> ./log.txt\n'
else
  printf '# Note: ./shared/api_test.log not found (LOG may be disabled or tests produced no file)\n'
fi

# ------------------------------------------------------------------------------
# 5) Shutdown (keeps reruns conflict-free)
# ------------------------------------------------------------------------------
make stop-all

printf '========================================================================================\n'
printf '   *** Docker Exam Pipeline (project: %s) — END   %s ***\n' "${PROJECT_NAME}" "$(date "${TIMESTAMP_FMT}")"
printf '========================================================================================\n\n'
