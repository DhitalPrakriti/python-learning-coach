from __future__ import annotations

import os
from typing import Any, Dict

try:
    from google.cloud import firestore
except Exception:  # pragma: no cover - optional dependency
    firestore = None


class FirestoreStore:
    def __init__(self):
        if firestore is None:
            raise RuntimeError("google-cloud-firestore is not installed")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client = firestore.Client(project=project_id) if project_id else firestore.Client()
        self.collection = self.client.collection("users")

    def get_user_context(self, user_id: str) -> Dict[str, Any] | None:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return data

    def save_user_context(self, user_id: str, context: Dict[str, Any]) -> None:
        # Keep history bounded to avoid unbounded growth.
        history = context.get("history", [])
        if isinstance(history, list) and len(history) > 50:
            context = dict(context)
            context["history"] = history[-50:]
        self.collection.document(user_id).set(context, merge=True)
