import streamlit as st
import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

st.set_page_config(
    page_title="Python Learning Coach",
    page_icon="🐍", 
    layout="wide"
)

st.title("🐍 Python Learning Coach")
st.markdown("### Your Complete AI-Powered Learning System")

# System prompt that simulates all 5 agents
system_prompt = """
You are a comprehensive Python Learning Coach with 5 specialized capabilities:

1. 🧠 ASSESSMENT AGENT: Evaluate programming experience and learning goals
2. 📚 CURRICULUM AGENT: Create personalized learning paths and study plans  
3. 👨‍🏫 TEACHING AGENT: Explain Python concepts with clear examples and analogies
4. 💻 PRACTICE AGENT: Generate appropriate coding exercises and challenges
5. 📊 PROGRESS AGENT: Track learning progress and provide motivational feedback

Adapt your responses based on what the student needs. Be encouraging and patient.
"""

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        ("assistant", "🐍 **Welcome to Python Learning Coach!**\n\nI'm your AI tutor with 5 capabilities:\n\n🧠 Assessment - Evaluate your level  \n📚 Curriculum - Create learning plans  \n👨‍🏫 Teaching - Explain concepts  \n💻 Practice - Give exercises  \n📊 Progress - Track your journey\n\n**Try asking:**\n- \"I'm a beginner\"\n- \"Create a curriculum\"  \n- \"Explain variables\"\n- \"Give me an exercise\"\n- \"How am I doing?\"")
    ]

# Sidebar
with st.sidebar:
    st.header("🤖 AI Agents")
    st.success("🧠 Assessment - Ready")
    st.info("📚 Curriculum - Ready")
    st.warning("👨‍🏫 Teaching - Ready") 
    st.error("💻 Practice - Ready")
    st.success("📊 Progress - Ready")
    
    st.header("🚀 Quick Start")
    if st.button("I'm a Beginner"):
        st.session_state.messages.append(("user", "I'm a complete beginner"))
    if st.button("Get Curriculum"):
        st.session_state.messages.append(("user", "Create a Python curriculum for me"))
    if st.button("Practice Exercise"):
        st.session_state.messages.append(("user", "Give me a coding exercise"))

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message[0]):
        st.markdown(message[1])

# Chat input
if prompt := st.chat_input("Ask about Python learning..."):
    # Add user message
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate AI response
    try:
        # Build conversation context
        conversation = system_prompt + "\n\nRecent conversation:\n"
        for msg in st.session_state.messages[-6:]:
            role = "Student" if msg[0] == "user" else "Tutor"
            conversation += f"{role}: {msg[1]}\n"
        
        conversation += f"Student: {prompt}\nTutor:"
        
        response = model.generate_content(conversation)
        
        # Add assistant response
        st.session_state.messages.append(("assistant", response.text))
        with st.chat_message("assistant"):
            st.markdown(response.text)
            
    except Exception as e:
        error_msg = f"⚠️ System temporarily unavailable. Please try again."
        st.session_state.messages.append(("assistant", error_msg))
        with st.chat_message("assistant"):
            st.markdown(error_msg)

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = [
        ("assistant", "Chat cleared! How can I help you learn Python today?")
    ]
    st.rerun()
