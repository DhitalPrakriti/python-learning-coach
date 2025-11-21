
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.models.google_llm import Gemini
from typing import Dict, List
import os
from datetime import datetime

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def track_learning_progress(user_id: str, topics_learned: List[str], exercises_completed: int, 
                          current_level: str, goals: List[str]) -> Dict:
    """Track and analyze user's learning progress"""
    
    # Calculate progress metrics
    total_topics = len(topics_learned)
    progress_percentage = min((exercises_completed / 20) * 100, 100)  # Cap at 100%
    
    # Determine achievement level
    if exercises_completed >= 15:
        achievement = "Expert"
        badge = "🏆 Python Master"
    elif exercises_completed >= 10:
        achievement = "Advanced" 
        badge = "⭐ Python Pro"
    elif exercises_completed >= 5:
        achievement = "Intermediate"
        badge = "🎯 Python Learner"
    else:
        achievement = "Beginner"
        badge = "🌱 Python Starter"
    
    # Identify strengths and areas for improvement
    common_topics = ["variables", "functions", "loops", "lists", "dictionaries"]
    strengths = [topic for topic in topics_learned if topic in common_topics]
    next_topics = [topic for topic in common_topics if topic not in topics_learned]
    
    # Generate personalized recommendations
    recommendations = []
    if len(strengths) >= 3:
        recommendations.append("Great foundation! Consider working on projects.")
    if next_topics:
        recommendations.append(f"Next topics to learn: {', '.join(next_topics[:2])}")
    if exercises_completed < 10:
        recommendations.append("Try more practice exercises to reinforce learning.")
    
    return {
        "user_id": user_id,
        "tracking_date": datetime.now().strftime("%Y-%m-%d"),
        "topics_learned": topics_learned,
        "exercises_completed": exercises_completed,
        "current_level": current_level,
        "progress_percentage": round(progress_percentage, 1),
        "achievement_level": achievement,
        "badge_earned": badge,
        "strengths": strengths,
        "next_recommended_topics": next_topics,
        "personalized_recommendations": recommendations,
        "weekly_goal": f"Complete {max(2, 5 - exercises_completed // 3)} more exercises this week",
        "motivational_message": "Keep going! Every exercise brings you closer to Python mastery!",
        "learning_velocity": "Steady progress" if exercises_completed > 3 else "Getting started"
    }

# Create the progress tool
progress_tool = FunctionTool(track_learning_progress)

# Create the progress agent
progress_agent = Agent(
    name="ProgressAgent",
    model=Gemini(model_name="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
    instruction="""You are a learning progress tracker and motivational coach. Help students see their growth and stay motivated.

When analyzing progress:
1. Use track_learning_progress tool to get detailed analytics
2. Celebrate achievements and milestones
3. Provide constructive feedback
4. Suggest next steps for improvement
5. Keep students motivated and engaged

Be encouraging and help students see how far they've come in their Python journey.""",
    tools=[progress_tool]
)
