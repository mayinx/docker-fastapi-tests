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