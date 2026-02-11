# Remarks / Justification of Choices

## File naming / structure
- I used `README_IMPLEMENTATION.md` as a reproducible build diary (commands + milestones).
- I used `README_REMARKS.md` as a short “why” document (subset of the implementation log), as suggested by the exam statement (“possibly remarks or justification”).

## Why Docker Compose from the start
- The exam requires a `docker-compose.yml` orchestrating 4 containers (API + 3 test containers).  
  Starting with Compose early avoids rework and keeps the final pipeline structure consistent.

## Why the API service is named `api`
- Compose provides internal DNS by service name.  
  Using `api` enables test containers to call the API with `http://api:8000/...` without hardcoding host IPs.

## Why a shared `./shared` folder exists already
- The exam requires a final `api_test.log` produced by the test runs.  
  A shared bind-mount makes it easy for **multiple test containers** to append to the same log file deterministically.


  --------


## Remarks / Justification (Auth test + pipeline runner)

- **One container per test:** The exam requests separate containers for each test suite (Authentication / Authorization / Content). This keeps the pipeline modular: changing one test does not require touching others.
- **Readiness polling:** The auth test script polls `GET /status` until the API is ready. This is important because `depends_on` in Docker Compose controls **start order**, not **service readiness**.
- **Compose-internal addressing:** Tests call the API via the Compose DNS name `api:8000`, avoiding host networking assumptions and keeping the setup portable.
- **Shared aggregated log:** When `LOG=1`, the test appends its report to a shared `LOG_PATH` (default `/shared/api_test.log`). A shared volume allows multiple test containers to write into a single file, as required for the final `log.txt`.
- **CI/CD-style exit codes:** The test script exits with `0` on success and `1` on failure so the pipeline can fail fast and Compose runs are machine-checkable.
- **setup.sh as reproducible runner:** `setup.sh` orchestrates a clean reset → run → capture logs → teardown flow to reduce “stray container / port already allocated” issues during repeated exam runs.


---

## Remarks / Justification (Authorization test)

- The exam requests a separate container for each test suite; `authz_test` isolates authorization checks from authentication/content checks.
- Authorization is validated by comparing expected HTTP status codes for version access:
  - alice: v1=200, v2=200
  - bob:   v1=200, v2=403
- The test calls the API via compose-internal DNS (`api:8000`) for portability.
- A readiness polling step (`GET /status`) is included because `depends_on` controls start order, not readiness.
- Logging is appended to the shared `/shared/api_test.log` (when `LOG=1`) so multiple test containers produce one aggregated report, later copied to `log.txt` for submission.