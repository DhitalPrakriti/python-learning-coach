import streamlit as st

st.set_page_config(
    page_title="Python Learning Coach",
    page_icon="🐍",
    layout="wide"
)

st.title("🐍 Python Learning Coach")
st.markdown("### Your AI-Powered Learning System")

def get_ai_response(message):
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['beginner', 'start', 'experience']):
        return "🧠 **Assessment Complete!**\n\nI recommend starting with Python fundamentals.\n\n**Your Learning Path:**\n🎯 Level: Beginner  \n📅 Duration: 6 weeks  \n💡 Focus: Basic syntax, variables, simple programs\n\nReady to create your curriculum?"

    elif any(word in message_lower for word in ['curriculum', 'plan', 'learn']):
        return "📚 **Python Fundamentals Curriculum**\n\n**Week 1-2:** Python Basics & Variables\n**Week 3-4:** Control Structures & Loops  \n**Week 5-6:** Functions & Projects\n\nWant me to explain any concepts?"

    elif any(word in message_lower for word in ['explain', 'teach', 'variable']):
        return "👨‍🏫 **Teaching: Variables**\n\nVariables store data values in Python.\n\n**Examples:**\n```python\nname = \"Alice\"\nage = 25\nheight = 5.9\n```\n\n**Practice:** Create variables for your name and age!"

    elif any(word in message_lower for word in ['exercise', 'practice']):
        return "💻 **Practice Exercise**\n\nCreate a program that asks for user's name and age, then prints a greeting.\n\n**Hint:** Use `input()` and `print()` functions!"

    else:
        return "🐍 **Python Learning Coach**\n\nI'm here to help you learn Python! I can:\n\n🧠 Assess your level\n📚 Create curriculum  \n👨‍🏫 Explain concepts\n💻 Give exercises\n📊 Track progress\n\nAsk me anything about Python learning!"

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("🤖 Learning Coach")
    st.success("All 5 capabilities ready!")
    
    if st.button("Get Started"):
        st.session_state.messages.append(("user", "I want to learn Python"))

for message in st.session_state.messages:
    with st.chat_message(message[0]):
        st.markdown(message[1])

if prompt := st.chat_input("Ask about Python..."):
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    
    response = get_ai_response(prompt)
    
    st.session_state.messages.append(("assistant", response))
    with st.chat_message("assistant"):
        st.markdown(response)

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
