
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any
import vertexai

# Initialize Vertex AI
vertexai.init(project="python-learning-coach-ai", location="us-central1")

def teach_python_concept(
    topic: str, 
    level: str = "beginner", 
    learning_style: str = "adaptive"
) -> Dict[str, Any]:
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
            "common_mistakes": ["Forgetting to initialize variables", "Using reserved keywords as names", "Case sensitivity issues"],
            "practice_exercise": "Create variables for your name, age, and favorite color, then print them."
        },
        "functions": {
            "explanation": "Functions are reusable blocks of code that perform specific tasks. They help organize code and avoid repetition.",
            "examples": [
                "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('Alice'))",
                "def add_numbers(a, b):\n    return a + b\n\nresult = add_numbers(5, 3)\nprint(result)  # Output: 8"
            ],
            "analogy": "Functions are like kitchen appliances - you give them ingredients (parameters), they do the work, and give you back the result.",
            "common_mistakes": ["Forgetting return statements", "Confusing parameters and arguments", "Not handling edge cases"],
            "practice_exercise": "Create a function that calculates the area of a rectangle given length and width."
        },
        "loops": {
            "explanation": "Loops let you execute a block of code repeatedly. Python has 'for' loops for iterating over sequences and 'while' loops for repeating while a condition is true.",
            "examples": [
                "# For loop\nfruits = ['apple', 'banana', 'cherry']\nfor fruit in fruits:\n    print(fruit)",
                "# While loop\ncount = 1\nwhile count <= 5:\n    print(count)\n    count += 1"
            ],
            "analogy": "Loops are like assembly lines - they repeatedly perform the same action on different items.",
            "common_mistakes": ["Infinite while loops", "Modifying the list being iterated", "Off-by-one errors"],
            "practice_exercise": "Write a loop that prints even numbers from 2 to 20."
        },
        "lists": {
            "explanation": "Lists are ordered, mutable collections of items. They can contain different data types and are very versatile.",
            "examples": [
                "# Creating lists\nnumbers = [1, 2, 3, 4, 5]\nnames = ['Alice', 'Bob', 'Charlie']\nmixed = [1, 'hello', True, 3.14]",
                "# List operations\nfruits = ['apple', 'banana']\nfruits.append('cherry')  # Add item\nfruits.remove('apple')   # Remove item\nprint(fruits[0])         # Access item"
            ],
            "analogy": "Lists are like train cars - each car holds something, and they're connected in order.",
            "common_mistakes": ["Index errors", "Confusing append() with extend()", "Not understanding mutability"],
            "practice_exercise": "Create a list of 5 numbers, then add, remove, and access elements."
        },
        "dictionaries": {
            "explanation": "Dictionaries store key-value pairs. They're unordered, mutable, and very fast for lookups.",
            "examples": [
                "# Creating dictionaries\nstudent = {'name': 'Alice', 'age': 20, 'grade': 'A'}\n\n# Accessing values\nprint(student['name'])  # Output: Alice\n\n# Adding new key-value\nstudent['city'] = 'Boston'"
            ],
            "analogy": "Dictionaries are like real dictionaries - you look up a word (key) to find its definition (value).",
            "common_mistakes": ["Key errors when accessing non-existent keys", "Using unhashable types as keys", "Forgetting .get() method"],
            "practice_exercise": "Create a dictionary for a book with title, author, and year, then add the genre."
        },
        "classes": {
            "explanation": "Classes are blueprints for creating objects. They bundle data (attributes) and functionality (methods) together.",
            "examples": [
                "class Dog:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n    \n    def bark(self):\n        return f'{self.name} says woof!'\n\nmy_dog = Dog('Buddy', 3)\nprint(my_dog.bark())"
            ],
            "analogy": "Classes are like cookie cutters - the class is the cutter, and objects are the cookies made from it.",
            "common_mistakes": ["Forgetting self parameter", "Not understanding __init__", "Confusing class vs instance variables"],
            "practice_exercise": "Create a Car class with make, model, and year attributes, plus a method to display info."
        },
        "conditionals": {
            "explanation": "Conditionals allow your code to make decisions based on conditions. Use if, elif, and else statements.",
            "examples": [
                "age = 18\nif age >= 18:\n    print('Adult')\nelse:\n    print('Minor')",
                "score = 85\nif score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelse:\n    grade = 'C'\nprint(f'Grade: {grade}')"
            ],
            "analogy": "Conditionals are like traffic lights - different paths are taken based on the signal (condition).",
            "common_mistakes": ["Using = instead of ==", "Incorrect indentation", "Logic errors in conditions"],
            "practice_exercise": "Write code that checks if a number is positive, negative, or zero."
        }
    }
    
    material = teaching_materials.get(topic.lower(), {
        "explanation": f"Let me explain {topic} in Python. This is a fundamental concept in programming.",
        "examples": [f"# Example of {topic}\n# Code will be demonstrated based on the concept"],
        "analogy": f"Think of {topic} as a tool in your programming toolbox.",
        "common_mistakes": [f"Be careful with {topic} syntax", "Practice regularly"],
        "practice_exercise": f"Try implementing {topic} in a simple program"
    })
    
    # Adapt explanation based on level
    level_adaptations = {
        "beginner": "We'll start with the basics and build up slowly. Don't worry if it takes time to understand.",
        "intermediate": "Let's dive deeper into the concepts and practical applications.", 
        "advanced": "We'll explore advanced usage patterns, edge cases, and best practices."
    }
    
    # Adapt based on learning style
    style_suggestions = {
        "visual": "I recommend drawing diagrams or flowcharts to visualize how this works.",
        "auditory": "Read the examples out loud and explain them to yourself or someone else.",
        "kinesthetic": "Type out all the examples yourself and experiment with variations.",
        "adaptive": "Try multiple approaches - read, write, and discuss to see what works best."
    }
    
    return {
        "topic": topic,
        "level": level,
        "learning_style": learning_style,
        "explanation": material["explanation"],
        "code_examples": material["examples"],
        "real_world_analogy": material["analogy"],
        "common_mistakes": material["common_mistakes"],
        "practice_exercise": material["practice_exercise"],
        "level_guidance": level_adaptations.get(level, level_adaptations["beginner"]),
        "style_suggestion": style_suggestions.get(learning_style, style_suggestions["adaptive"]),
        "next_steps": f"After mastering {topic}, you'll be ready for more advanced concepts.",
        "key_takeaways": [
            f"Understand the purpose and syntax of {topic}",
            "Practice with the provided examples", 
            "Avoid the common mistakes mentioned",
            "Apply this concept in your own projects"
        ],
        "additional_resources": [
            f"Python documentation on {topic}",
            f"Interactive {topic} tutorials online",
            f"Practice {topic} on coding platforms"
        ]
    }

