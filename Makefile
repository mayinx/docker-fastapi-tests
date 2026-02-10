# ==============================================================================
# ⚙️  CONFIG
# ==============================================================================
COMPOSE_PROJECT := docker-exam
COMPOSE := docker compose -p $(COMPOSE_PROJECT)

start-project:
	${COMPOSE} up -d

stop-project:
	# Shutdown the entire stack and remove internal networks
	${COMPOSE} down

stop-all:
	# Shutdown + remove orphaned containers
	$(COMPOSE) down --remove-orphans

# 🔥 Common exam issue: a stray container named "api" blocks compose if container_name: api was ever used
kill-api:
	@docker rm -f api >/dev/null 2>&1 && echo "Removed stray container: api" || echo "No stray container named: api"


ps:
	# Show running services/containers for this compose project
	$(COMPOSE) ps

ps-api:
	# Show only running services/containers for api
	$(COMPOSE) ps	


# ==============================================================================
# 🔎 LOGGING / INSPECTION
# ==============================================================================
logs:
	# View real-time logs for the whole stack
	$(COMPOSE) logs -f

logs-api:
	# Follow logs for the api service 
	$(COMPOSE) logs -f api


