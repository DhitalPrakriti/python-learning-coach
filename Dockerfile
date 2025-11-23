# Dockerfile
# Use a Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set environment variables (for the agent's internal use)
ENV GOOGLE_CLOUD_PROJECT="python-learning-coach-ai"
ENV GOOGLE_CLOUD_LOCATION="us-central1"
ENV GOOGLE_GENAI_USE_VERTEXAI="1"
# We removed ENV PORT="8080" as it's set by Cloud Run dynamically

# Expose the port (informative only, doesn't affect runtime)
EXPOSE 8080

# Command to run the application using Uvicorn
# CRITICAL FIX: We now use the $PORT environment variable, which Cloud Run sets.
CMD python -m uvicorn main:app --host 0.0.0.0 --port $PORT