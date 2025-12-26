from google import genai
from google.genai import types
from typing import Dict, Any

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

# 2. THE NEW AGENT CLASS (The "Body")
# ==========================================
class GenAITeachingAgent:
    def __init__(self, client: genai.Client):
        self.client = client
        self.model_id = "gemini-2.5-flash"
        
        # KEY CHANGE: We put the RAW function in a list. 
        # No 'FunctionTool' wrapper needed!
        self.tools = [teach_python_concept]

    def query(self, message: str) -> str:
        """
        Sends the message to Gemini with the tools enabled.
        The SDK handles the 'Function Calling' automatically.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=message,
                config=types.GenerateContentConfig(
                    tools=self.tools,  # <--- We pass the tool here
                    system_instruction="""
                        You are a patient Python teacher. 
                        When asked about a topic, YOU MUST USE the 'teach_python_concept' tool 
                        to get the lesson plan, then explain it to the student.
                    """
                )
            )
 
            # The model will run the tool internally and give you the final text
            return response.text
            
        except Exception as e:
            return f"Agent Error: {str(e)}"

# ==========================================
# 3. THE FACTORY
# ==========================================
def create_teaching_agent(client: genai.Client):
    return GenAITeachingAgent(client)

