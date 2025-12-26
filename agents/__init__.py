# agents/__init__.py - FINAL VERSION
from .assessment_agent import create_assessment_agent, assess_learning_profile
from .curriculum_agent import create_curriculum_agent, generate_python_curriculum
from .teaching_agent import create_teaching_agent, teach_python_concept
from .practice_agent import create_practice_agent, generate_python_exercise
from .progress_agent import create_progress_agent, track_learning_progress
from .coordinator import LearningCoachCoordinator

__all__ = [
    # Factory functions
    'create_assessment_agent',
    'create_curriculum_agent',
    'create_teaching_agent',
    'create_practice_agent',
    'create_progress_agent',
    
    # Direct functions (from tools)
    'assess_learning_profile',
    'generate_python_curriculum',
    'teach_python_concept',
    'generate_python_exercise',
    'track_learning_progress',
    
    # Coordinator
    'LearningCoachCoordinator'
]

print("✅ Agents package initialized with coordinator")