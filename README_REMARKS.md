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