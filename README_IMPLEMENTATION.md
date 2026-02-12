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
- Validate that the provided API image can be started as api-service via docker-compose and reached on `/status` and `/docs`.

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

- FYI: We use a prebuild image for the api container - so we don't build the api-image ourselves - we just run it (the test containers that will be implemented later on will use Dockerfiles of course)
- As per requriments, the API is to be made available on port 8000 of the host machine.
- The test containers don't need port publishing (see. `ports: ...`) for the api-container at all - they can reach the API over the internal Docker network via the service name (http://api:8000). But having `ports` defined is convenient for manual checks like curl http://localhost:8000/status or opening `/docs` in the browser


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
- `./shared` will be used later for the single merged `api_test.log`, produced by the test runs. A shared bind-mount makes it easy for multiple test containers to append to the same log file deterministically.

### 1.3 Pull + run the API and validate its endpoints 

Pull the image:

```bash
docker image pull datascientest/fastapi:1.0.0
```

Now we could run a docker container on base of the pulled image to play with the api like this:

```bash
docker container run -p 8000:8000 datascientest/fastapi:1.0.0
```

But thanks to our docker-compose-config we can start the API via Compose instead:

```bash
# Creates and start all services defined in our Compose file 
# (right now just the api)
# -p: project name  
# -d: detached - run containers in background adn free terminal 
docker compose -p docker-exam up -d

# insepct preocess status to list all running containers on teh hostz 
# related to the current project / docker-compose file  
docker compose -p docker-exam ps
```

Smoke tests from the host against the api: 
- expected: `/status` returns `1` (== healthy api) 
- and /docs (FastAPI-docs) is reachable in browser:

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
docker compose -p docker-exam logs -f api
```

Stop/cleanup:

```bash
docker compose -p docker-exam down
```

We can also check if we can reach the api-endpoints and teh FastAPI Docs UI via the browser:

- http://localhost:8000/status returns 1 if the API is running
- http://localhost:8000/permissions returns a user's permissions (expected at this point of course: {"detail":"Authentication failed"})
- http://localhost:8000/v1/sentiment returns the sentiment analysis using an old model (expected: {"detail":"Authentication failed"})
- http://localhost:8000/v2/sentiment returns the sentiment analysis using a new template (expected: {"detail":"Authentication failed"})
- http://localhost:8000/docs renders the FastAPI Docs UI showing doc on the mentioned api-endpoints 

#### 1.4 Result (Milestone 1)

- docker-compose.yml starts the provided API image
- API reachable on http://localhost:8000/status and http://localhost:8000/docs etc. ...


---

## 2) Authentication test (containerized) - GET /permissions 

> ### General Requirements for all test scenarios:
> - As per the requirements, all test scenarios are to be performed via separate containers - i.e. one dedicated container per test scenario 
> - If an environment variable `LOG` is set to `1` on a test run, then a log should be printed in a log file named `api_test.log`.
> - To create the tests, a starter tenplate (python) is provided    

### Goal for the Authnetication test (exam requirement)
Run a dedicated container that tests authentication logic via the api-route `/permissions`:
- `alice:wonderland`        -> user exists  -> expected `HTTP 200`
- `bob:builder`             -> user exists  -> expected `HTTP 200`
- `clementine:mandarine`    -> nope         -> expected `HTTP 403`

---

### 2.1 Create the authentication test script

Create `tests/authentication/test_authentication.py`
(implementation see there)

```bash
# Usage:
API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
python3 tests/authentication/test_authentication.py
```

What the `test_authentication.py` script does (and why):

- Authentication Tests: It validates the API authentication behavior by calling GET /permissions
with 3 sets of known credentials and checking the expected HTTP status codes.
- Readiness Check/Polling: It includes a readiness check (polling GET /status) to ensure the API is up before testing (because `depends_on` in docker-compose ensures just order - not readiness)
- Shared Logging: If LOG=1, it appends the report to a shared LOG_PATH (default: /shared/api_test.log) so multiple test containers can share one log file later.
- Exits with `0` on success, `1` on failure (important so CI/CD-style pipelines can fail fast).
- Calls the API over the docker compose internal DNS name `api:8000` (no host IP needed).
 
---

### 2.2 Create a Dockerfile for the authentication test image

Create `tests/authentication/Dockerfile`:

~~~Dockerfile
# Use a minimal python base image 
FROM python:3.12-slim

WORKDIR /app

# Install requests - i.e3. only what we need for HTTP calls 
# and don't keep pip's download/cache dir on disk 
RUN pip install --no-cache-dir requests

# Copy the entire `tests/` package tree (test modules + shared helpers) 
# into the image, so `python -m tests...` can import `tests._shared.*` 
# and run the suite via module path.
COPY tests /app/tests

# Default command: run the test module on container start
# (so `docker compose up` triggers the test automatically)
# FYI: Environment vars needed for the script execution are 
# set by docker-compose
# The test are run as a Python module (`-m`), so `tests.*` 
# imports (e.g. `tests._shared...`) work because `tests/` 
# is treated as a package tree.
CMD ["python3", "-m", "tests.authentication.test_authentication"]
~~~

---

### 2.3 Wire the authentication test container into docker-compose

Now we need to update `docker-compose.yml` to add `auth_test`: 

~~~yaml
services:
  api:
    image: datascientest/fastapi:1.0.0
    container_name: api
    ports:
      - "8000:8000" # host:container (so you can curl localhost:8000 for manual checks)
    networks:
      - sentiment_net
    volumes:
      - ./shared:/shared

  auth_test:
    build:
      context: .
      dockerfile: ./tests/authentication/Dockerfile            
    container_name: auth_test
    depends_on:
      - api
    networks:
      - sentiment_net
    environment:
      # LOG=1 => append to shared log file (exam requirement)
      - LOG=1
      # These are optional overrides; defaults in the script are already correct
      - API_ADDRESS=api
      - API_PORT=8000
      - LOG_PATH=/shared/api_test.log
      - HTTP_TIMEOUT=5   
    volumes:
      - ./shared:/shared

networks:
  sentiment_net:
    driver: bridge
~~~

To ensure the test log file is shared, both services mount `./shared:/shared` - all tests can append into one shared file `/shared/api_test.log`. 

We still keep `ports: "8000:8000"` on the API, even if it's not required for inter-container communication - sicne it makes manual debugging fast (`curl http://localhost:8000/status` and `/docs`).

