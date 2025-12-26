# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set build-time arguments
ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=1000

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use gunicorn for production instead of python main.py
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0  --worker-tmp-dir /dev/shm main:app