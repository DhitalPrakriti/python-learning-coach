from google import genai
from google.genai import types
import os
from datetime import datetime
from typing import Dict, Any

# IMPORT ALL AGENTS
from agents.teaching_agent import create_teaching_agent
from agents.assessment_agent import create_assessment_agent
from agents.curriculum_agent import create_curriculum_agent
from agents.practice_agent import create_practice_agent
from agents.progress_agent import create_progress_agent

class LearningCoachCoordinator:
    def __init__(self):
        self.user_contexts = {}
        
        # --- API KEY SETUP ---
        # written by fix_coordinator.py
        api_key = "AIzaSyC-cQiSMZXslKcpCR0yOE_1c3YZi2PzrQA"
        
        # Initialize the client
        # We use v1beta because that is often safer for newer models
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1beta')
        )
        
        self.agent_registry = {}
        self.initialize_agents()
        print(f"📊 Coordinator initialized")

    def initialize_agents(self):
        print("🔄 Loading All Agents...")
        try:
            self.agent_registry["teaching"] = create_teaching_agent(self.client)
            self.agent_registry["assessment"] = create_assessment_agent(self.client)
            self.agent_registry["curriculum"] = create_curriculum_agent(self.client)
            self.agent_registry["practice"] = create_practice_agent(self.client)
            self.agent_registry["progress"] = create_progress_agent(self.client)
            print("✅ All Agents CONNECTED.")
        except Exception as e:
            print(f"⚠️ Agent Loading Failed: {e}")

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                'skill_level': 'unknown',
                'history': [],
                'last_interaction': datetime.now().isoformat()
            }
        return self.user_contexts[user_id]

    async def process_with_agent(self, agent_name: str, message: str, user_id: str) -> str:
        context = self.get_user_context(user_id)
        active_agent = self.agent_registry.get(agent_name)
        
        if active_agent:
            print(f"🤖 Delegating to: {agent_name}")
            try:
                response = active_agent.query(message)
                self._update_user_context(user_id, context, message, str(response), agent_name)
                return str(response)
            except Exception as e:
                return f"Agent Error: {str(e)}"
        else:
            return f"Error: Agent '{agent_name}' not found."

    def _update_user_context(self, user_id, context, message, response, agent):
        context['history'].append({'role': 'user', 'content': message})
        context['history'].append({'role': agent, 'content': response[:200]})