---

### 2.4 Add `setup.sh` as a "Pipeline Runner" (start → run tests → capture logs → cleanup)

We add a small `setup.sh` script that acts as a **pipeline runner** for this exam.

**What it does (in order):**
- **Resets** to a clean state (stops previous compose runs, removes stray containers, frees host port `8000` if needed)
- **Starts** the compose stack (API + test container(s))
- **Waits** for the `auth_test` container to finish (so the run is deterministic)
- **Prints** the `auth_test` logs to the terminal (quick verification)
- **Copies** the aggregated log from `./shared/api_test.log` to `./log.txt` (**exam requirement**)
- **Stops** the stack again (avoids conflicts on rerun)

FYI: the script calls **Makefile targets** to keep the runner readable and DRY (details live in `Makefile`).

Create/update `setup.sh` (simplified excerpt — see implemented file for the full documented version):

~~~bash
#!/usr/bin/env bash
set -euo pipefail

# Clean start (idempotent)
make reset

# Start stack (detached) + show status
make start-project
make ps

# Wait for test completion + print logs
make wait-auth
make logs-auth

# Create submission snapshot log.txt from shared aggregate log (exam requirement)
if [ -f "./shared/api_test.log" ]; then
  cp ./shared/api_test.log ./log.txt
fi

# Shutdown to keep reruns conflict-free
make stop-all
~~~

Make it executable:

~~~bash
chmod +x setup.sh
~~~

### 2.5 Run Milestone 2 (API + Authenticaiton Services)

Clean previous logs (optional but recommended):

~~~bash
rm -f ./shared/api_test.log ./log.txt
~~~

Run via script:

~~~bash
./setup.sh
~~~

Or run manually (useful for iteration):

~~~bash
# Start in background + rebuild test images
docker compose up -d --build

# Check running containers
docker compose ps

# View test output
docker compose logs auth_test

# Check aggregated log
ls -la ./shared/api_test.log
cat ./shared/api_test.log

# Stop everything
docker compose down
~~~

---

## 3) Authorization Test (containerized) — verify access to /v1/sentiment vs /v2/sentiment

**Exam requirement:** 

### Goal
- “Authorization” test suite in a separate container.  
- Validate that authorization rules work:
  - `bob` has access to v1 only
  - `alice` has access to v1 and v2
- For each user, call:
  - `GET /v1/sentiment`
  - `GET /v2/sentiment`
- params: `username`, `password`, `sentence`.

