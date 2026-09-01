# CV Analyzer & Roadmap Generator

An intelligent, agentic career development platform that bridges the gap between an engineer's current experience and their career goals. By leveraging RAG (Retrieval-Augmented Generation) and LangGraph workflows, this project transforms static CV data into actionable, personalized growth roadmaps.

## 🌟 Why I Built This
In an industry moving at light speed, maintaining a clear career trajectory is difficult. I built this tool to solve the "what's next?" problem. Rather than generic advice, this system uses a curated "Base Roadmap" of industry skills and maps them against an individual's unique background to identify high-impact learning opportunities.

## 🚀 How It Works
The platform operates as a coordinated multi-service ecosystem:

1.  **Ingestion & Analysis:** Users upload their CVs and define career objectives. The system ingests this data, extracts key skills, and stores them in a **Postgres** relational database.
2.  **Vector-Powered Matching:** Skills and experience are embedded and stored in a **Qdrant** vector database, allowing the system to perform semantic searches against a massive, structured library of professional development nodes (the "Base Roadmap").
3.  **Agentic Orchestration:** Using **LangGraph**, the backend orchestrates a multi-step reasoning process. It compares your current skill graph against the target roadmap to synthesize a personalized learning path, prioritizing gaps that will provide the highest career leverage.
4.  **Real-Time Feedback:** The **Streamlit** frontend provides a responsive, live-streamed interface that keeps users engaged while the agent processes their personalized path.

## 💡 How It Helps
- **Gap Analysis:** Instantly identifies missing technical competencies for specific job roles.
- **Personalized Prioritization:** Instead of learning "everything," the agent suggests exactly what you need to learn to reach your specific goals.
- **Dynamic Growth:** As you update your profile, the roadmap evolves with you, ensuring your growth plan is always relevant.

## 🛠️ Tech Stack
- **Backend:** FastAPI (async), LangGraph for stateful agent workflows.
- **Frontend:** Streamlit for rapid, data-centric UI development.
- **Data Layer:** Postgres (relational state), Qdrant (vector storage).
- **Orchestration:** Custom CLI built with `uv` for seamless local development, testing, and infrastructure management.
- **Deployment:** Cloud-native architecture designed for Railway, Neon Postgres, and Qdrant Cloud.
