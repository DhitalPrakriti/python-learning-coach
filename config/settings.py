import os
import vertexai

# Vertex AI Configuration
PROJECT_ID = "python-learning-coach-ai"
LOCATION = "us-central1"

# Model Configuration - Use proven model
MODEL_NAME = "gemini-1.5-flash-001"

# Learning Configuration
DEFAULT_SUBJECT = "python"
SUPPORTED_LEVELS = ["beginner", "intermediate", "advanced"]
LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "adaptive"]

print("✅ Vertex AI Learning Coach configuration loaded")
