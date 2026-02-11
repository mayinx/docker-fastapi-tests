# Use a minimal python base image 
FROM python:3.12-slim

WORKDIR /app

# Install requests - i.e3. only what we need for HTTP calls 
# and don't keep pip's download/cache dir on disk 
RUN pip install --no-cache-dir requests

# Copy test script into teh image 
# COPY test_authorization.py /app/test_authorization.py

# copy the whole package tree (so `tests.*` imports work)
COPY tests /app/tests

# Default command: run the test script on container start
# (so `docker compose up` triggers the test automatically)
# FYI: Environment vars needed for the script execution are 
# set by docker-compose
# CMD ["python", "/app/test_authorization.py"]
CMD ["python3", "-m", "tests.authorization.test_authorization"]