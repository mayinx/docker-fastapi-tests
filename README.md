# 🐋 Docker Exam Project: FastAPI Sentiment Test Pipeline
### Tested sentiment analysis API • Python-based tests • Reproducible • CI/CD-style • One container per test suite • Shared aggregated log

## 🎯 What this project demonstrates
This repository implements a **Docker Compose test pipeline** for the sentiment analysis API image `datascientest/fastapi:1.0.0`.

✅ **API container** exposed on host port 8000 (endpoints: `/status`, `/permissions`, `/v1/sentiment`, `/v2/sentiment`)  
✅ **3 separate Python test containers** (one per suite) that validate:
- **Authentication** (`/permissions`)
- **Authorization** (`/v1/sentiment` vs `/v2/sentiment`)
- **Content** (positive/negative score checks for given sentences)

✅ **Automatic sequential execution** via Compose `depends_on` conditions: API → Authentication → Authorization → Content  
✅ **LOG=1** support: all suites append into a single shared **`api_test.log`** (kept in `./shared/`).  
✅ **`setup.sh`** runs the whole pipeline reproducibly and produces **`log.txt`** (submission artifact)  

---

## 🎭 Tech Stack
🐋 **Docker / Docker Compose** | 🐍 **Python 3.12** | 🌐 **requests** | ⚙️ **Makefile orchestration**

---

## 🧠 Engineering Notes (Beyond Requirements): Shared, reusable test framework

While the exam only requires “3 test containers + test scripts + a shared log”, I deliberately invested extra effort to keep the solution **abstract, reusable, and maintainable**—so each suite only defines its **test cases** in a (mroe or less) DSL-like manner, while the execution (incl. assertions) + logging pipeline stays consistent across all suites.

### What’s abstracted (and why it matters)
- **Central config loading** (`tests/_shared/config.py`)  
  All suites use the same env contract (`API_ADDRESS`, `API_PORT`, `LOG`, `LOG_PATH`, `HTTP_TIMEOUT`) so behavior is consistent across containers and host runs.

- **One generic request runner** (`tests/_shared/runner.py`)  
  A single function executes HTTP requests, validates status codes, and (only when required) validates sentiment score direction.  
  → Suites don’t duplicate request/validation logic.

- **Unified, deterministic logging** (`tests/_shared/logging.py`)  
  Consistent suite headers/footers + per-test formatting for stdout and (when `LOG=1`) a shared append-only log file.  
  → The aggregated `api_test.log` stays readable and stable across runs.

- **Generic params handling** (`tests/_shared/params.py`)  
  `iter_params(...)` normalizes suite-specific param objects (dicts, dataclasses, NamedTuples, etc.) into `(key, value)` pairs for logging and request execution.  
  → Each suite can model its test parameters however it wants without changing the logger/runner.

- **Shared types for clarity** (`tests/_shared/types.py`)  
  Common `TestCase` + `TestResult` structures keep the contract between suite definitions and the shared engine explicit.

### Result
Each suite module focuses on *only*:
- defining test cases (endpoint + params + expected outcomes)
- invoking the shared runner/logger
- returning an exit code suitable for CI/CD

Everything else (config, readiness waiting, request execution, output format, file logging) is handled once in `tests/_shared/`.

---

## 🏗️ Architecture (Pipeline + Shared Log)

~~~text
                                (host)
                       ./shared/  +  ./log.txt
                          ▲               ▲
                          │               │  snapshot copy
         bind mount       │               └─ setup.sh / make snapshot-log
      ./shared:/shared    │
                          │
