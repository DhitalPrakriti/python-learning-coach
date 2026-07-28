import argparse
import sys
from typing import List, Dict, Tuple

import requests


def post_chat(base_url: str, message: str, user_id: str, timeout_s: int) -> Dict[str, str]:
    resp = requests.post(
        f"{base_url}/chat",
        json={"message": message, "user_id": user_id},
        timeout=timeout_s,
    )
    resp.raise_for_status()
    return resp.json()


def check_health(base_url: str, timeout_s: int) -> Dict[str, str]:
    resp = requests.get(f"{base_url}/health", timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()


def response_sets_skill_level(result: Dict[str, str]) -> bool:
    """Check the learner context, not the prose.

    Scanning the reply for "beginner"/"intermediate"/"advanced" always passed,
    because an assessment reply normally names all three. The context is the
    thing routing actually depends on.
    """
    context = result.get("context") or {}
    return context.get("skill_level") in ("beginner", "intermediate", "advanced")


def seed_assessment_until_set(
    base_url: str,
    user_id: str,
    timeout_s: int,
    max_attempts: int,
) -> Dict[str, str]:
    last = {}
    for attempt in range(1, max_attempts + 1):
        msg = (
            "Please assess my Python skill level and tell me if I am beginner, "
            "intermediate, or advanced."
        )
        last = post_chat(base_url, msg, user_id, timeout_s)
        used = last.get("agent_used")
        print(
            f"Seed attempt {attempt}/{max_attempts}: agent={used} "
            f"source={last.get('source')} level={(last.get('context') or {}).get('skill_level')}"
        )
        if used == "assessment" and response_sets_skill_level(last):
            return last
    return last


def run_checks(base_url: str, timeout_s: int, seed_attempts: int) -> int:
    print(f"Checking service health at {base_url}...")
    health = check_health(base_url, timeout_s)
    print(f"Health: {health}")
    if health.get("degraded"):
        last_error = health.get("last_error") or {}
        print(
            f"NOTE: service is degraded ({last_error.get('kind')}). Replies below "
            "come from local content, so they test routing but not the model."
        )

    user_id = "healthcheck_user"

    # Seed assessment until skill_level is likely set (or max attempts reached).
    print("\nSeeding assessment...")
    seed = seed_assessment_until_set(base_url, user_id, timeout_s, seed_attempts)
    print(f"Seed agent: {seed.get('agent_used')}")

    tests: List[Tuple[str, str]] = [
        ("Give me a practice exercise on loops.", "practice"),
        ("Create a 4-week Python roadmap.", "curriculum"),
        ("Explain what a dictionary is in Python.", "teaching"),
        ("Show my progress and give me a badge.", "progress"),
    ]

    failures = 0
    warnings = 0

    print("\nRunning agent checks...")
    for message, expected in tests:
        try:
            result = post_chat(base_url, message, user_id, timeout_s)
            used = result.get("agent_used")
            if used == expected:
                print(f"OK: {expected} -> {used}")
            elif used == "assessment":
                warnings += 1
                print(f"WARN: {expected} -> {used} (skill_level may still be unknown)")
            else:
                failures += 1
                print(f"FAIL: {expected} -> {used}")
        except Exception as exc:
            failures += 1
            print(f"ERROR: {expected} -> {exc}")

    print("\nSummary:")
    print(f"  Failures: {failures}")
    print(f"  Warnings: {warnings}")

    return 1 if failures > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check for Python Learning Coach agents.")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL for the API.")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds.")
    parser.add_argument("--seed-attempts", type=int, default=5, help="Assessment retries to set skill level.")
    args = parser.parse_args()

    return run_checks(args.base_url, args.timeout, args.seed_attempts)


if __name__ == "__main__":
    sys.exit(main())
