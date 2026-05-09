# 🧠 OmniSynth — Enterprise AI Research & Productivity Platform

<div align="center">

![OmniSynth](https://img.shields.io/badge/OmniSynth-v1.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)

**OmniSynth is a fully open-source, enterprise-grade AI research & productivity automation platform powered entirely by free models via Groq (Llama-3-70B, Mixtral-8x7B) and HuggingFace.**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [API Docs](#api-documentation) • [Deployment](#deployment)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent AI** | 9 specialized LangGraph agents (research, OCR, citation, drafting, summarization, plagiarism, recommendation, productivity, general) |
| 🔍 **HyDE-Enhanced RAG** | Hypothetical Document Embedding for superior semantic retrieval with FAISS + reranking |
| 📄 **Multi-Engine OCR** | PyMuPDF + EasyOCR + pytesseract + pdfplumber pipeline for PDFs, images, DOCX |
| 🔬 **Semantic Search** | FAISS vector store + sentence-transformers (all-MiniLM-L6-v2) embeddings |
| ✍️ **AI Content Drafting** | Abstract, introduction, literature review, methodology, conclusion generation |
| 📖 **Citation Generator** | APA, MLA, IEEE, Chicago, Harvard, Vancouver, ACS + BibTeX + DOI metadata fetch |
| 🛡️ **Plagiarism Detection** | Semantic + fingerprinting (Winnowing) + n-gram + edit-distance analysis |
| 👥 **Collaboration Workspaces** | Real-time WebSocket workspaces with presence indicators and comments |
| 📊 **Productivity Analytics** | AI-powered research progress tracking, activity heatmaps, insights |
| 🧠 **Long-term Memory** | PostgreSQL + FAISS semantic memory for persistent context |
| 💡 **Recommendation Engine** | AI-powered paper and research recommendations |
| 🔐 **Enterprise Auth** | JWT + refresh tokens, RBAC (admin/researcher/collaborator/viewer) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NGINX (Reverse Proxy / SSL)                        │
│              Rate limiting • Security headers • WebSocket             │
└────────────────────┬───────────────────────┬───────────────────────┘
                     │                        │
         ┌───────────▼──────────┐ ┌──────────▼──────────┐
         │   Next.js 14 (SSR)   │ │  FastAPI + Uvicorn   │
         │  TypeScript + Tailwind│ │  Python 3.11 Backend │
         │  Framer Motion + RQ  │ │  Async SQLAlchemy    │
         └──────────────────────┘ └──────────┬──────────┘
                                             │
         ┌───────────────────────────────────┼────────────────────┐
         │                                   │                    │
┌────────▼──────────┐  ┌────────────────────▼──┐  ┌────────────▼────────────┐
│  LangGraph        │  │   Data Layer           │  │  AI Services            │
│  Multi-Agent      │  │   PostgreSQL (primary) │  │  Groq API (LLM)         │
│  Orchestrator     │  │   Redis (cache/queue)  │  │  Llama3-70B (primary)   │
│  9 Agents         │  │   FAISS (vectors)      │  │  Mixtral-8x7B (fallback)│
│  LangChain RAG    │  │   Celery (tasks)       │  │  HuggingFace Embeddings │
└───────────────────┘  └───────────────────────┘  └─────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript, TailwindCSS, Framer Motion, Recharts |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy (async), Alembic, Pydantic v2 |
| **AI/ML** | LangChain, LangGraph, Groq SDK, HuggingFace Transformers, sentence-transformers |
| **LLM Models** | Llama3-70B-8192 (primary), Mixtral-8x7B-32768 (secondary), Llama3-8B (fast) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (384-dim, free) |
| **OCR** | PyMuPDF, EasyOCR, pytesseract, pdfplumber (multi-engine) |
| **Vector DB** | FAISS (IndexFlatIP with IDMap) |
| **Database** | PostgreSQL 16 (primary), Redis 7 (cache + Celery broker) |
| **Task Queue** | Celery 5 with Redis broker (document processing, AI tasks) |
| **Infrastructure** | Docker Compose, Nginx, GitHub Actions CI/CD |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API key (free at [groq.com](https://groq.com))
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/test.git
cd test
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add:
# GROQ_API_KEY=your_groq_api_key_here
```

### 3. Launch with Docker

```bash
docker-compose up -d --build
```

### 4. Initialize Database

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the Platform

| Service | URL |
|---|---|
| 🌐 Frontend | http://localhost |
| 📡 Backend API | http://localhost/api/v1 |
| 📖 API Docs | http://localhost/docs |
| 📊 ReDoc | http://localhost/redoc |

**Default Admin Account:**
- Email: `admin@omnisynth.ai`
- Password: `Admin@123456`

> ⚠️ Change the admin password immediately after first login!

---

## 📁 Project Structure

```
omnisynth/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph multi-agent system
│   │   │   ├── orchestrator.py      # Intent routing & agent coordination
│   │   │   └── research_agent.py    # HyDE-RAG research agent
│   │   ├── api/v1/endpoints/ # FastAPI route handlers
│   │   │   ├── auth.py              # JWT authentication
│   │   │   ├── chat.py              # AI chat + streaming
│   │   │   ├── research.py          # Sessions, docs, drafts
│   │   │   ├── citations.py         # Citation generation
│   │   │   ├── plagiarism.py        # Plagiarism detection
│   │   │   ├── ocr.py               # Document OCR
│   │   │   ├── analytics.py         # Productivity analytics
│   │   │   ├── collaboration.py     # Workspaces + WebSocket
│   │   │   └── admin.py             # Admin panel
│   │   ├── core/            # Database, config, Redis, security
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic services
│   │   │   ├── groq_service.py      # Groq LLM wrapper
│   │   │   ├── embedding_service.py # FAISS + sentence-transformers
│   │   │   ├── hyde_service.py      # HyDE retrieval
│   │   │   ├── ocr_service.py       # Multi-engine OCR
│   │   │   ├── citation_service.py  # Citation formatting
│   │   │   └── plagiarism_service.py # Plagiarism analysis
│   │   └── tasks/           # Celery async tasks
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 App Router pages
│   │   │   ├── page.tsx             # Landing page
│   │   │   ├── dashboard/           # Main dashboard
│   │   │   ├── chat/                # OmniChat AI interface
│   │   │   ├── research/            # Research sessions
│   │   │   ├── citations/           # Citation generator
│   │   │   ├── plagiarism/          # Plagiarism checker
│   │   │   ├── ocr/                 # Document OCR upload
│   │   │   ├── analytics/           # Productivity analytics
│   │   │   ├── collaboration/       # Workspaces
│   │   │   ├── profile/             # User profile
│   │   │   ├── settings/            # App settings
│   │   │   ├── admin/               # Admin panel
│   │   │   └── auth/                # Login/Register
│   │   ├── components/      # Reusable React components
│   │   ├── lib/             # API client, auth utilities
│   │   ├── store/           # Zustand state management
│   │   ├── hooks/           # Custom React hooks
│   │   └── types/           # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf           # Nginx reverse proxy config
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions pipeline
├── docker-compose.yml
└── README.md
```

---

## 🔌 API Documentation

### Authentication Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login & get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user profile |
| PUT | `/api/v1/auth/me` | Update user info |
| PUT | `/api/v1/auth/me/profile` | Update research profile |
| PUT | `/api/v1/auth/change-password` | Change password |
| POST | `/api/v1/auth/logout` | Logout |

### Research Endpoints

| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/v1/research/sessions` | List/Create sessions |
| GET/PUT/DELETE | `/api/v1/research/sessions/{id}` | Session CRUD |
| POST | `/api/v1/research/query` | HyDE-RAG AI query |
| POST | `/api/v1/research/generate-content` | AI content generation |
| POST | `/api/v1/research/sessions/{id}/documents` | Upload document |
| GET | `/api/v1/research/sessions/{id}/drafts` | List drafts |

### AI Chat Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/chat/send` | Send message to AI |
| GET | `/api/v1/chat/stream` | Stream AI response (SSE) |
| GET | `/api/v1/chat/conversations` | List conversations |
| GET | `/api/v1/chat/agents` | List available agents |

### Citation Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/citations/generate` | Generate citation |
| POST | `/api/v1/citations/generate-all` | Generate all styles |
| POST | `/api/v1/citations/extract-from-text` | Extract citations from text |
| GET | `/api/v1/citations/styles` | List supported styles |

### OCR Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/ocr/upload` | Upload & extract text |
| POST | `/api/v1/ocr/extract-text` | Extract text only |
| GET | `/api/v1/ocr/documents` | List documents |
| GET | `/api/v1/ocr/documents/{id}` | Get document |

### Other Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/plagiarism/check` | Check text for plagiarism |
| GET | `/api/v1/analytics/dashboard` | Dashboard analytics |
| GET | `/api/v1/analytics/productivity` | Productivity metrics |
| GET/POST | `/api/v1/collaboration/workspaces` | Workspace management |
| WS | `/api/v1/collaboration/ws/{id}` | Real-time WebSocket |
| GET | `/api/v1/admin/users` | Admin: list users |
| GET | `/api/v1/admin/stats` | System statistics |

---

## 🐳 Docker Services

| Service | Port | Description |
|---|---|---|
| nginx | 80, 443 | Reverse proxy + SSL termination |
| frontend | 3000 | Next.js 14 application |
| backend | 8000 | FastAPI application |
| celery_worker | - | Async task processor |
| postgres | 5432 | Primary database |
| redis | 6379 | Cache + Celery broker |

---

## ⚙️ Environment Variables

```bash
# AI Models (Groq - free)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_PRIMARY=llama3-70b-8192
GROQ_MODEL_SECONDARY=mixtral-8x7b-32768
GROQ_MODEL_FAST=llama3-8b-8192

# Database
DATABASE_URL=postgresql+asyncpg://omnisynth:omnisynth_pass@postgres:5432/omnisynth_db

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Admin
FIRST_SUPERUSER_EMAIL=admin@omnisynth.ai
FIRST_SUPERUSER_PASSWORD=Admin@123456
```

---

## 🔄 CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci-cd.yml`) runs:

1. **Backend Tests** — pytest with PostgreSQL + Redis services
2. **Frontend Build** — TypeScript check, lint, Next.js build
3. **Docker Build** — Multi-stage builds for both services
4. **Security Scan** — Trivy CVE scan + Gitleaks secrets check
5. **Deploy** — Triggered on `main` branch push

---

## 🧪 Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

# Database
docker run -d -e POSTGRES_DB=omnisynth_db -e POSTGRES_USER=omnisynth \
  -e POSTGRES_PASSWORD=omnisynth_pass -p 5432:5432 postgres:16-alpine

# Redis
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 📈 Performance

- **LLM Inference**: ~200ms avg via Groq (fastest inference in the world)
- **Embedding**: 384-dim MiniLM, ~50ms per document chunk
- **OCR**: 1-3 seconds per page (multi-engine)
- **FAISS Search**: Sub-millisecond vector similarity search
- **API Response**: < 100ms for non-AI endpoints

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ using Groq + Llama3-70B + HuggingFace + LangChain + LangGraph
</div>
