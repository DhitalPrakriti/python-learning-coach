from google import genai
from google.genai import types
from typing import Dict, Any
from datetime import datetime

# ==========================================
# 1. YOUR PROGRESS LOGIC (The "Brain")
# ==========================================
def track_learning_progress(
    user_id: str,
    topics_learned: str,  # Comma-separated string
    exercises_completed: int,
    current_level: str,
    goals: str = "Learn Python fundamentals"
) -> Dict[str, Any]:
    """Track and analyze user's learning progress"""
    
    topics_list = [t.strip() for t in topics_learned.split(",")] if topics_learned else []
    goals_list = [g.strip() for g in goals.split(",")] if goals else []
    
    total_topics = len(topics_list)
    progress_percentage = min((exercises_completed / 20) * 100, 100)
    
    # Achievement Logic
    if exercises_completed >= 15:
        achievement = "Expert"; badge = "🏆 Python Master"
    elif exercises_completed >= 10:
        achievement = "Advanced"; badge = "⭐ Python Pro"
    elif exercises_completed >= 5:
        achievement = "Intermediate"; badge = "🎯 Python Learner"
    else:
        achievement = "Beginner"; badge = "🌱 Python Starter"
    
    # Strengths
    common_topics = ["variables", "functions", "loops", "lists", "dictionaries", "conditionals", "classes"]
    strengths = [topic for topic in topics_list if topic.lower() in common_topics]
    next_topics = [topic for topic in common_topics if topic not in [t.lower() for t in topics_list]]
    
    # Recommendations
    recommendations = []
    if len(strengths) >= 3: recommendations.append("Great foundation! Ready for small projects.")
    if len(strengths) >= 5: recommendations.append("Strong skills! Consider building a portfolio.")
    if next_topics: recommendations.append(f"Next topics: {', '.join(next_topics[:2])}")
    if exercises_completed < 5: recommendations.append("Complete more practice exercises.")
    else: recommendations.append("Excellent practice habits!")
    
    # Velocity
    if exercises_completed >= 10: velocity = "Fast learner!"
    elif exercises_completed >= 5: velocity = "Steady progress."
    else: velocity = "Getting started."
    
    return {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "metrics": {
            "topics": total_topics,
            "exercises": exercises_completed,
            "level": current_level,
            "progress": round(progress_percentage, 1)
        },
        "gamification": {
            "achievement": achievement,
            "badge": badge,
            "velocity": velocity
        },
        "insights": {
            "strengths": strengths,
            "recommendations": recommendations,
            "next_topics": next_topics[:3]
        }
    }

def generate_progress_report(
    user_id: str,
    topics_learned: str,
    exercises_completed: int,
    days_active: int = 7
) -> Dict[str, Any]:
    """Generate comprehensive progress report with insights"""
    
    topics_list = [t.strip() for t in topics_learned.split(",")] if topics_learned else []
    avg_exercises = round(exercises_completed / max(days_active, 1), 1)
    
    if avg_exercises >= 2: pace = "Excellent pace!"
    elif avg_exercises >= 1: pace = "Good consistency."
    else: pace = "Try to practice more often."
    
    return {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "summary": {
            "topics_count": len(topics_list),
            "exercises_total": exercises_completed,
            "days_active": days_active,
            "avg_daily": avg_exercises
        },
        "analysis": {
            "pace": pace,
            "milestone_status": "Advanced" if exercises_completed >= 15 else "Developing",
            "topics_covered": topics_list[:5]
        }
    }

def suggest_next_steps(current_level: str, topics_mastered: str) -> Dict[str, Any]:
    """Suggest personalized next steps based on progress"""
    
    topics_list = [t.strip().lower() for t in topics_mastered.split(",")] if topics_mastered else []
    
    pathways = {
        "beginner": {
            "focus": "Master Fundamentals",
            "steps": ["Practice variables", "Learn loops", "Build calculator"],
            "resources": ["Python.org", "Codecademy"]
        },
        "intermediate": {
            "focus": "Build Projects",
            "steps": ["Master OOP", "File Handling", "Build Todo App"],
            "resources": ["Real Python", "Automate the Boring Stuff"]
        },
        "advanced": {
            "focus": "Specialization",
            "steps": ["Web/Data Specialization", "Open Source", "Design Patterns"],
            "resources": ["Fluent Python"]
        }
    }
    
    pathway = pathways.get(current_level.lower(), pathways["beginner"])
    
    return {
        "level": current_level,
        "pathway": pathway,
        "skill_gaps": [t for t in ["functions", "loops"] if t not in topics_list],
        "motivation": f"You are doing great at the {current_level} level!"
    }

# ==========================================
# 2. THE NEW AGENT CLASS (The "Body")
# ==========================================
class GenAIProgressAgent:
    def __init__(self, client: genai.Client):
        self.client = client
        self.model_id = "gemini-2.5-flash"
        
        # KEY CHANGE: Pass functions directly!
        self.tools = [track_learning_progress, generate_progress_report, suggest_next_steps]

    def query(self, message: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=message,
                config=types.GenerateContentConfig(
                    tools=self.tools,
                    system_instruction="""
                    You are a motivational learning coach.
                    1. Use 'track_learning_progress' to analyze user stats and badges.
                    2. Use 'generate_progress_report' for summaries.
                    3. Use 'suggest_next_steps' to guide them forward.
                    
                    Always be encouraging, celebrate small wins (Badges), and provide data-driven advice.
                    """
                )
            )
            return response.text
        except Exception as e:
            return f"Agent Error: {str(e)}"

# ==========================================
# 3. THE FACTORY
# ==========================================
def create_progress_agent(client: genai.Client):
    return GenAIProgressAgent(client)