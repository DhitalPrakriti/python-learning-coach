from google import genai
from google.genai import types
from typing import Dict, Any

# ==========================================
# 1. YOUR CURRICULUM LOGIC (The "Brain")
# ==========================================
def generate_python_curriculum(
    experience_level: str, 
    learning_goals: str = "general Python proficiency", 
    focus_areas: str = None
) -> Dict[str, Any]:
    """Generate personalized Python learning curriculum based on assessment"""
    
    # Parse focus_areas if provided
    focus_list = focus_areas.split(",") if focus_areas else ["core programming concepts"]
    
    # --- YOUR ORIGINAL CURRICULUM DATA ---
    python_curricula = {
        "beginner": {
            "title": "Python Fundamentals Path (6 Weeks)",
            "description": "Perfect for absolute beginners starting their programming journey",
            "weekly_plan": [
                {"week": 1, "topic": "Python Basics & Setup", "lessons": ["Installing Python", "Variables"], "practice": "Create a simple calculator"},
                {"week": 2, "topic": "Control Structures", "lessons": ["If/Else", "Boolean logic"], "practice": "Build a number guessing game"},
                {"week": 3, "topic": "Loops & Iterations", "lessons": ["For/While loops"], "practice": "Multiplication tables"},
                {"week": 4, "topic": "Functions", "lessons": ["Parameters, Scope"], "practice": "Temperature converter"},
                {"week": 5, "topic": "Data Structures", "lessons": ["Lists, Dictionaries"], "practice": "Grade tracker"},
                {"week": 6, "topic": "Final Project", "lessons": ["Debugging, Next Steps"], "practice": "Todo list app"}
            ],
            "resources": ["Python Docs", "Codecademy", "freeCodeCamp"],
            "pace": "Slow and steady",
            "milestones": ["Week 1: First program", "Week 3: First game", "Week 6: First app"]
        },
        "intermediate": {
            "title": "Python Developer Path (8 Weeks)", 
            "description": "For those with basic knowledge ready to build real apps",
            "weekly_plan": [
                {"week": 1, "topic": "OOP", "lessons": ["Classes, Inheritance"], "practice": "Banking system"},
                {"week": 2, "topic": "Advanced Data Structures", "lessons": ["Comprehensions"], "practice": "Data processing"},
                {"week": 3, "topic": "Error Handling", "lessons": ["Try/Except"], "practice": "Robust file processor"},
                {"week": 4, "topic": "File Handling", "lessons": ["JSON, CSV, SQL"], "practice": "Contact manager"},
                {"week": 5, "topic": "APIs", "lessons": ["REST, Requests"], "practice": "Weather app"},
                {"week": 6, "topic": "Libraries", "lessons": ["Pandas, Matplotlib"], "practice": "Data analysis"},
                {"week": 7, "topic": "Testing", "lessons": ["Pytest, Git"], "practice": "Write tests"},
                {"week": 8, "topic": "Capstone", "lessons": ["Deployment"], "practice": "Web application"}
            ],
            "resources": ["Real Python", "Effective Python"],
            "pace": "Moderate",
            "milestones": ["Week 4: Database app", "Week 6: API integration", "Week 8: Portfolio"]
        },
        "advanced": {
            "title": "Python Mastery Path (6 Weeks)",
            "description": "Mastering advanced concepts",
            "weekly_plan": [
                {"week": 1, "topic": "Advanced OOP", "lessons": ["Design Patterns"], "practice": "Implement patterns"},
                {"week": 2, "topic": "Concurrency", "lessons": ["Async/Await"], "practice": "Concurrent scraper"},
                {"week": 3, "topic": "Performance", "lessons": ["Profiling, Caching"], "practice": "Optimize app"},
                {"week": 4, "topic": "Frameworks", "lessons": ["Django/FastAPI/PyTorch"], "practice": "Build with framework"},
                {"week": 5, "topic": "System Design", "lessons": ["Microservices"], "practice": "Design system"},
                {"week": 6, "topic": "Open Source", "lessons": ["Contributing"], "practice": "Contribute to project"}
            ],
            "resources": ["Fluent Python", "Architecture Patterns"],
            "pace": "Fast-paced",
            "milestones": ["Week 3: Tuning", "Week 5: Architecture", "Week 6: Contribution"]
        }
    }
    
    curriculum = python_curricula.get(experience_level.lower(), python_curricula["beginner"])
    
    return {
        "curriculum_title": curriculum["title"],
        "description": curriculum["description"],
        "experience_level": experience_level,
        "learning_goals": learning_goals,
        "focus_areas": focus_list,
        "weekly_plan": curriculum["weekly_plan"],
        "recommended_resources": curriculum["resources"],
        "recommended_pace": curriculum["pace"],
        "key_milestones": curriculum["milestones"]
    }

# ==========================================
# 2. THE NEW AGENT CLASS (The "Body")
# ==========================================
class GenAICurriculumAgent:
    def __init__(self, client: genai.Client):
        self.client = client
        self.model_id = "gemini-2.5-flash"
        
        # KEY CHANGE: Pass the function directly!
        self.tools = [generate_python_curriculum]

    def query(self, message: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=message,
                config=types.GenerateContentConfig(
                    tools=self.tools,  # <--- Tool enabled
                    system_instruction="""
                    You are an expert Python curriculum designer. 
                    When a user asks for a learning path, use 'generate_python_curriculum'.
                    1. Generate the plan based on their level.
                    2. Present the weekly schedule clearly.
                    3. Encourage them to start Week 1.
                    """
                )
            )
            return response.text
        except Exception as e:
            return f"Agent Error: {str(e)}"

# ==========================================
# 3. THE FACTORY
# ==========================================
# IMPORTANT: This function now accepts the 'client' argument!
def create_curriculum_agent(client: genai.Client):
    return GenAICurriculumAgent(client)