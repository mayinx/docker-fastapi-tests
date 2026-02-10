# Implementation Steps / Exam Log

> ## 👤 About
> This README contains my personal implementation log (“exam build diary”).  
> It was written while building the solution to keep milestones, decisions, and commands reproducible.

---

## 📌 Index
- [1) Repo scaffold + API container baseline](#1-repo-scaffold--api-container-baseline)

---

## 1) Repo scaffold + API container baseline

### Goal
- Create a git-tracked project folder for the exam hand-in 
- Validate that the provided API image can be started and reached on `/status` and `/docs`.

---

### 1.1 Create repo structure

From your workspace folder:

```bash
mkdir -p docker-exam-fastapi-tests
cd docker-exam-fastapi-tests

mkdir -p tests/authentication tests/authorization tests/content
mkdir -p shared logs

touch docker-compose.yml setup.sh log.txt README.md README_IMPLEMENTATION.md README_REMARKS.md .gitignore
git init
```


### 1.2 Add the API service (docker-compose baseline)

- FYI: We use a prebuild image for the api container - so we don't build the api-image ourselves - we just run it (the test contaienrs taht will be implemented later on  will use Dockerfiles of course)
- As per requriments, the API is to be made available on port 8000 of the host machine.
- Test containers don't need port publishing (see. ports: ...) for teh api-container at all - they can reach the API over the internal Docker network via the service name (http://api:8000). But having ports is convenient for manual checks like curl http://localhost:8000/status or opening /docs in the browser


In `docker-compose.yml`:

```yaml
services:
  api:
    image: datascientest/fastapi:1.0.0
    container_name: api
    ports:
      - "8000:8000"
    networks:
      - sentiment_net
    volumes:
      # shared artifacts (test containers will write api_test.log here)
      - ./shared:/shared

networks:
  sentiment_net:
    driver: bridge
```

This way ...

- the api gets a stable service name (`api`) for Compose DNS (later tests can use `http://api:8000/...`).
- `./shared` will be used later for the single merged `api_test.log`.

### 1.3 Pull + run the API and validate endpoints

Pull the image:

```bash
docker image pull datascientest/fastapi:1.0.0
```

Start via Compose:

```bash
docker compose up -d
docker compose ps
```

Smoke tests from the host (expected: /status returns 1 and /docs (FastAPI-docs) is reachable in browser):

```bash
# API up?
# Call the /status endpoint and print the 
# response body (expected: 1)
# -s = “silent”: hide noise / just response body
curl -s "http://localhost:8000/status"; echo

# FastAPI’s UI with Docs reachable?
# Calls /docs but prints only the HTTP status code
# (expected: 200).
# - -s = silent (no progress meter)
# - -o /dev/null        = throw away the response body
# - -w "%{http_code}\n" = “write-out”: after the request
# finishes, print the HTTP status code + newline
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/docs"
```

View logs (optional):

```bash
docker compose logs -f api
```

Stop/cleanup:

```bash
docker compose down
```

#### 1.4 Git commit (baseline)
git add .
git commit -m "chore: scaffold repo + compose baseline for API container"

#### 1.4 Result (Milestone 1)

- docker-compose.yml starts the provided API image
- API reachable on http://localhost:8000/status and http://localhost:8000/docs