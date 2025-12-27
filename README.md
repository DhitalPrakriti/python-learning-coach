🎓 Multi-Agent AI Learning Orchestrator (Vertex AI Ready)
A sophisticated, production-grade orchestration system built on the Google Cloud Vertex AI ecosystem. This project implements a Modular Agentic Workflow that manages personalized educational paths using high-concurrency Python logic and the Gemini 2.0 Flash model.

🏗️ Core Engineering & Architecture
1. Modular Agentic Framework
Instead of a monolithic AI prompt, this system is engineered with five Independent Agent Modules. Each module acts as a specialized micro-service with its own operational logic, temperature settings, and behavioral constraints:

Assessment Module: Executes diagnostic profiling to establish a user’s knowledge baseline.

Curriculum Designer: Architectures long-term, goal-oriented learning roadmaps.

Instructional Engine: Delivers concept explanations through real-world analogies and code synthesis.

Practice Sandbox: Generates algorithmic challenges with hint-based scaffolding (Productive Struggle).

Progress Monitor: Tracks achievement state and executes gamification logic through digital badges.

2. Intelligent Routing & Orchestration
The heart of the system is a Dynamic Orchestrator implemented in coordinator.py. It utilizes Heuristic Intent Analysis to route traffic between agent modules in real-time.

Contextual Persistence: Manages a shared state across all agents, allowing the "Curriculum" module to know exactly what the "Assessment" module discovered.

Intent Detection: Scans user input for semantic triggers to pivot the conversation between different agent specialties.

🛠️ Vertex AI Integration & Infrastructure
The system is built using the google-genai Unified SDK, making it fully compatible with enterprise cloud environments.

Platform Agnostic Client: Configured to interface with both Google AI Studio for rapid prototyping and Vertex AI for secure, IAM-protected production deployment.

Environment Parity: Engineered to handle the specific authentication protocols (API Key vs. OAuth2/Service Accounts) required by the aiplatform.googleapis.com service.

Concurrency Management: Utilizes a ThreadPoolExecutor and asyncio to manage high-traffic inference requests without blocking the Flask gateway.

📋 Technical Setup
Backend: Flask-based REST API designed for high-availability.

SDK: google-genai (utilizing the v1beta endpoint for Gemini 2.0 access).

Deployment: Docker-ready with built-in /health monitoring for Cloud Run or GKE integration

