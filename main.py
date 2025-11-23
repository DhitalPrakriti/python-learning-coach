# main.py
import os
from fastapi import FastAPI
from google.adk.agent_engines.runtime import AgentEngine, AgentEngineConfig
from agent import agent as python_learning_coach_agent

# Initialize environment variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Create the FastAPI app
app = FastAPI(title="Python Learning Coach API")

# Configure and integrate the Agent Engine
# This handles the conversation flow for your multi-agent system
agent_config = AgentEngineConfig(
    project_id=PROJECT_ID,
    location=LOCATION
)

# Pass your orchestrator agent object to the AgentEngine
agent_engine = AgentEngine(
    agent=python_learning_coach_agent,
    config=agent_config
)

# Mount the AgentEngine router to your FastAPI app at the root path "/"
app.include_router(agent_engine.router)

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "agent_name": python_learning_coach_agent.name}
