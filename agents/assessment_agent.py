
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.models.google_llm import Gemini
from typing import Optional, Dict
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def assess_learning_profile(experience: str, learning_style: Optional[str] = None, subject: str = "general") -> Dict:
    experience_levels = {
        "beginner": {"score": 1, "pace": "slow", "depth": "fundamentals"},
        "intermediate": {"score": 2, "pace": "moderate", "depth": "concepts"},
        "advanced": {"score": 3, "pace": "fast", "depth": "advanced_topics"}
    }
    experience_lower = experience.lower()
    base_profile = experience_levels.get(experience_lower, experience_levels["beginner"])
    subject_paths = {
        "python": f"{experience}_python_path",
        "math": f"{experience}_math_path",
        "general": f"{experience}_learning_path"
    }
    return {
        "experience_level": experience,
        "learning_style": learning_style or "adaptive",
        "subject": subject,
        "recommended_pace": base_profile["pace"],
        "learning_depth": base_profile["depth"],
        "custom_path": subject_paths.get(subject, subject_paths["general"]),
        "next_steps": f"Start with {subject} {experience} fundamentals"
    }

profile_tool = FunctionTool(assess_learning_profile)

assessment_agent = Agent(
    name="GenericAssessmentAgent",
    model=Gemini(
        model_name="gemini-2.0-flash-exp",
        api_key=GOOGLE_API_KEY
    ),
    instruction="""You are a GENERIC learning assessment expert. Ask about user's goals, experience, and learning style. Use the tool to create a personalized learning profile.""",
    tools=[profile_tool]
)
