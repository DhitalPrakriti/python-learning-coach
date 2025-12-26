from google import genai
from google.genai import types
from typing import Dict, Any

# ==========================================
# 1. YOUR ASSESSMENT LOGIC (The "Brain")
# ==========================================
# (I kept your exact functions!)

def assess_learning_profile(
    experience: str, 
    learning_style: str = "adaptive", 
    subject: str = "python"
) -> Dict[str, Any]:
    """Create personalized learning profile based on experience level"""
    
    experience_levels = {
        "beginner": {
            "score": 1, "pace": "slow", "depth": "fundamentals",
            "topics": ["variables", "data types", "basic operators", "if/else"]
        },
        "intermediate": {
            "score": 2, "pace": "moderate", "depth": "concepts",
            "topics": ["functions", "OOP", "file I/O", "error handling"]
        },
        "advanced": {
            "score": 3, "pace": "fast", "depth": "advanced_topics",
            "topics": ["decorators", "generators", "async/await", "metaclasses"]
        }
    }
    
    base_profile = experience_levels.get(experience.lower(), experience_levels["beginner"])
    
    return {
        "experience_level": experience,
        "learning_style": learning_style,
        "subject": subject,
        "recommended_pace": base_profile["pace"],
        "learning_depth": base_profile["depth"],
        "assessment_score": base_profile["score"],
        "recommended_topics": base_profile["topics"],
        "next_steps": f"Start with {subject} {experience} level: {', '.join(base_profile['topics'][:2])}"
    }

def analyze_student_input(student_input: str) -> Dict[str, Any]:
    """Analyze student's description to determine experience and learning style"""
    input_lower = student_input.lower()
    
    # Experience
    if any(w in input_lower for w in ["expert", "advanced", "senior", "years of"]):
        experience = "advanced"
    elif any(w in input_lower for w in ["intermediate", "some experience", "basic knowledge"]):
        experience = "intermediate"
    else:
        experience = "beginner"
    
    # Style
    if any(w in input_lower for w in ["visual", "see", "watch", "diagram"]):
        learning_style = "visual"
    elif any(w in input_lower for w in ["audio", "listen", "hear", "explain"]):
        learning_style = "auditory"
    elif any(w in input_lower for w in ["hands-on", "practice", "code", "build"]):
        learning_style = "kinesthetic"
    else:
        learning_style = "adaptive"
    
    return {
        "detected_experience": experience,
        "detected_learning_style": learning_style,
        "analysis_complete": True
    }

def assess_with_code_sample(code_sample: str) -> Dict[str, Any]:
    """Assess skill level based on code sample"""
    code_lower = code_sample.lower()
    
    advanced_indicators = ["def __", "async def", "yield", "@", "metaclass", "lambda"]
    intermediate_indicators = ["def ", "class ", "import ", "return", "self.", "for ", "while "]
    beginner_indicators = ["print(", "input(", "if ", "else:", "="]
    
    adv_count = sum(1 for ind in advanced_indicators if ind in code_lower)
    int_count = sum(1 for ind in intermediate_indicators if ind in code_lower)
    beg_count = sum(1 for ind in beginner_indicators if ind in code_lower)
    
    if adv_count >= 2: level = "advanced"
    elif int_count >= 3: level = "intermediate"
    else: level = "beginner"
    
    return {
        "assessed_level": level,
        "code_complexity": {"advanced": adv_count, "intermediate": int_count},
        "has_code_sample": True
    }

# ==========================================
# 2. THE NEW AGENT CLASS (The "Body")
# ==========================================
class GenAIAssessmentAgent:
    def __init__(self, client: genai.Client):
        self.client = client
        self.model_id = "gemini-2.5-flash"
        
        # KEY CHANGE: Pass the raw functions directly!
        self.tools = [assess_learning_profile, analyze_student_input, assess_with_code_sample]

    def query(self, message: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=message,
                config=types.GenerateContentConfig(
                    tools=self.tools,  # <--- Tools enabled
                    system_instruction="""
                    You are an expert Python learning assessment specialist.
                    1. If the user describes themselves, use 'analyze_student_input'.
                    2. If the user provides code, use 'assess_with_code_sample'.
                    3. ALWAYS finish by using 'assess_learning_profile' to generate a plan.
                    
                    Be encouraging, honest, and specific.
                    """
                )
            )
            return response.text
        except Exception as e:
            return f"Agent Error: {str(e)}"

# ==========================================
# 3. THE FACTORY
# ==========================================
def create_assessment_agent(client: genai.Client):
    return GenAIAssessmentAgent(client)