
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any
import vertexai

def assess_learning_profile(
    experience: str, 
    learning_style: str = "adaptive", 
    subject: str = "python"
) -> Dict[str, Any]:
    """Create personalized learning profile based on experience level"""
    
    experience_levels = {
        "beginner": {
            "score": 1, 
            "pace": "slow", 
            "depth": "fundamentals",
            "topics": ["variables", "data types", "basic operators", "if/else"]
        },
        "intermediate": {
            "score": 2, 
            "pace": "moderate", 
            "depth": "concepts",
            "topics": ["functions", "OOP", "file I/O", "error handling"]
        },
        "advanced": {
            "score": 3, 
            "pace": "fast", 
            "depth": "advanced_topics",
            "topics": ["decorators", "generators", "async/await", "metaclasses"]
        }
    }
    
    base_profile = experience_levels.get(
        experience.lower(), 
        experience_levels["beginner"]
    )
    
    return {
        "experience_level": experience,
        "learning_style": learning_style,
        "subject": subject,
        "recommended_pace": base_profile["pace"],
        "learning_depth": base_profile["depth"],
        "assessment_score": base_profile["score"],
        "recommended_topics": base_profile["topics"],
        "next_steps": f"Start with {subject} {experience} level: {', '.join(base_profile['topics'][:2])}"
    }

def analyze_student_input(student_input: str) -> Dict[str, Any]:
    """Analyze student's description to determine experience and learning style"""
    
    input_lower = student_input.lower()
    
    # Experience level detection
    if any(word in input_lower for word in [
        "expert", "advanced", "professional", "senior", 
        "years of", "experienced", "master", "proficient"
    ]):
        experience = "advanced"
    elif any(word in input_lower for word in [
        "intermediate", "some experience", "basic knowledge", 
        "familiar with", "understand basics", "coded before"
    ]):
        experience = "intermediate"
    else:
        experience = "beginner"
    
    # Learning style detection
    if any(word in input_lower for word in [
        "visual", "see", "watch", "diagram", "video", "youtube", "show me"
    ]):
        learning_style = "visual"
    elif any(word in input_lower for word in [
        "audio", "listen", "hear", "podcast", "explain", "tell me"
    ]):
        learning_style = "auditory"
    elif any(word in input_lower for word in [
        "hands-on", "practice", "code", "build", "project", 
        "exercise", "write", "do it myself"
    ]):
        learning_style = "kinesthetic"
    else:
        learning_style = "adaptive"
    
    # Detect knowledge gaps
    knowledge_gaps = []
    if "struggle" in input_lower or "difficult" in input_lower:
        knowledge_gaps.append("needs_review")
    if "never" in input_lower or "new" in input_lower:
        knowledge_gaps.append("complete_beginner")
    
    return {
        "detected_experience": experience,
        "detected_learning_style": learning_style,
        "knowledge_gaps": knowledge_gaps,
        "confidence": "high" if len(student_input) > 50 else "medium",
        "analysis_complete": True
    }

def assess_with_code_sample(code_sample: str) -> Dict[str, Any]:
    """Assess skill level based on code sample"""
    
    code_lower = code_sample.lower()
    
    # Check for advanced patterns
    advanced_indicators = [
        "def __", "async def", "yield", "@", "metaclass",
        "lambda", "with ", "try:", "except", "finally:"
    ]
    
    intermediate_indicators = [
        "def ", "class ", "import ", "return", 
        "self.", "[]", "{}", "for ", "while "
    ]
    
    beginner_indicators = [
        "print(", "input(", "if ", "else:", "=", "+", "-"
    ]
    
    # Count indicators
    advanced_count = sum(1 for ind in advanced_indicators if ind in code_lower)
    intermediate_count = sum(1 for ind in intermediate_indicators if ind in code_lower)
    beginner_count = sum(1 for ind in beginner_indicators if ind in code_lower)
    
    # Determine level
    if advanced_count >= 2:
        level = "advanced"
        confidence = "high"
    elif intermediate_count >= 3:
        level = "intermediate"
        confidence = "high"
    elif beginner_count >= 2:
        level = "beginner"
        confidence = "medium"
    else:
        level = "beginner"
        confidence = "low"
    
    return {
        "assessed_level": level,
        "confidence": confidence,
        "code_complexity": {
            "advanced_patterns": advanced_count,
            "intermediate_patterns": intermediate_count,
            "beginner_patterns": beginner_count
        },
        "has_code_sample": True
    }

# Create FunctionTools
profile_tool = FunctionTool(assess_learning_profile)
input_analysis_tool = FunctionTool(analyze_student_input)
code_assessment_tool = FunctionTool(assess_with_code_sample)

def create_assessment_agent():
    """Factory function to create the assessment agent"""
    return Agent(
        name="assessment_agent",
        model="gemini-1.5-flash-001",
        description="Evaluates student Python skill level through conversation analysis and code review",
        instruction="""
        You are an expert Python learning assessment specialist. Your role:
        
        1. **Analyze student descriptions** using analyze_student_input to detect:
           - Experience level (beginner/intermediate/advanced)
           - Preferred learning style (visual/auditory/kinesthetic/adaptive)
           - Knowledge gaps and areas of struggle
        
        2. **Review code samples** using assess_with_code_sample to:
           - Evaluate coding proficiency objectively
           - Identify skill level from code patterns
           - Provide confidence rating on assessment
        
        3. **Create learning profiles** using assess_learning_profile to:
           - Generate personalized learning plans
           - Set appropriate pace and depth
           - Recommend specific starting topics
        
        **Assessment Workflow:**
        - For new students without code: Use analyze_student_input
        - For students with code samples: Use assess_with_code_sample
        - Always conclude with assess_learning_profile for next steps
        
        Be encouraging, honest, and specific. Focus on growth potential, not just current level.
        Provide actionable recommendations tailored to their detected learning style.
        """,
        tools=[profile_tool, input_analysis_tool, code_assessment_tool]
    )

print("✅ Assessment Agent module loaded")
