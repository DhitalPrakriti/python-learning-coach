# main.py - PRODUCTION READY (CLEANED)
from flask import Flask, request, jsonify
# import vertexai  <-- REMOVED (Not needed with API Key)
from agents.coordinator import LearningCoachCoordinator # Ensure correct import path
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ==========================================
# 1. INITIALIZATION
# ==========================================
# We no longer need PROJECT_ID or LOCATION for the API Key method.
print("🔄 Initializing Learning Coach Coordinator...")

# The Coordinator now handles all authentication internally via your API Key
coordinator = LearningCoachCoordinator()
coordinator.initialize_agents()
print("✅ Coordinator and all 5 agents initialized!")

# Thread pool for scaling
executor = ThreadPoolExecutor(max_workers=10)

def run_async(coro):
    """Bridge to run async agent logic in synchronous Flask securely"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


# 2. DOCKER HEALTH CHECK

@app.route('/health', methods=['GET'])
def health():
    """Required for Docker HEALTHCHECK and Cloud Run Liveness Probes"""
    return jsonify({
        'status': 'healthy',
        'agents_count': len(coordinator.agents) if hasattr(coordinator, 'agents') else 0,
        'active_users': len(coordinator.user_contexts)
    }), 200

# 3. INTELLIGENT ROUTER
=
def determine_agent(message: str, user_id: str) -> str:
    """Heuristic logic to route the user to the correct expert agent"""
    msg = message.lower()
    context = coordinator.get_user_context(user_id)
    
    # 1. New user check
    if context.get('skill_level') == 'unknown':
        return 'assessment'
    
    # 2. Keyword based routing
    if any(w in msg for w in ['assess', 'level', 'skill', 'evaluate']):
        return 'assessment'
    elif any(w in msg for w in ['plan', 'roadmap', 'curriculum', 'path']):
        return 'curriculum'
    elif any(w in msg for w in ['explain', 'teach', 'what is', 'how to']):
        return 'teaching'
    elif any(w in msg for w in ['practice', 'exercise', 'task', 'code']):
        return 'practice'
    elif any(w in msg for w in ['progress', 'badge', 'achievement', 'report']):
        return 'progress'
    
    # 3. Smart Default
    return 'teaching' if len(context.get('topics_learned', [])) < 1 else 'practice'

# ==========================================
# 4. API ENDPOINTS
# ==========================================
@app.route('/chat', methods=['POST'])
def chat():
    """The main entry point for the Multi-Agent Coach"""
    try:
        # Use get_json for safer parsing of POST data
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'default_user')
        
        if not user_message:
            return jsonify({'error': 'Message is empty'}), 400
        
        # Determine the right agent
        agent_name = determine_agent(user_message, user_id)
        
        # Run the async agent logic
        response = run_async(
            coordinator.process_with_agent(agent_name, user_message, user_id)
        )
        
        return jsonify({
            'response': response,
            'agent_used': agent_name,
            'user_id': user_id,
            'status': 'success'
        })
    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        return jsonify({'error': f"Agent processing failed: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def index():
    """Simple status page"""
    return jsonify({
        'service': 'Python Learning Coach AI',
        'status': 'Online',
        'agents': coordinator.agents if hasattr(coordinator, 'agents') else []
    })

# ==========================================
# 5. SERVER RUN
# ==========================================
if __name__ == '__main__':
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
