
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any
from datetime import datetime
import vertexai


def track_learning_progress(
    user_id: str,
    topics_learned: str,  # Comma-separated string
    exercises_completed: int,
    current_level: str,
    goals: str = "Learn Python fundamentals"  # Comma-separated string
) -> Dict[str, Any]:
    """Track and analyze user's learning progress"""
    
    # Parse comma-separated strings to lists
    topics_list = [t.strip() for t in topics_learned.split(",")] if topics_learned else []
    goals_list = [g.strip() for g in goals.split(",")] if goals else []
    
    # Calculate progress metrics
    total_topics = len(topics_list)
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
    common_topics = ["variables", "functions", "loops", "lists", "dictionaries", 
                     "conditionals", "classes", "file_handling", "error_handling"]
    strengths = [topic for topic in topics_list if topic.lower() in common_topics]
    next_topics = [topic for topic in common_topics if topic not in [t.lower() for t in topics_list]]
    
    # Generate personalized recommendations
    recommendations = []
    if len(strengths) >= 3:
        recommendations.append("Great foundation! You're ready to work on small projects.")
    if len(strengths) >= 5:
        recommendations.append("Strong skills! Consider building a portfolio project.")
    if next_topics:
        recommendations.append(f"Next topics to learn: {', '.join(next_topics[:2])}")
    if exercises_completed < 5:
        recommendations.append("Complete more practice exercises to build muscle memory.")
    elif exercises_completed < 10:
        recommendations.append("Good practice! Try tackling medium difficulty exercises.")
    else:
        recommendations.append("Excellent practice habits! Ready for advanced challenges.")
    
    # Calculate learning velocity
    if exercises_completed >= 10:
        velocity = "Fast learner - excellent progress!"
    elif exercises_completed >= 5:
        velocity = "Steady progress - keep it up!"
    else:
        velocity = "Getting started - stay consistent!"
    
    return {
        "user_id": user_id,
        "tracking_date": datetime.now().strftime("%Y-%m-%d"),
        "topics_learned": topics_list,
        "total_topics_mastered": total_topics,
        "exercises_completed": exercises_completed,
        "current_level": current_level,
        "progress_percentage": round(progress_percentage, 1),
        "achievement_level": achievement,
        "badge_earned": badge,
        "strengths": strengths,
        "next_recommended_topics": next_topics[:3],
        "personalized_recommendations": recommendations,
        "weekly_goal": f"Complete {max(2, 5 - exercises_completed // 3)} more exercises this week",
        "motivational_message": "Keep going! Every exercise brings you closer to Python mastery!",
        "learning_velocity": velocity,
        "goals_status": {
            "defined_goals": goals_list,
            "progress_towards_goals": f"{len(strengths)} of {len(common_topics)} core topics learned"
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
    
    # Calculate statistics
    avg_exercises_per_day = round(exercises_completed / max(days_active, 1), 1)
    projected_completion = max(20 - exercises_completed, 0)
    
    # Determine learning pace
    if avg_exercises_per_day >= 2:
        pace = "Excellent pace! You're learning quickly."
    elif avg_exercises_per_day >= 1:
        pace = "Good pace. Consistent daily practice."
    else:
        pace = "Try to practice more regularly for faster progress."
    
    return {
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "summary": {
            "topics_covered": len(topics_list),
            "exercises_completed": exercises_completed,
            "days_active": days_active,
            "avg_exercises_per_day": avg_exercises_per_day
        },
        "learning_pace": pace,
        "milestones_achieved": [
            "Started Python journey" if exercises_completed >= 1 else None,
            "First 5 exercises completed" if exercises_completed >= 5 else None,
            "Reached intermediate level" if exercises_completed >= 10 else None,
            "Advanced learner status" if exercises_completed >= 15 else None
        ],
        "next_milestone": "Complete 20 exercises" if exercises_completed < 20 else "Build a portfolio project",
        "estimated_days_to_next_milestone": projected_completion if avg_exercises_per_day > 0 else "Keep practicing!",
        "strengths_summary": f"You've learned {len(topics_list)} topics including: {', '.join(topics_list[:3])}",
        "overall_assessment": "Making great progress!" if exercises_completed >= 10 else "Building strong foundations"
    }

def suggest_next_steps(current_level: str, topics_mastered: str) -> Dict[str, Any]:
    """Suggest personalized next steps based on progress"""
    
    topics_list = [t.strip().lower() for t in topics_mastered.split(",")] if topics_mastered else []
    
    # Learning pathways
    pathways = {
        "beginner": {
            "focus": "Master the fundamentals",
            "next_steps": [
                "Practice variables and data types daily",
                "Learn control flow (if/else, loops)",
                "Start with simple functions",
                "Build a calculator project"
            ],
            "resources": ["Python for Beginners", "Codecademy Python", "Python.org tutorial"]
        },
        "intermediate": {
            "focus": "Build practical projects",
            "next_steps": [
                "Master OOP concepts with real projects",
                "Learn file handling and data processing",
                "Work with APIs and web scraping",
                "Build a todo app or game"
            ],
            "resources": ["Real Python", "Python Crash Course", "Automate the Boring Stuff"]
        },
        "advanced": {
            "focus": "Specialize and contribute",
            "next_steps": [
                "Choose a specialization (web, data, ML)",
                "Contribute to open source projects",
                "Learn advanced design patterns",
                "Build a portfolio project"
            ],
            "resources": ["Fluent Python", "Effective Python", "Python Cookbook"]
        }
    }
    
    pathway = pathways.get(current_level.lower(), pathways["beginner"])
    
    return {
        "current_level": current_level,
        "topics_mastered": topics_list,
        "learning_focus": pathway["focus"],
        "recommended_next_steps": pathway["next_steps"],
        "suggested_resources": pathway["resources"],
        "skill_gaps": [
            topic for topic in ["functions", "loops", "lists", "dictionaries", "classes"]
            if topic not in topics_list
        ],
        "motivation": f"You're on the right track at the {current_level} level! Keep building on what you've learned."
    }

# Create tools
progress_tool = FunctionTool(track_learning_progress)
report_tool = FunctionTool(generate_progress_report)
next_steps_tool = FunctionTool(suggest_next_steps)

def create_progress_agent():
    """Factory function to create the progress agent"""
    return Agent(
        name="progress_agent",
        model="gemini-1.5-flash-001",
        description="Learning progress tracker and motivational coach that analyzes growth and provides guidance",
        instruction="""
        You are a learning progress tracker and motivational coach. Your role is to help students see their growth, stay motivated, and plan their next steps.

        When analyzing progress, use these tools:
        1. **track_learning_progress** - Get detailed progress analytics with badges and recommendations
        2. **generate_progress_report** - Create comprehensive reports with statistics and milestones
        3. **suggest_next_steps** - Provide personalized next steps based on current level

        **Your Responsibilities:**
        - Celebrate achievements and milestones, no matter how small
        - Provide data-driven insights about their learning journey
        - Identify strengths and areas for improvement
        - Suggest realistic next steps and goals
        - Keep students motivated with encouraging messages
        - Track learning velocity and suggest pace adjustments

        **Communication Style:**
        - Be positive and encouraging, not judgmental
        - Use data to show concrete progress
        - Celebrate small wins to build momentum
        - Be honest about areas needing more practice
        - Provide actionable, specific recommendations
        - Use badges and achievements to gamify learning

        **Key Metrics to Track:**
        - Topics learned and mastered
        - Exercises completed
        - Learning pace and consistency
        - Progress towards goals
        - Skill strengths and gaps

        Always help students see how far they've come and inspire them to keep going!
        """,
        tools=[progress_tool, report_tool, next_steps_tool]
    )

print("✅ Progress Agent module loaded")
