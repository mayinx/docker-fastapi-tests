MAKEFLAGS += --no-print-directory

# ==============================================================================
# ⚙️  CONFIG
# ==============================================================================
COMPOSE_PROJECT := docker-exam
COMPOSE := docker compose -p $(COMPOSE_PROJECT)

start-project:
	@echo "# [make start-project] Start stack (detached)"
	${COMPOSE} up -d

stop-project:
	@echo "# [make stop-project] Stop stack + remove containers/networks"
	${COMPOSE} down

stop-all:
	@echo "# [make stop-all] Stop stack + remove orphans (quiet)"
	@$(COMPOSE) down --remove-orphans  >/dev/null 2>&1 || true
	@echo "# Compose project stopped (if it was running)."

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
	@echo "# [make reset] Reset to a guaranteed clean state (stop-all + kill-api + free-port-8000)"
	@$(MAKE) stop-all
	@$(MAKE) kill-api
	@$(MAKE) free-port-8000

ps:
	@echo "# [make ps] Show running services for this compose project"
	$(COMPOSE) ps

ps-api:
	@echo "# [makle ps-api] Show running api service container(s)"
	$(COMPOSE) ps	

wait-auth:
	@echo "# [make wait-auth] Wait until auth_test finishes"
	@$(COMPOSE) wait auth_test >/dev/null 2>&1 || true

# ==============================================================================
# 🔎 LOGGING / INSPECTION
# ==============================================================================
logs:
	echo "# [make logs] View real-time logs for the whole stack"
	$(COMPOSE) logs -f

logs-api:
	echo "[make logs-api] # Follow logs for the api service" 
	$(COMPOSE) logs -f api

logs-auth:
	@echo "# [make logs-auth] Print auth_test logs (tail=200)"
	@$(COMPOSE) logs --no-color --tail=200 auth_test || true
