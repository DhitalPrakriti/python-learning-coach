# diagnostics_import_check.py
import os
import sys
sys.path.insert(0, os.getcwd()) 

print("FIXED COORDINATOR TEST")
print("=" * 60)

# Get current directory
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")

# Check if we're in the right place
if not current_dir.endswith('python_learning_coach_deploy'):
    print("WARNING: You might be in the wrong directory")
    print("   Run: cd D:\\python_learning_coach_deploy")

# Add the PARENT directory to Python path
# This allows: from agents.coordinator import ...
sys.path.insert(0, current_dir)

print(f"\nPython path now includes: {current_dir}")

# List what's in agents folder
agents_path = os.path.join(current_dir, 'agents')
print(f"\nContents of agents folder:")
if os.path.exists(agents_path):
    for file in os.listdir(agents_path):
        if file.endswith('.py'):
            print(f"  - {file}")
else:
    print("ERROR: agents folder not found!")

# Now try the import
print("\nTRYING IMPORTS...")

# Method 1: Absolute import (preferred)
print("\n1. Absolute import (from agents.coordinator):")
try:
    from agents.coordinator import LearningCoachCoordinator
    print("SUCCESS: from agents.coordinator import LearningCoachCoordinator")
    
    # Test creating instance
    print("\n2. Testing coordinator creation:")
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"SUCCESS: API key found (...{api_key[-6:]})")
        
        try:
            coord = LearningCoachCoordinator()
            print("SUCCESS: Coordinator instance created!")
            
            # Test agent initialization
            if hasattr(coord, 'initialize_agents'):
                result = coord.initialize_agents()
                print(f"SUCCESS: Agent initialization: {result}")
                
                if hasattr(coord, 'agents'):
                    print(f"SUCCESS: Agents loaded: {list(coord.agents.keys())}")
            else:
                print("ERROR: No initialize_agents method")
                
        except Exception as e:
            print(f"ERROR: Coordinator creation failed: {e}")
    else:
        print("ERROR: No API key in .env")
        
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    
    # Method 2: Try importing the module first
    print("\n3. Trying to import agents module first:")
    try:
        import agents
        print("SUCCESS: Imported agents package")
        
        # Now try to access coordinator
        if hasattr(agents, 'coordinator'):
            print("SUCCESS: agents.coordinator exists")
        else:
            print("ERROR: agents.coordinator not found")
    except ImportError as e2:
        print(f"ERROR: Could not import agents: {e2}")

print("\n" + "=" * 60)
print("If imports fail, check:")
print("1. You're in D:\\python_learning_coach_deploy")
print("2. Run this command: cd D:\\python_learning_coach_deploy")
print("3. agents/ folder contains coordinator.py")
