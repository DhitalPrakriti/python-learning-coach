
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, List, Any
import vertexai

def generate_python_curriculum(
    experience_level: str, 
    learning_goals: str = "general Python proficiency", 
    focus_areas: str = None
) -> Dict[str, Any]:
    """Generate personalized Python learning curriculum based on assessment"""
    
    # Parse focus_areas if provided as comma-separated string
    focus_list = focus_areas.split(",") if focus_areas else ["core programming concepts"]
    
    # Comprehensive curriculum templates
    python_curricula = {
        "beginner": {
            "title": "Python Fundamentals Path (6 Weeks)",
            "description": "Perfect for absolute beginners starting their programming journey",
            "weekly_plan": [
                {
                    "week": 1,
                    "topic": "Python Basics & Setup",
                    "lessons": ["Installing Python", "Running first program", "Variables & Data Types", "Basic Input/Output"],
                    "practice": "Create a simple calculator"
                },
                {
                    "week": 2, 
                    "topic": "Control Structures",
                    "lessons": ["If/Else statements", "Comparison operators", "Logical operators", "Boolean logic"],
                    "practice": "Build a number guessing game"
                },
                {
                    "week": 3,
                    "topic": "Loops & Iterations", 
                    "lessons": ["For loops", "While loops", "Loop control (break/continue)", "Nested loops"],
                    "practice": "Create multiplication tables"
                },
                {
                    "week": 4,
                    "topic": "Functions & Modular Code",
                    "lessons": ["Function definition", "Parameters & return values", "Scope", "Built-in functions"],
                    "practice": "Build a temperature converter"
                },
                {
                    "week": 5,
                    "topic": "Data Structures",
                    "lessons": ["Lists", "Dictionaries", "Tuples", "Sets"],
                    "practice": "Create a student grade tracker"
                },
                {
                    "week": 6,
                    "topic": "Final Project & Next Steps",
                    "lessons": ["Putting it all together", "Debugging basics", "Next learning steps"],
                    "practice": "Build a personal todo list application"
                }
            ],
            "resources": [
                "Python Official Documentation",
                "Codecademy Python Course", 
                "freeCodeCamp Python Tutorial",
                "Automate the Boring Stuff with Python"
            ],
            "pace": "Slow and steady",
            "milestones": ["Week 1: First program", "Week 3: First game", "Week 6: First app"]
        },
        "intermediate": {
            "title": "Python Developer Path (8 Weeks)", 
            "description": "For those with basic Python knowledge ready to build real applications",
            "weekly_plan": [
                {
                    "week": 1,
                    "topic": "Object-Oriented Programming",
                    "lessons": ["Classes & Objects", "Inheritance", "Polymorphism", "Encapsulation"],
                    "practice": "Build a banking system with classes"
                },
                {
                    "week": 2,
                    "topic": "Advanced Data Structures",
                    "lessons": ["List comprehensions", "Dictionary comprehensions", "Generators", "Iterators"],
                    "practice": "Data processing with comprehensions"
                },
                {
                    "week": 3,
                    "topic": "Error Handling & Debugging",
                    "lessons": ["Try/Except blocks", "Custom exceptions", "Logging", "Debugging tools"],
                    "practice": "Robust file processor with error handling"
                },
                {
                    "week": 4,
                    "topic": "File Handling & Data Persistence",
                    "lessons": ["Reading/writing files", "CSV/JSON processing", "Working with databases", "SQL basics"],
                    "practice": "Build a contact management system"
                },
                {
                    "week": 5,
                    "topic": "Working with APIs",
                    "lessons": ["HTTP requests", "REST APIs", "JSON parsing", "API authentication"],
                    "practice": "Create a weather app using public API"
                },
                {
                    "week": 6,
                    "topic": "Popular Python Libraries",
                    "lessons": ["Requests for web", "Pandas for data", "Matplotlib for visualization", "BeautifulSoup for web scraping"],
                    "practice": "Web scraper or data analysis project"
                },
                {
                    "week": 7,
                    "topic": "Testing & Code Quality",
                    "lessons": ["Unit testing with pytest", "Code documentation", "Code style (PEP8)", "Version control with Git"],
                    "practice": "Write tests for previous projects"
                },
                {
                    "week": 8,
                    "topic": "Capstone Project",
                    "lessons": ["Project planning", "Implementation", "Testing", "Deployment"],
                    "practice": "Build a complete web application"
                }
            ],
            "resources": [
                "Real Python Tutorials",
                "Python Crash Course", 
                "Effective Python",
                "Python documentation"
            ],
            "pace": "Moderate with hands-on projects",
            "milestones": ["Week 4: Database app", "Week 6: API integration", "Week 8: Portfolio project"]
        },
        "advanced": {
            "title": "Python Mastery Path (6 Weeks)",
            "description": "For experienced developers mastering advanced Python concepts",
            "weekly_plan": [
                {
                    "week": 1,
                    "topic": "Advanced OOP & Design Patterns",
                    "lessons": ["Abstract classes", "Interfaces", "Singleton, Factory patterns", "Dependency injection"],
                    "practice": "Implement common design patterns"
                },
                {
                    "week": 2,
                    "topic": "Concurrency & Parallelism",
                    "lessons": ["Threading vs Multiprocessing", "Async/Await", "Concurrent futures", "GIL understanding"],
                    "practice": "Build a concurrent web scraper"
                },
                {
                    "week": 3,
                    "topic": "Performance Optimization",
                    "lessons": ["Profiling code", "Memory management", "Caching strategies", "Algorithm optimization"],
                    "practice": "Optimize a slow application"
                },
                {
                    "week": 4,
                    "topic": "Advanced Libraries & Frameworks",
                    "lessons": ["Django/Flask for web", "NumPy/SciPy for science", "PyTorch/TensorFlow for ML", "FastAPI for APIs"],
                    "practice": "Choose and build with a framework"
                },
                {
                    "week": 5,
                    "topic": "System Design & Architecture",
                    "lessons": ["Microservices", "API design", "Database design", "System scalability"],
                    "practice": "Design and document a system"
                },
                {
                    "week": 6,
                    "topic": "Open Source & Career Development",
                    "lessons": ["Contributing to open source", "Code reviews", "Technical interviews", "Career planning"],
                    "practice": "Contribute to a Python open source project"
                }
            ],
            "resources": [
                "Fluent Python",
                "Python Cookbook",
                "Architecture Patterns with Python", 
                "Advanced Python Mastery"
            ],
            "pace": "Fast-paced with complex projects",
            "milestones": ["Week 3: Performance tuning", "Week 5: System design", "Week 6: Open source contribution"]
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
        "key_milestones": curriculum["milestones"],
        "total_weeks": len(curriculum["weekly_plan"]),
        "success_tips": [
            "Practice coding daily, even for 15 minutes",
            "Build projects to reinforce learning", 
            "Join Python communities for support",
            "Don't hesitate to ask questions"
        ]
    }

# Create the curriculum tool
curriculum_tool = FunctionTool(generate_python_curriculum)

def create_curriculum_agent():
    """Factory function to create the curriculum agent"""
    return Agent(
        name="curriculum_agent",
        model="gemini-1.5-flash-001",
        description="Expert Python curriculum designer that creates personalized learning paths",
        instruction="""
        You are an expert Python curriculum designer. Your job is to create personalized learning paths based on the user's experience level and goals.

        When a user provides their experience level (beginner/intermediate/advanced) and learning goals:
        1. Use the generate_python_curriculum tool to create a comprehensive learning plan
        2. Provide a structured weekly breakdown with lessons and practice projects
        3. Recommend appropriate learning resources
        4. Set clear milestones and success tips
        5. Be encouraging and specific about what they'll achieve

        **Key Responsibilities:**
        - Design realistic, achievable learning timelines (6-8 weeks)
        - Balance theory with hands-on practice projects
        - Recommend quality resources appropriate for their level
        - Set measurable milestones to track progress
        
        Always start by acknowledging their goals and experience level, then present the curriculum in a clear, organized way.
        Emphasize that consistency and practice are more important than speed.
        """,
        tools=[curriculum_tool]
    )

print("✅ Curriculum Agent module loaded")
