import os
from kaggle_secrets import UserSecretsClient

# API Configuration
GOOGLE_API_KEY = UserSecretsClient().get_secret("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
MODEL_NAME = "gemini-2.0-flash-exp"

# Learning Configuration
DEFAULT_SUBJECT = "python"
SUPPORTED_LEVELS = ["beginner", "intermediate", "advanced"]
LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "adaptive"]

print("✅ Learning Coach configuration loaded")