Expected outcomes
- `alice`:
  - `/v1/sentiment` => 200
  - `/v2/sentiment` => 200
- `bob`:
  - `/v1/sentiment` => 200
  - `/v2/sentiment` => 403

### 3.1 Create the authorization test script

Create `tests/authorization/test_authorization.py`  
(implementation: see file)

~~~bash
# Usage (host-run dev):
API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
python3 -m tests.authorization.test_authorization
~~~

What the `test_authorization.py` script does (and why):

- **Authorization Tests:** It validates API authorization by calling the sentiment endpoints and checking **expected HTTP status codes** for each case:
  - `alice` can access `/v1/sentiment` and `/v2/sentiment` → **200**
  - `bob` can access `/v1/sentiment` → **200**
  - `bob` must be blocked on `/v2/sentiment` → **403**
- **Readiness Check / Polling:** It polls `GET /status` until it returns `"1"` before executing tests (because `depends_on` controls startup order, not readiness).
- **Shared Logging:** If `LOG=1`, it appends the suite report to `LOG_PATH` (default: `/shared/api_test.log`) so multiple test containers can write into one shared log file later.
- **Exit Codes for Pipelines:** Exits with `0` only if **all** cases pass, otherwise `1` (so CI/CD-style pipelines can fail fast).
- **Compose DNS by default:** Uses Docker Compose internal DNS by default (`api:8000`). For host-run dev, override with `API_ADDRESS=localhost`.

---



### 3.2 Create the Dockerfile for this test image: `tests/authorization/Dockerfile`

Like for the authentication tests, wWe build a separate test container for the authorization suite as well.
- `python:3.12-slim` provides a minimal Python runtime
- `pip install --no-cache-dir requests` installs the only dependency
  - `--no-cache-dir` tells pip not to store wheel/download caches in the image layer (smaller image)
- `CMD ["python", "..."]` runs the script when the container starts
  - in most images, `python` points to Python 3 (equivalent to `python3`)

Create `tests/authorization/Dockerfile`:

~~~Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install only what we need for HTTP calls
# --no-cache-dir: don't keep pip download 
# caches inside the image layer (smaller image)
RUN pip install --no-cache-dir requests

# Copy the entire `tests/` package tree (test modules + shared helpers) 
# into the image, so `python -m tests...` can import `tests._shared.*` 
# and run the suite via module path.
COPY tests /app/tests

# Default command: run the test module on container start
# (so `docker compose up` triggers the test automatically)
# FYI: Environment vars needed for the script execution are 
# set by docker-compose
# The test are run as a Python module (`-m`), so `tests.*` 
# imports (e.g. `tests._shared...`) work because `tests/` 
# is treated as a package tree.
CMD ["python3", "-m", "tests.authorization.test_authorization"]
~~~

### 3.3 Update `docker-compose.yml`: add the `authz_test` service

We add a second test service/container:
- It builds from `tests/authorization/Dockerfile`
- It uses the same internal API address: `API_ADDRESS=api`, `API_PORT=8000`
- It writes into the same shared log file via the shared volume (`./shared:/shared`)
- `depends_on` ensures the API container starts before the test container starts (readiness is handled by polling in the script)

Add:

~~~yaml
  authz_test:
    build:
      context: .
      dockerfile: ./tests/authorization/Dockerfile            
    container_name: authz_test
    environment:
      - API_ADDRESS=api
      - API_PORT=8000
      - LOG=1
      - LOG_PATH=/shared/api_test.log
      - HTTP_TIMEOUT=5
    depends_on:
      - api
    networks:
      - sentiment_net
    volumes:
      - ./shared:/shared
~~~

### 3.4 Extend Makefile with authorization helpers (optional but consistent)

Add:

~~~makefile
wait-authz:
	@echo "# [make wait-authz] Wait until authz_test finishes"
	@$(COMPOSE) wait authz_test >/dev/null 2>&1 || true

logs-authz:
	@echo "# [make logs-authz] Print authz_test logs (tail=200)"
	@$(COMPOSE) logs --no-color --tail=200 authz_test || true
~~~

### 3.5 Extend `setup.sh` to run Authorization test too

After the auth test, run the authorization test the same way:

~~~bash
make wait-authz
make logs-authz
~~~

### 3.6 Quick dev verification (optional)

You can run the script locally against the running API (no containerization), to iterate faster:

~~~bash
API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
python3 tests/authorization/test_authorization.py
~~~