# Create the teaching tool
teaching_tool = FunctionTool(teach_python_concept)

def create_teaching_agent():
    """Factory function to create the teaching agent"""
    return Agent(
        name="teaching_agent",
        model="gemini-1.5-flash-001",
        description="Patient and effective Python programming teacher who explains concepts clearly",
        instruction="""
        You are a patient and effective Python programming teacher. Your role is to explain Python concepts clearly and help students understand through examples and analogies.

        When a student asks about a Python topic:
        1. Use the teach_python_concept tool to get structured teaching materials
        2. Explain the concept in simple, clear language appropriate for their level
        3. Provide multiple code examples they can try
        4. Use real-world analogies to make abstract concepts relatable
        5. Warn about common mistakes and pitfalls to avoid
        6. Give practical exercises for hands-on practice
        7. Adapt your teaching to their level (beginner/intermediate/advanced) and learning style

        **Teaching Principles:**
        - Be encouraging and supportive, not judgmental
        - Break complex concepts into smaller, digestible parts
        - Check for understanding by asking if they have questions
        - Relate new concepts to previously learned material
        - Emphasize learning by doing through practice exercises
        
        **Topics You Can Teach:**
        Variables, Functions, Loops, Lists, Dictionaries, Classes, Conditionals, and more.
        
        If asked about a topic not in your knowledge base, explain it clearly in your own words and provide relevant examples.
        Always end with an encouragement to practice and experiment.
        """,
        tools=[teaching_tool]
    )

print("✅ Teaching Agent module loaded")
