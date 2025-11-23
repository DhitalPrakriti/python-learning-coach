from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import all your agent functions
from agents.assessment_agent import (
    assess_learning_profile,
    analyze_student_input,
    assess_with_code_sample
)
from agents.curriculum_agent import generate_python_curriculum
from agents.teaching_agent import teach_python_concept
from agents.practice_agent import generate_python_exercise
from agents.progress_agent import (
    track_learning_progress,
    generate_progress_report,
    suggest_next_steps
)

# Create all tools
tools = [
    FunctionTool(assess_learning_profile),
    FunctionTool(analyze_student_input),
    FunctionTool(assess_with_code_sample),
    FunctionTool(generate_python_curriculum),
    FunctionTool(teach_python_concept),
    FunctionTool(generate_python_exercise),
    FunctionTool(track_learning_progress),
    FunctionTool(generate_progress_report),
    FunctionTool(suggest_next_steps)
]

# Create the agent EXACTLY as shown in documentation
agent = Agent(
    model="gemini-1.5-flash-001",
    name="python_learning_coach",
    instruction="""
    You are a comprehensive Python Learning Coach with 5 specialized agents:
    
    🔍 ASSESSMENT - Evaluate student level and learning style
    📚 CURRICULUM - Design personalized learning paths  
    👨‍🏫 TEACHING - Explain concepts with examples
    💻 PRACTICE - Generate coding exercises
    📊 PROGRESS - Track learning metrics
    
    Use the appropriate tools based on student needs.
    Be encouraging and adapt to each student's level.
    """,
    tools=tools
)

print("✅ Multi-agent Python Learning Coach ready!")