+-------------------------------------------------------------------------------+
|                          docker compose project                               |
|                                                                               |
|   +--------------------------+            +------------------------------+    |
|   |        API service        |<---------->|   internal network           |   |
|   |  datascientest/fastapi    |  HTTP      |   sentiment_net (DNS: api)   |   |
|   |  host 8000 -> :8000       |            +------------------------------+   |
|   +-------------+------------+                                                |
|                 ^                                                             |
|                 |  (all test suites call http://api:8000/...)                 |
|                 |                                                             |
|   +-------------+--------------------------------------------------------+    |
|   |                                                                      |    |
|   |   +-------------------+     +-------------------+     +----------------+  |
|   |   | auth_test (suite) | --> | authz_test (suite)| --> | content_test    | |
|   |   | /permissions      |     | /v1 + /v2 access  |     | /v1 + /v2 score | |
|   |   +---------+---------+     +---------+---------+     +--------+--------+ |
|   |             |                       |                        |            |
|   |             | append                | append                 | append     |
|   |             v                       v                        v            |
|   |       +--------------------------------------------------------------+    |
|   |       |          shared bind mount: ./shared : /shared               |    |
|   |       |          aggregated log:    /shared/api_test.log             |    |
|   |       +--------------------------------------------------------------+    |
|   |                                                                      |    |
|   +----------------------------------------------------------------------+    |
|                                                                               |
+-------------------------------------------------------------------------------+

Sequential order is enforced by docker-compose `depends_on` conditions:
- `auth_test` waits for `api` to start (service_started) + polls /status until ready
- `authz_test` starts only after `auth_test` finished successfully (service_completed_successfully)
- `content_test` starts only after `authz_test` finished successfully (service_completed_successfully)

All suites append into the same shared file: /shared/api_test.log
At the end, setup.sh snapshots it to ./log.txt (exam artifact).
~~~

---

## 📁 Project Structure (high level)

~~~text
.
├── docker-compose.yml
├── Makefile
├── setup.sh
├── README.md
├── log.txt                  # exam artifact (snapshotted from ./shared/api_test.log)
├── docs/
    ├── IMPLEMENTATION.md
├── shared/
│   └── api_test.log         # aggregated suite logs (written by test containers when LOG=1)
└── tests/
    ├── _shared/             # common helpers (config, logging, readiness, runner, types)
    ├── authentication/
    │   ├── Dockerfile
    │   └── test_authentication.py
    ├── authorization/
    │   ├── Dockerfile
    │   └── test_authorization.py
    └── content/
        ├── Dockerfile
        └── test_content.py
~~~

---

## 🚀 Quick Start (Exam Runner)

### 1) Run the full pipeline (build → start → test → snapshot log → cleanup)
~~~bash
./setup.sh
~~~

This will:
- reset to a clean state (containers/ports/logs)
- start the API + test containers
- run suites in order: **AUTHENTICATION → AUTHORIZATION → CONTENT**
- write the aggregated log to `./shared/api_test.log` (**exam requirement via LOG=1**)
- copy it to `./log.txt` (**submission artifact**)
- stop everything (rerun-safe)

---

## 🔎 Manual API sanity checks (optional)

~~~bash
curl -s "http://localhost:8000/status"; echo
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/docs"
~~~

---

## ✅ Most useful Make targets

- `make start-project` — start stack (detached) and build images
- `make stop-project` — stop stack (normal down)
- `make stop-all` — stop stack + remove orphans (quiet + idempotent)
- `make reset` — guaranteed clean state (stop-all + kill-api + free-port-8000 + reset-logs)
- `make logs` — follow logs for the whole stack
- `make logs-auth` / `make logs-authz` / `make logs-content` — print suite logs (tail)
- `make snapshot-log` — copy `./shared/api_test.log` → `./log.txt`

---

## 🧾 Implementation log  

Instead of maintaining a separate `README_student.md`, this project keeps a single detailed build diary:

➡️ See **`docs/IMPLEMENTATION.md`** for step-by-step implementation notes, decisions, and commands:
-  [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)

---

## ⚖️ Notes on portability (UID/GID + bind mounts)

The test containers write into a **bind-mounted** folder (`./shared:/shared`).  
To avoid root-owned files on the host, the test services run as the host user:

- `setup.sh` exports `HOST_UID` and `HOST_GID`
- `docker-compose.yml` uses `user: "${HOST_UID}:${HOST_GID}"` for each test service

This keeps `./shared/api_test.log` writable and removable without `sudo`, and makes reruns deterministic.

---

## APPENDIX: Original Exam Brief (excerpt)

**Goal:** Build a small **CI/CD-style Docker Compose pipeline** that automatically tests a provided **sentiment analysis FastAPI** container image.

- API image: `datascientest/fastapi:1.0.0`
- Endpoints: `/status`, `/permissions`, `/v1/sentiment`, `/v2/sentiment`
- **Pipeline requirement:** Docker Compose must launch **4 containers total**:
  - 1× API container
  - **3× separate test containers** (**Authentication**, **Authorization**, **Content**) — one python test suite per container
- **Logging requirement:** When `LOG=1`, each suite must append its report into **`api_test.log`** (single aggregated file)
- **Expected test coverage:**
  - Authentication: `/permissions` returns **200** for `alice:wonderland` and `bob:builder`, and **403** for `clementine:mandarine`
  - Authorization: `bob` can use **v1 only**, `alice` can use **v1 and v2**
  - Content: using `alice`, sentences **"life is beautiful"** (positive score) and **"that sucks"** (negative score) must be validated for both **v1** and **v2**
- Final deliverables include: `docker-compose.yml`, Python test scripts, Dockerfiles, `setup.sh`, and a submission `log.txt` containing the aggregated results.

### ✅ Deliverables checklist (Exam Requirements)
- ✅ `docker-compose.yml` contains the **sequence of tests** (API + 3 suites)
- ✅ Python test files for **Authentication / Authorization / Content**
- ✅ Dockerfiles to build each test image
- ✅ `setup.sh` to build + launch the compose pipeline
- ✅ `log.txt` containing the aggregated logs (snapshotted from `./shared/api_test.log`)
- ✅ Optional remarks file: [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)