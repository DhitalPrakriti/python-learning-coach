import streamlit as st
import requests
import json
import os

st.set_page_config(
    page_title="Python Learning Coach",
    page_icon="🐍",
    layout="wide"
)

st.title("🐍 Python Learning Coach")
st.markdown("### Your AI-Powered Learning System")

# Simple system without external dependencies
def get_ai_response(message):
    """Simulate AI responses with predefined logic"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['beginner', 'start', 'experience']):
        return """🧠 **Assessment Complete!**

I recommend starting with Python fundamentals.

**Your Learning Path:**
🎯 Level: Beginner  
📅 Duration: 6 weeks  
💡 Focus: Basic syntax, variables, simple programs

Ready to create your curriculum?"""

    elif any(word in message_lower for word in ['curriculum', 'plan', 'learn']):
        return """📚 **Python Fundamentals Curriculum**

**Week 1-2:** Python Basics & Variables
**Week 3-4:** Control Structures & Loops  
**Week 5-6:** Functions & Projects

Want me to explain any concepts?"""

    elif any(word in message_lower for word in ['explain', 'teach', 'variable']):
        return """👨‍🏫 **Teaching: Variables**

Variables store data values in Python.

**Examples:**
```python
name = "Alice"
age = 25
height = 5.9
