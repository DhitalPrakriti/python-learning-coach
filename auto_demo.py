# auto_demo.py
import time

import requests

BASE_URL = "http://localhost:8080"

print("MULTI-AGENT LEARNING COACH - AUTOMATIC DEMO")
print("=" * 60)
print("This demo automatically showcases all 5 coach agents.")
print("=" * 60)

try:
    health_response = requests.get(f"{BASE_URL}/health", timeout=5)
    if health_response.status_code == 200:
        print("OK: Server is running!")
    else:
        print("ERROR: Server not responding properly")
        raise SystemExit(1)
except Exception:
    print("ERROR: Cannot connect to server. Make sure it's running with: python main.py")
    raise SystemExit(1)

time.sleep(1)

demo_sequence = [
    {
        "query": "I'm completely new to programming and want to learn Python",
        "agent": "Assessment Agent",
        "description": "Determines skill level and learning style",
    },
    {
        "query": "Can you create a personalized 4-week learning plan for me?",
        "agent": "Curriculum Agent",
        "description": "Creates structured learning paths",
    },
    {
        "query": "Explain what variables and data types are in Python",
        "agent": "Teaching Agent",
        "description": "Explains concepts with examples",
    },
    {
        "query": "Give me a beginner coding exercise to practice Python lists",
        "agent": "Practice Agent",
        "description": "Generates coding challenges",
    },
    {
        "query": "How would you track my learning progress and keep me motivated?",
        "agent": "Progress Agent",
        "description": "Tracks progress and provides motivation",
    },
]

print(f"\nTesting {len(demo_sequence)} specialized agents...")
print("=" * 60)

for i, demo in enumerate(demo_sequence, 1):
    print(f"\nDEMO {i}/{len(demo_sequence)}")
    print(f"Agent: {demo['agent']}")
    print(f"Description: {demo['description']}")
    print(f"User asks: \"{demo['query']}\"")
    print("-" * 50)

    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": demo["query"], "user_id": f"demo_user_{i}"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            actual_agent = data.get("agent_used", "unknown").upper()
            source = data.get("source", "unknown")
            answer = data.get("response", "")

            print(f"OK: Agent responded: {actual_agent} ({source})")

            if answer:
                print("\nResponse preview:")
                print("-" * 40)
                preview_lines = [line.strip() for line in answer.splitlines() if line.strip()][:3]
                for line in preview_lines:
                    print(f"  {line[:80]}" + ("..." if len(line) > 80 else ""))
                print("-" * 40)
                print(f"Full response: {len(answer)} characters")
            else:
                print("ERROR: No response text")
        else:
            print(f"ERROR: Server error: {response.status_code}")
            print(f"   {response.text[:100]}")

    except Exception as e:
        print(f"ERROR: {e}")

    time.sleep(2)

print("\n" + "=" * 60)
print("DEMO COMPLETE!")
print("\nSUMMARY:")
print(f"- Tested {len(demo_sequence)} specialized AI agents")
print("- Each agent handles a specific aspect of learning")
print("- Coordinator intelligently routes queries")
print("- Flask REST API is ready for local demos")
