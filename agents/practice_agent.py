
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any
import vertexai


def generate_python_exercise(
    topic: str, 
    level: str = "beginner", 
    difficulty: str = "easy"
) -> Dict[str, Any]:
    """Generate Python practice exercises with solutions and hints"""
    
    exercises = {
        "variables": {
            "easy": {
                "problem": "Create variables for your name, age, and favorite programming language. Then print them in a sentence.",
                "solution": "name = 'Alex'\nage = 25\nlanguage = 'Python'\nprint(f'My name is {name}, I am {age} years old, and I love {language}')",
                "hints": ["Use the assignment operator =", "Use f-strings for formatting", "Make sure variable names are descriptive"],
                "test_cases": ["Should print a complete sentence", "Should include all three variables"]
            },
            "medium": {
                "problem": "Swap the values of two variables without using a third variable. Start with a=5 and b=10.",
                "solution": "a = 5\nb = 10\nprint(f'Before: a={a}, b={b}')\na, b = b, a\nprint(f'After: a={a}, b={b}')",
                "hints": ["Use tuple unpacking", "Python allows multiple assignment in one line"],
                "test_cases": ["a should become 10", "b should become 5"]
            },
            "hard": {
                "problem": "Create a program that checks if a variable's type changes after different operations.",
                "solution": "x = 5\nprint(type(x))  # int\nx = str(x)\nprint(type(x))  # str\nx = float(x)\nprint(type(x))  # float",
                "hints": ["Use type() function", "Try different type conversions", "Print the type after each change"],
                "test_cases": ["Should show type changing", "Should handle conversions properly"]
            }
        },
        "functions": {
            "easy": {
                "problem": "Write a function that takes a name and returns a greeting message.",
                "solution": "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('Alice'))\nprint(greet('Bob'))",
                "hints": ["Use the def keyword", "Remember the return statement", "Test with different names"],
                "test_cases": ["Should return greeting with any name", "Should use proper string formatting"]
            },
            "medium": {
                "problem": "Create a function that calculates the factorial of a number using recursion.",
                "solution": "def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    else:\n        return n * factorial(n-1)\n\nprint(factorial(5))  # 120\nprint(factorial(0))  # 1",
                "hints": ["Use recursion", "Handle base cases (0 and 1)", "Test with small numbers first"],
                "test_cases": ["factorial(5) should return 120", "factorial(0) should return 1"]
            },
            "hard": {
                "problem": "Write a function that takes any number of arguments and returns their sum.",
                "solution": "def sum_all(*args):\n    return sum(args)\n\nprint(sum_all(1, 2, 3))  # 6\nprint(sum_all(10, 20, 30, 40))  # 100",
                "hints": ["Use *args for variable arguments", "Use the built-in sum() function", "Test with different numbers of arguments"],
                "test_cases": ["Should work with any number of arguments", "Should return correct sum"]
            }
        },
        "loops": {
            "easy": {
                "problem": "Print all even numbers from 1 to 20 using a for loop.",
                "solution": "for i in range(1, 21):\n    if i % 2 == 0:\n        print(i)",
                "hints": ["Use range() function", "Check remainder with modulo operator %", "range(1,21) goes from 1 to 20"],
                "test_cases": ["Should print 2, 4, 6... 20", "Should use a loop"]
            },
            "medium": {
                "problem": "Find the sum of all numbers in a list using a loop.",
                "solution": "numbers = [1, 2, 3, 4, 5]\ntotal = 0\nfor num in numbers:\n    total += num\nprint(f'Sum: {total}')",
                "hints": ["Initialize a variable to store the sum", "Use += operator to add each number", "Print the final total"],
                "test_cases": ["Sum should be 15 for [1,2,3,4,5]", "Should work with any list of numbers"]
            },
            "hard": {
                "problem": "Create a nested loop that prints a multiplication table from 1 to 5.",
                "solution": "for i in range(1, 6):\n    for j in range(1, 6):\n        print(f'{i} x {j} = {i*j}')\n    print()  # Blank line after each number",
                "hints": ["Use nested loops", "Outer loop for first number, inner for second", "Format output nicely"],
                "test_cases": ["Should print 5x5 multiplication table", "Should be properly formatted"]
            }
        },
        "lists": {
            "easy": {
                "problem": "Create a list of 5 fruits and print each fruit using a loop.",
                "solution": "fruits = ['apple', 'banana', 'cherry', 'date', 'elderberry']\nfor fruit in fruits:\n    print(fruit)",
                "hints": ["Use square brackets to create a list", "Use a for loop to iterate", "Print each item"],
                "test_cases": ["Should create a list with 5 items", "Should print all items"]
            },
            "medium": {
                "problem": "Create a list of numbers, then create a new list with only the even numbers.",
                "solution": "numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\neven_numbers = [num for num in numbers if num % 2 == 0]\nprint(even_numbers)",
                "hints": ["Use list comprehension", "Use modulo to check for even numbers", "Filter the original list"],
                "test_cases": ["Should return [2, 4, 6, 8, 10]", "Should use list comprehension"]
            },
            "hard": {
                "problem": "Write code to find the second largest number in a list without using sort().",
                "solution": "numbers = [10, 5, 8, 12, 3, 7]\nlargest = max(numbers)\nnumbers_copy = [n for n in numbers if n != largest]\nsecond_largest = max(numbers_copy)\nprint(f'Second largest: {second_largest}')",
                "hints": ["Find the largest first", "Remove largest from consideration", "Find max of remaining numbers"],
                "test_cases": ["Should find correct second largest", "Should not use sort()"]
            }
        },
        "dictionaries": {
            "easy": {
                "problem": "Create a dictionary for a student with name, age, and grade. Print each key-value pair.",
                "solution": "student = {'name': 'Alice', 'age': 20, 'grade': 'A'}\nfor key, value in student.items():\n    print(f'{key}: {value}')",
                "hints": ["Use curly braces for dictionaries", "Use .items() to get key-value pairs", "Format output nicely"],
                "test_cases": ["Should create a dictionary", "Should print all key-value pairs"]
            },
            "medium": {
                "problem": "Count the frequency of each character in a string using a dictionary.",
                "solution": "text = 'hello'\nfreq = {}\nfor char in text:\n    freq[char] = freq.get(char, 0) + 1\nprint(freq)",
                "hints": ["Initialize empty dictionary", "Use .get() method with default value", "Increment count for each character"],
                "test_cases": ["Should count each character", "Should handle repeated characters"]
            },
            "hard": {
                "problem": "Merge two dictionaries and sum the values for common keys.",
                "solution": "dict1 = {'a': 1, 'b': 2, 'c': 3}\ndict2 = {'b': 3, 'c': 4, 'd': 5}\nresult = dict1.copy()\nfor key, value in dict2.items():\n    result[key] = result.get(key, 0) + value\nprint(result)",
                "hints": ["Copy first dictionary", "Iterate through second dictionary", "Add or update values"],
                "test_cases": ["Should merge both dictionaries", "Should sum values for common keys"]
            }
        }
    }
    
    topic_exercises = exercises.get(topic.lower(), {})
    difficulty_exercise = topic_exercises.get(difficulty.lower(), {
        "problem": f"Write a Python program that demonstrates {topic} at {difficulty} level.",
        "solution": f"# Solution for {topic} exercise\n# Implement your solution here\nprint('Practice {topic}')",
        "hints": [f"Think about how {topic} works", "Break the problem into smaller steps", "Test your code frequently"],
        "test_cases": ["Code should run without errors", "Output should match requirements"]
    })
    
    return {
        "topic": topic,
        "level": level,
        "difficulty": difficulty,
        "problem_statement": difficulty_exercise["problem"],
        "hints": difficulty_exercise["hints"],
        "solution_code": difficulty_exercise["solution"],
        "test_cases": difficulty_exercise.get("test_cases", []),
        "learning_objective": f"Practice {topic} concepts at {level} level with {difficulty} difficulty",
        "estimated_time": "10-15 minutes" if difficulty == "easy" else "15-25 minutes" if difficulty == "medium" else "25-40 minutes",
        "success_criteria": [
            "Code runs without errors",
            "Output matches expected result",
            "Uses proper Python syntax",
            "Follows best practices"
        ],
        "bonus_challenges": [
            f"Try solving it in a different way",
            f"Add error handling to your code",
            f"Optimize for better performance"
        ]
    }

