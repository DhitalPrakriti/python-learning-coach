# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set build-time arguments
ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=1000

# curl is needed by the HEALTHCHECK below. No compiler is installed: every
# dependency ships a manylinux wheel, and build-essential added ~400MB.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=$USERNAME:$USERNAME . .

# Switch to non-root user
USER $USERNAME

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose port (for documentation)
EXPOSE 8080

# Health check. Kept on one line so linters don't read the HEALTHCHECK's own
# CMD as a second container CMD. Uses $PORT so it follows an overridden port.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

# Use gunicorn for production instead of python main.py.
# --timeout 120 rather than 0: an unbounded timeout means a hung Gemini call
# pins a worker forever instead of failing and freeing the slot.
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 \
    --graceful-timeout 30 --worker-tmp-dir /dev/shm --access-logfile - main:app
