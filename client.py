# client.py
from uuid import uuid4
import textwrap

import requests

URL = "http://127.0.0.1:8080/chat"
USER_ID = f"demo_{uuid4().hex[:8]}"


def start_chat():
    print("Python Learning Coach is ONLINE!")
    print("Type 'exit' to end the session.\n")

    session = requests.Session()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("Goodbye! Happy coding!")
            break

        payload = {"message": user_input, "user_id": USER_ID}

        try:
            print("Coach: (thinking...)")
            resp = session.post(URL, json=payload, timeout=30)

            if resp.status_code != 200:
                print(f"\n[ERROR] HTTP {resp.status_code}\n{resp.text}\n")
                continue

            try:
                data = resp.json()
            except ValueError:
                print("\n[ERROR] Server returned non-JSON response:\n")
                print(resp.text)
                print()
                continue

            ai_response = data.get("response", "")
            agent_name = data.get("agent_used", "unknown").upper()
            source = data.get("source", "unknown")

            wrapped = "\n".join(textwrap.wrap(ai_response, width=90))
            print(f"\n[{agent_name} AGENT | {source}]:\n{wrapped}\n")

        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Can't connect to server.")
            print("Make sure Flask is running: python main.py\n")
        except requests.exceptions.Timeout:
            print("\n[ERROR] Request timed out (30s). Try again.\n")
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}\n")


if __name__ == "__main__":
    start_chat()
