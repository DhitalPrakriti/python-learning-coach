
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.models.google_llm import Gemini
from typing import Dict, List
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def teach_python_concept(topic: str, level: str, learning_style: str = "visual") -> Dict:
    """Teach a specific Python concept with explanations and examples"""
    
    # Teaching materials for different Python topics
    teaching_materials = {
        "variables": {
            "explanation": "Variables are like containers that store data values. In Python, you create a variable by assigning a value to a name.",
            "examples": [
                "name = 'Alice'  # String variable",
                "age = 25       # Integer variable", 
                "height = 5.9   # Float variable",
                "is_student = True  # Boolean variable"
            ],
            "analogy": "Think of variables like labeled boxes - the label is the variable name, and what's inside is the value.",
            "common_mistakes": ["Forgetting to initialize variables", "Using reserved keywords as names"],
            "practice_exercise": "Create variables for your name, age, and favorite color, then print them."
        },
        "functions": {
            "explanation": "Functions are reusable blocks of code that perform specific tasks. They help organize code and avoid repetition.",
            "examples": [
                "def greet(name):\n    return f\"Hello, {name}!\"\n\nprint(greet(\"Alice\"))",
                "def add_numbers(a, b):\n    return a + b\n\nresult = add_numbers(5, 3)\nprint(result)  # Output: 8"
            ],
            "analogy": "Functions are like kitchen appliances - you give them ingredients (parameters), they do the work, and give you back the result.",
            "common_mistakes": ["Forgetting return statements", "Confusing parameters and arguments"],
            "practice_exercise": "Create a function that calculates the area of a rectangle given length and width."
        },
        "loops": {
            "explanation": "Loops let you execute a block of code repeatedly. Python has 'for' loops for iterating over sequences and 'while' loops for repeating while a condition is true.",
            "examples": [
                "# For loop\nfruits = [\"apple\", \"banana\", \"cherry\"]\nfor fruit in fruits:\n    print(fruit)",
                "# While loop\ncount = 1\nwhile count <= 5:\n    print(count)\n    count += 1"
            ],
            "analogy": "Loops are like assembly lines - they repeatedly perform the same action on different items.",
            "common_mistakes": ["Infinite while loops", "Modifying the list being iterated"],
            "practice_exercise": "Write a loop that prints even numbers from 2 to 20."
        },
        "lists": {
            "explanation": "Lists are ordered, mutable collections of items. They can contain different data types and are very versatile.",
            "examples": [
                "# Creating lists\nnumbers = [1, 2, 3, 4, 5]\nnames = [\"Alice\", \"Bob\", \"Charlie\"]\nmixed = [1, \"hello\", True, 3.14]",
                "# List operations\nfruits = [\"apple\", \"banana\"]\nfruits.append(\"cherry\")  # Add item\nfruits.remove(\"apple\")   # Remove item\nprint(fruits[0])         # Access item"
            ],
            "analogy": "Lists are like train cars - each car holds something, and they're connected in order.",
            "common_mistakes": ["Index errors", "Confusing append() with extend()"],
            "practice_exercise": "Create a list of 5 numbers, then add, remove, and access elements."
        },
        "dictionaries": {
            "explanation": "Dictionaries store key-value pairs. They're unordered, mutable, and very fast for lookups.",
            "examples": [
                "# Creating dictionaries\nstudent = {\"name\": \"Alice\", \"age\": 20, \"grade\": \"A\"}\n\n# Accessing values\nprint(student[\"name\"])  # Output: Alice\n\n# Adding new key-value\nstudent[\"city\"] = \"Boston\""
            ],
            "analogy": "Dictionaries are like real dictionaries - you look up a word (key) to find its definition (value).",
            "common_mistakes": ["Key errors", "Using unhashable types as keys"],
            "practice_exercise": "Create a dictionary for a book with title, author, and year, then add the genre."
        }
    }
    
    material = teaching_materials.get(topic.lower(), {
        "explanation": f"Let me explain {topic} in Python...",
        "examples": [f"Example of {topic} will be shown here"],
        "analogy": f"Think of {topic} like...",
        "common_mistakes": [f"Common mistake with {topic}"],
        "practice_exercise": f"Practice {topic} with this exercise"
    })
    
    # Adapt explanation based on level
    level_adaptations = {
        "beginner": "We'll start with the basics and build up slowly.",
        "intermediate": "Let's dive deeper into the concepts and applications.", 
        "advanced": "We'll explore advanced usage patterns and best practices."
    }
    
    # Adapt based on learning style
    style_suggestions = {
        "visual": "I'll provide clear examples and suggest drawing diagrams.",
        "auditory": "Read the examples out loud and explain them to someone.",
        "kinesthetic": "Type out all the examples yourself and experiment.",
        "adaptive": "Try different approaches to see what works best for you."
    }
    
    return {
        "topic": topic,
        "level": level,
        "learning_style": learning_style,
        "explanation": material["explanation"],
        "examples": material["examples"],
        "analogy": material["analogy"],
        "common_mistakes": material["common_mistakes"],
        "practice_exercise": material["practice_exercise"],
        "level_guidance": level_adaptations.get(level, ""),
        "style_suggestion": style_suggestions.get(learning_style, ""),
        "next_steps": f"After mastering {topic}, consider learning related concepts.",
        "key_takeaways": [
            f"Understand the purpose of {topic}",
            "Practice with the provided examples", 
            "Avoid common mistakes mentioned",
            "Apply to your own projects"
        ]
    }

# Create the teaching tool
teaching_tool = FunctionTool(teach_python_concept)

# Create the teaching agent
teaching_agent = Agent(
    name="TeachingAgent",
    model=Gemini(
        model_name="gemini-2.0-flash-exp",
        api_key=GOOGLE_API_KEY
    ),
    instruction="""You are a patient and effective Python programming teacher. Your role is to explain Python concepts clearly and help students understand through examples and analogies.

When a student asks about a Python topic:
1. Use the teach_python_concept tool to get structured teaching materials
2. Explain the concept in simple, clear language
3. Provide multiple examples with code
4. Use analogies to make concepts relatable
5. Warn about common mistakes and pitfalls
6. Give practical exercises for practice
7. Adapt your teaching to their level and learning style

Be encouraging, answer questions patiently, and check for understanding. If a concept is complex, break it down into smaller parts.""",
    tools=[teaching_tool]
)
