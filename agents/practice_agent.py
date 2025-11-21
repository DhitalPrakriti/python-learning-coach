
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.models.google_llm import Gemini
from typing import Dict, List
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def generate_python_exercise(topic: str, level: str, difficulty: str = "easy") -> Dict:
    """Generate Python practice exercises with solutions"""
    
    exercises = {
        "variables": {
            "easy": {
                "problem": "Create variables for your name, age, and favorite programming language. Then print them in a sentence.",
                "solution": "name = 'Alex'\nage = 25\nlanguage = 'Python'\nprint(f'My name is {name}, I am {age} years old, and I love {language}')",
                "hints": ["Use the assignment operator =", "Use f-strings for formatting", "Make sure variable names are descriptive"]
            },
            "medium": {
                "problem": "Swap the values of two variables without using a third variable.",
                "solution": "a = 5\nb = 10\na, b = b, a\nprint(f'a = {a}, b = {b}')",
                "hints": ["Use tuple unpacking", "Python allows multiple assignment"]
            }
        },
        "functions": {
            "easy": {
                "problem": "Write a function that takes a name and returns a greeting message.",
                "solution": "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('Alice'))",
                "hints": ["Use the def keyword", "Remember the return statement", "Test with different names"]
            },
            "medium": {
                "problem": "Create a function that calculates the factorial of a number.",
                "solution": "def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    else:\n        return n * factorial(n-1)\n\nprint(factorial(5))",
                "hints": ["Use recursion", "Handle base cases (0 and 1)", "Test with small numbers first"]
            }
        },
        "loops": {
            "easy": {
                "problem": "Print all even numbers from 1 to 20 using a loop.",
                "solution": "for i in range(1, 21):\n    if i % 2 == 0:\n        print(i)",
                "hints": ["Use range() function", "Check remainder with modulo operator %", "range(1,21) goes from 1 to 20"]
            },
            "medium": {
                "problem": "Find the sum of all numbers in a list using a loop.",
                "solution": "numbers = [1, 2, 3, 4, 5]\ntotal = 0\nfor num in numbers:\n    total += num\nprint(total)",
                "hints": ["Initialize a variable to store the sum", "Use += operator to add each number", "Print the final total"]
            }
        }
    }
    
    topic_exercises = exercises.get(topic.lower(), {})
    difficulty_exercise = topic_exercises.get(difficulty.lower(), {
        "problem": f"Write a Python program that demonstrates {topic}.",
        "solution": f"# Solution for {topic} exercise\nprint('Implement your solution here')",
        "hints": [f"Think about how {topic} works", "Break the problem into smaller steps"]
    })
    
    return {
        "topic": topic,
        "level": level,
        "difficulty": difficulty,
        "problem": difficulty_exercise["problem"],
        "hints": difficulty_exercise["hints"],
        "solution": difficulty_exercise["solution"],
        "learning_objective": f"Practice {topic} concepts at {level} level",
        "estimated_time": "10-15 minutes",
        "success_criteria": ["Code runs without errors", "Output matches expected result", "Uses proper Python syntax"]
    }

# Create the practice tool
practice_tool = FunctionTool(generate_python_exercise)

# Create the practice agent
practice_agent = Agent(
    name="PracticeAgent",
    model=Gemini(model_name="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
    instruction="""You are a Python practice exercise generator. Create coding challenges that help students reinforce their learning.

When a student needs practice:
1. Use generate_python_exercise tool to create appropriate exercises
2. Provide clear problem statements
3. Offer helpful hints (but not the solution)
4. Adjust difficulty based on student level
5. Encourage trying multiple approaches

Focus on practical, hands-on coding practice that builds real skills.""",
    tools=[practice_tool]
)
