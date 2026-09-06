# DesignMentor AI

An agentic AI system for learning Low-Level Design (LLD) and High-Level Design (HLD) — built with LangGraph, FastAPI, Next.js, PostgreSQL, and a Random Forest adaptive model.

---

## Architecture

```
User
 └─ Next.js Frontend (port 3000)
     └─ FastAPI Backend (port 8000)
         ├─ LangGraph Orchestrator
         │   ├─ Teacher Agent      — teaches concepts with examples
         │   ├─ Quiz Agent         — generates contextual questions
         │   ├─ Evaluation Agent   — scores answers, detects weak areas
         │   ├─ Mentor Agent       — Socratic conversation handler
         │   ├─ Planning Agent     — decides what to learn next
         │   ├─ Design Reviewer    — reviews LLD/HLD submissions
         │   └─ Interview Agent    — simulates real interviews
         ├─ Random Forest Model    — predicts mastery, detects weaknesses
         ├─ RAG (pgvector)         — knowledge base retrieval
         ├─ PostgreSQL             — all data + vector embeddings
         └─ Redis                  — session cache + rate limiting
```

---

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+
- An OpenAI API key

### 1. Clone and configure
```powershell
cd designmentor-ai
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY and a random SECRET_KEY
```

### 2. Run setup script
```powershell
.\scripts\setup.ps1
```

This will:
- Start PostgreSQL and Redis via Docker
- Create a Python venv and install dependencies
- Run database migrations
- Seed the curriculum (39 concepts across foundation → LLD → HLD)
- Train the Random Forest model from synthetic data
- Install frontend npm packages

### 3. Start development servers
```powershell
.\scripts\start_dev.ps1
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

### 4. Load the RAG knowledge base (optional but recommended)
```powershell
.\scripts\load_rag.ps1
```

### Or use Docker Compose for everything
```powershell
docker compose up
```

---

## Learning Path

```
Foundation (OOP)
  → Classes & Objects → Encapsulation → Inheritance
  → Polymorphism → Abstraction → Interfaces & Composition

LLD
  → SOLID (SRP, OCP, LSP, ISP, DIP)
  → Design Principles (DRY, KISS, DI)
  → Creational Patterns (Singleton, Factory, Builder)
  → Structural Patterns (Adapter, Decorator, Facade)
  → Behavioral Patterns (Strategy, Observer, Command, State)
  → LLD Problems (Parking Lot, Elevator, Splitwise)

HLD (unlocked after LLD mastery ≥ 75%)
  → System Design Basics → Networking → SQL → NoSQL
  → Caching → CAP Theorem → Horizontal Scaling
  → Message Queues → Load Balancing
  → HLD Problems (URL Shortener, Instagram, Rate Limiter)
```

---

## Key Features

| Feature | How it works |
|---|---|
| Adaptive learning | RF model predicts mastery from 21 features; re-routes to reteach if below threshold |
| Spaced repetition | SM-2 algorithm schedules reviews |
| LangGraph agents | 7-node graph with conditional routing based on student performance |
| RAG | Knowledge base chunked into pgvector; cosine similarity retrieval |
| RF retraining | Auto-retrains every 50 quiz completions using real student data |
| Interview mode | 15-turn Socratic interview with 6-dimension scorecard |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login → JWT |
| POST | `/api/learn/` | Send message to learning agent |
| POST | `/api/quiz/start` | Start quiz |
| POST | `/api/quiz/answer` | Submit answer |
| POST | `/api/quiz/complete/{id}` | Finish quiz, get result |
| POST | `/api/interview/start` | Start interview |
| POST | `/api/interview/message` | Send interview message |
| GET | `/api/progress/dashboard` | Dashboard data |
| GET | `/api/progress/concepts` | All concept progress |
| GET | `/api/progress/rf-insights/{slug}` | RF model predictions |
| POST | `/api/progress/design/submit` | Submit design for review |

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic
- **AI**: LangGraph, LangChain, OpenAI GPT-4o, text-embedding-ada-002
- **ML**: scikit-learn Random Forest (regressor + classifier), SM-2 spaced repetition
- **Database**: PostgreSQL 16 + pgvector (IVFFlat index)
- **Cache**: Redis
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Recharts, Zustand
- **Infra**: Docker Compose