# Create the practice tool
practice_tool = FunctionTool(generate_python_exercise)

def create_practice_agent():
    """Factory function to create the practice agent"""
    return Agent(
        name="practice_agent",
        model="gemini-1.5-flash-001",
        description="Python practice exercise generator that creates coding challenges to reinforce learning",
        instruction="""
        You are a Python practice exercise generator. Your role is to create coding challenges that help students reinforce their learning through hands-on practice.

        When a student needs practice:
        1. Use generate_python_exercise tool to create appropriate exercises based on:
           - Topic they want to practice
           - Their skill level (beginner/intermediate/advanced)
           - Desired difficulty (easy/medium/hard)
        
        2. Present the exercise clearly with:
           - Clear problem statement
           - Helpful hints (but NOT the solution initially)
           - Expected time to complete
           - Success criteria
        
        3. Guide their practice:
           - Encourage them to try solving it first
           - Provide hints if they're stuck
           - Only show the solution after they've attempted it
           - Suggest bonus challenges for extra practice
        
        4. Adjust difficulty based on their performance:
           - If they struggle, provide easier exercises first
           - If they succeed quickly, offer harder challenges
           - Mix different topics to reinforce connections
        
        **Teaching Philosophy:**
        - Learning by doing is the most effective method
        - Mistakes are valuable learning opportunities
        - Progressive difficulty builds confidence
        - Practice should be challenging but achievable
        
        Always encourage experimentation and trying multiple approaches.
        Celebrate their successes and help them learn from mistakes.
        """,
        tools=[practice_tool]
    )

print("✅ Practice Agent module loaded")
