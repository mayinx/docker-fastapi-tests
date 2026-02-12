MAKEFLAGS += --no-print-directory

# ==============================================================================
# ⚙️  CONFIG
# ==============================================================================
COMPOSE_PROJECT := docker-exam
COMPOSE := docker compose -p $(COMPOSE_PROJECT)

# Export host UID/GID for docker-compose `user:` mapping (avoid bash's readonly UID var)
# Ensure containers that write to bind-mounted volumes (./shared) use the host user.
# Prevents root-owned files like ./shared/api_test.log - which would break reset-logs.
export HOST_UID := $(shell id -u)
export HOST_GID := $(shell id -g)

# ==============================================================================
# 🚀 CORE PIPELINE (start/stop/reset)
# ==============================================================================
start-project:
	@echo "# [make start-project] Start stack (detached) and rebuild images if Dockerfiles changed"
	@$(COMPOSE) up -d --build

stop-project:
	@echo "# [make stop-project] Stop stack + remove containers/networks"
	@$(COMPOSE) down

stop-all:
	@echo "# [make stop-all] Stop stack + remove orphans (quiet)"
	@$(COMPOSE) down --remove-orphans >/dev/null 2>&1 || true
	@echo "# Compose project stopped (if it was running)."

# ------------------------------------------------------------------------------
# Clean-start helpers (common exam issues)
# ------------------------------------------------------------------------------

# 🔥 Common exam issue: a stray container named "api" blocks compose if container_name: api was ever used
kill-api:
	@echo "# [make kill-api] Remove stray container named 'api' (if it exists)"
	@docker rm -f api >/dev/null 2>&1 && echo "# Removed stray container: api" || echo "# No stray container named: api"

# Kill anything (container) that currently publishes host port 8000
free-port-8000:
	@echo "# [make free-port-8000] Free host port 8000 by removing containers that publish it (if any)"
	@docker ps --filter "publish=8000" -q | xargs -r docker rm -f
	@echo "# Freed host port 8000 (if it was in use by containers)."

reset:
	@echo "# [make reset] Reset to a guaranteed clean state (stop-all + kill-api + free-port-8000 + reset-logs)"
	@$(MAKE) stop-all
	@$(MAKE) kill-api
	@$(MAKE) free-port-8000
	@$(MAKE) reset-logs

# ==============================================================================
# 🔎 STATUS / INSPECTION
# ==============================================================================
ps:
	@echo "# [make ps] Show running services for this compose project"
	@$(COMPOSE) ps

ps-api:
	@echo "# [make ps-api] Show running api service container(s)"
	@$(COMPOSE) ps api

# ==============================================================================
# ⏳ TEST RUNNERS (wait + logs per test container)
# ==============================================================================
wait-auth:
	@echo "# [make wait-auth] Wait until auth_test finishes"
	@$(COMPOSE) wait auth_test >/dev/null 2>&1 || true

logs-auth:
	@echo "# [make logs-auth] Print auth_test logs (tail=200)"
	@$(COMPOSE) logs --no-color --tail=200 auth_test || true

wait-authz:
	@echo "# [make wait-authz] Wait until authz_test finishes"
	@$(COMPOSE) wait authz_test >/dev/null 2>&1 || true

logs-authz:
	@echo "# [make logs-authz] Print authz_test logs (tail=200)"
	@$(COMPOSE) logs --no-color --tail=200 authz_test || true

wait-content:
	@echo "# [make wait-content] Wait until content_test finishes"
	@$(COMPOSE) wait content_test >/dev/null 2>&1 || true

logs-content:
	@echo "# [make logs-content] Print content_test logs (tail=200)"
	@$(COMPOSE) logs --no-color --tail=200 content_test || true

# ==============================================================================
# 📜 LIVE LOGGING (follow)
# ==============================================================================
logs:
	@echo "# [make logs] View real-time logs for the whole stack"
	@$(COMPOSE) logs -f

logs-api:
	@echo "# [make logs-api] Follow logs for the api service"
	@$(COMPOSE) logs -f api

# ==============================================================================
# 🧾 LOG FILE HANDLING
# ==============================================================================

snapshot-log:
	@echo "# [make snapshot-log] Copy shared/api_test.log -> ./log.txt (exam artifact)"
	@if [ -f "./shared/api_test.log" ]; then \
		cp ./shared/api_test.log ./log.txt; \
		echo "# Copied aggregated log: ./shared/api_test.log -> ./log.txt"; \
	else \
		echo "# Note: ./shared/api_test.log not found (LOG may be disabled or tests produced no file)"; \
	fi

reset-logs:
	@echo "# [make reset-logs] Clear shared/api_test.log + local log.txt (fresh run)"
	@rm -f ./log.txt || true
	@rm -f ./shared/api_test.log || true
	@touch ./shared/api_test.log	

# ==============================================================================
# 🧯 DOCKER RECOVERY (use only when Docker/BuildKit is broken)
# ==============================================================================
repair-buildkit:
	@echo "# [make repair-buildkit] Fix BuildKit snapshot/cache issues (destructive)"
	@docker builder prune -af

repair-docker:
	@echo "# [make repair-docker] Prune unused Docker data (VERY destructive: images/volumes)"
	@docker system prune -af --volumes

repair-all:
	@echo "# [make repair-all] reset + repair-buildkit + repair-docker (VERY destructive)"
	@$(MAKE) reset
	@$(MAKE) repair-buildkit
	@$(MAKE) repair-docker
