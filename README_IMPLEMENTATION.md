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
- The test containers don't need port publishing (see. ports: ...) for the api-container at all - they can reach the API over the internal Docker network via the service name (http://api:8000). But having ports is convenient for manual checks like curl http://localhost:8000/status or opening /docs in the browser


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

## 2) Authentication test container (GET /permissions)

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

Create `tests/authentication/test_authentication.py`:

~~~python
import os
import time
import requests

# Compose DNS: service name "api" resolves to the API container on the compose network
API_ADDRESS = os.environ.get("API_ADDRESS", "api")
API_PORT = int(os.environ.get("API_PORT", "8000"))

# Shared log file location (bind-mounted volume in docker-compose)
LOG_PATH = os.environ.get("LOG_PATH", "/shared/api_test.log")

def wait_for_api(timeout_s: int = 30) -> bool:
    """
    Wait until the API answers /status with '1'.
    Why: docker-compose 'depends_on' does not guarantee the service is READY,
    only that the container started. This makes the test container robust.
    """
    url = f"http://{API_ADDRESS}:{API_PORT}/status"
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200 and r.text.strip() == "1":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def write_log(block: str) -> None:
    """
    LOG behavior (exam requirement):
    - If LOG=1, append the report to a shared file.
    """
    if os.environ.get("LOG") == "1":
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(block + "\n")

def check_case(username: str, password: str, expected_code: int) -> bool:
    url = f"http://{API_ADDRESS}:{API_PORT}/permissions"
    r = requests.get(url, params={"username": username, "password": password}, timeout=5)
    ok = (r.status_code == expected_code)

    output = f"""
============================
    Authentication test
============================
request done at "/permissions"
| username="{username}"
| password="{password}"
expected result = {expected_code}
actual result   = {r.status_code}
==> {("SUCCESS" if ok else "FAILURE")}
"""
    print(output)
    write_log(output)
    return ok

def main() -> int:
    ready = wait_for_api(timeout_s=40)
    if not ready:
        output = """
============================
    Authentication test
============================
API readiness check FAILED
expected /status => "1"
==> FAILURE
"""
        print(output)
        write_log(output)
        return 1

    cases = [
        ("alice", "wonderland", 200),
        ("bob", "builder", 200),
        ("clementine", "mandarine", 403),
    ]

    all_ok = True
    for u, p, exp in cases:
        all_ok = check_case(u, p, exp) and all_ok

    return 0 if all_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
~~~

What this script does (and why):
- Calls the API over the **compose internal DNS name** `api:8000` (no host IP needed).
- Waits for readiness using `/status` because:
  - `depends_on` ensures order, not readiness.
- Runs the 3 exam-defined credential checks and validates HTTP status codes.
- If `LOG=1`, appends readable reports to `/shared/api_test.log` so multiple test containers can share one log file later.
- Exits with `0` on success, `1` on failure (important so CI/CD-style pipelines can fail fast).

---

### 2.2 Create a Dockerfile for the authentication test image

Create `tests/authentication/Dockerfile`:

~~~Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install only what we need for HTTP calls
RUN pip install --no-cache-dir requests

COPY test_authentication.py /app/test_authentication.py

# Default command: run the test script
CMD ["python", "/app/test_authentication.py"]
~~~

What this Dockerfile does (and why):
- Uses a small Python base image.
- Installs `requests` (enough for HTTP calls; keeps scope minimal).
- Copies the test script into the image.
- Runs the test on container start (so `docker compose up` triggers the test automatically).

---

### 2.3 Wire the authentication test container into docker-compose

Update your `docker-compose.yml`:
- keep the existing `api` service
- add `auth_test`
- keep your chosen network name `sentiment_net`
- keep `./shared:/shared` on both API and test containers so log file is shared

~~~yaml
services:
  api:
    image: datascientest/fastapi:1.0.0
    container_name: api
    ports:
      - "8000:8000"   # host:container (so you can curl localhost:8000 for manual checks)
    networks:
      - sentiment_net
    volumes:
      - ./shared:/shared

  auth_test:
    build:
      context: ./tests/authentication
      dockerfile: Dockerfile
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
    volumes:
      - ./shared:/shared

networks:
  sentiment_net:
    driver: bridge
~~~

Why keep `ports: "8000:8000"` on the API:
- Not required for inter-container communication.
- But it makes **manual debugging** fast (`curl http://localhost:8000/status` and `/docs`).

Why both services mount `./shared:/shared`:
- So all tests can append into one shared file `/shared/api_test.log` (later: all 3 test containers write into the same report).

---

### 2.4 Add a setup.sh starter (build + run + capture logs)

Create or update `setup.sh` (make executable with `chmod +x setup.sh`):

~~~bash
#!/usr/bin/env bash
set -euo pipefail

# What this script does:
# - builds test images (because compose has a build: section for tests)
# - starts the stack
# - shows container status
# - prints test logs to the terminal
# - copies the aggregated shared log to log.txt (exam requirement: log.txt result)
# - shuts down containers

# Flags explained:
# docker compose up -d --build
# - up: create/start services
# - -d: detached/background mode (returns to shell immediately)
# - --build: rebuild images that have a build: section (our test containers)

docker compose up -d --build

# Show status (ps = "process status" for compose services)
docker compose ps

# Stream auth_test logs then exit (logs = container stdout/stderr)
docker compose logs auth_test

# Copy aggregated report if present
if [ -f "./shared/api_test.log" ]; then
  cp ./shared/api_test.log ./log.txt
fi

# Shutdown (down = stop + remove containers/networks created by this compose project)
docker compose down
~~~

Make it executable:

~~~bash
chmod +x setup.sh
~~~

---

### 2.5 Run Milestone 2

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

### 2.6 Git commit

~~~bash
git add .
git commit -m "test(auth): add authentication test container and shared logging"
~~~

---

# (Paste into README_REMARKS.md)

## Milestone 2 — Remarks / Justification

- I implemented **one container per test** as required, starting with `auth_test`. This keeps the pipeline modular: if one test changes, only that image needs rebuilding.
- The authentication test waits for API readiness via `/status` because `docker compose depends_on` guarantees start order but not that the API is ready to serve requests.
- I used Compose DNS (`api:8000`) instead of host IPs to keep the solution portable and network-correct.
- Logging is written to a shared bind mount (`./shared:/shared`) so all test containers can append into a single `api_test.log`, matching the exam’s requirement for a final consolidated report.
