import streamlit as st
import sys
import os
import asyncio

# Add current directory to path
sys.path.append('.')

st.set_page_config(
    page_title="Python Learning Coach",
    page_icon="🐍",
    layout="wide"
)

st.title("🐍 Python Learning Coach")
st.markdown("### Your AI-Powered Learning System with 5 Specialized Agents")

# Try to import agents
try:
    from agents.assessment_agent import assessment_agent
    from agents.curriculum_agent import curriculum_agent, generate_python_curriculum
    from agents.teaching_agent import teaching_agent, teach_python_concept
    from agents.practice_agent import practice_agent, generate_python_exercise
    from agents.progress_agent import progress_agent, track_learning_progress
    
    from google.adk.runners import InMemoryRunner
    
    st.success("✅ All 5 AI Agents Loaded Successfully!")
    
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "experience_level": None,
        "topics_learned": [],
        "exercises_completed": 0
    }

# Sidebar
with st.sidebar:
    st.header("🤖 Agent Status")
    st.success("🧠 Assessment Agent - Ready")
    st.info("📚 Curriculum Agent - Ready") 
    st.warning("👨‍🏫 Teaching Agent - Ready")
    st.error("💻 Practice Agent - Ready")
    st.success("📊 Progress Agent - Ready")
    
    st.header("🚀 Quick Actions")
    if st.button("Get Learning Assessment"):
        st.session_state.messages.append(("user", "I want to assess my Python level"))
    if st.button("View Curriculum"):
        st.session_state.messages.append(("user", "Show me a Python curriculum"))
    if st.button("Practice Exercise"):
        st.session_state.messages.append(("user", "Give me a coding exercise"))

# Chat interface
async def chat_with_agent(message, agent_type):
    """Chat with the appropriate agent"""
    try:
        if agent_type == "assessment":
            runner = InMemoryRunner(agent=assessment_agent)
        elif agent_type == "curriculum":
            runner = InMemoryRunner(agent=curriculum_agent)
        elif agent_type == "teaching":
            runner = InMemoryRunner(agent=teaching_agent)
        elif agent_type == "practice":
            runner = InMemoryRunner(agent=practice_agent)
        else:
            runner = InMemoryRunner(agent=assessment_agent)
            
        response = await runner.run_debug(message)
        return response
    except Exception as e:
        return f"Agent error: {str(e)}"

# Display chat
for message in st.session_state.messages:
    with st.chat_message("user" if message[0] == "user" else "assistant"):
        st.markdown(message[1])

# Chat input
if prompt := st.chat_input("Ask about Python learning..."):
    # Add user message
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Determine which agent to use
    agent_type = "assessment"
    if any(word in prompt.lower() for word in ["curriculum", "plan", "learn"]):
        agent_type = "curriculum"
    elif any(word in prompt.lower() for word in ["explain", "teach", "what is"]):
        agent_type = "teaching" 
    elif any(word in prompt.lower() for word in ["exercise", "practice"]):
        agent_type = "practice"
    
    # Get AI response
    response = asyncio.run(chat_with_agent(prompt, agent_type))
    
    # Add assistant response
    st.session_state.messages.append(("assistant", response))
    with st.chat_message("assistant"):
        st.markdown(response)
