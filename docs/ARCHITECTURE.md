# OmniSynth Architecture Documentation

## System Architecture Diagram

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Port 80/443)                         │
│    Rate Limiting • SSL/TLS • WebSocket • Security Headers        │
└────────┬─────────────────────────────────────┬──────────────────┘
         │                                     │
         ▼                                     ▼
┌─────────────────────┐            ┌───────────────────────┐
│  Next.js 14 (3000)  │            │  FastAPI (8000)        │
│  ─────────────────  │            │  ──────────────────    │
│  Landing Page       │◄──API──────│  JWT Auth              │
│  Dashboard          │            │  Rate Limiting         │
│  OmniChat           │            │  9 API Modules         │
│  Research           │            │  CORS Middleware        │
│  Citations          │            │  Global Exc Handler    │
│  Plagiarism         │            └─────────┬─────────────┘
│  OCR Upload         │                      │
│  Analytics          │            ┌─────────▼─────────────┐
│  Collaboration      │            │  Multi-Agent System    │
│  Profile/Settings   │            │  ──────────────────    │
│  Admin Panel        │            │  LangGraph Orchestrator│
└─────────────────────┘            │  Research Agent (HyDE) │
                                   │  Citation Agent        │
                                   │  OCR Agent             │
                                   │  Plagiarism Agent      │
                                   │  Summarization Agent   │
                                   │  Drafting Agent        │
                                   │  Analytics Agent       │
                                   │  Recommendation Agent  │
                                   └─────────┬─────────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────┐
              │                              │                      │
              ▼                              ▼                      ▼
┌─────────────────────┐  ┌─────────────────────────┐  ┌───────────────────┐
│  PostgreSQL (5432)  │  │  Redis (6379)            │  │  FAISS Index      │
│  ───────────────    │  │  ──────────────          │  │  ─────────────    │
│  Users              │  │  Session Cache           │  │  Document Vecs    │
│  ResearchSessions   │  │  Celery Broker/Backend   │  │  384-dim MiniLM   │
│  Documents          │  │  Rate Limit Store        │  │  IndexFlatIP      │
│  Drafts             │  │  Real-time Pub/Sub       │  │  ID Mapping       │
│  Citations          │  └─────────────────────────┘  └───────────────────┘
│  PlagiarismReports  │
│  Workspaces         │              ┌──────────────────────────────────┐
│  AIConversations    │              │  External AI Services (Free)     │
│  Analytics          │              │  ─────────────────────────────   │
│  ActivityLogs       │              │  Groq API (LLM Inference)        │
└─────────────────────┘              │    • llama3-70b-8192 (primary)   │
                                     │    • mixtral-8x7b-32768 (2nd)    │
              ┌──────────────────┐   │    • llama3-8b-8192 (fast)      │
              │  Celery Workers  │   │  HuggingFace (Embeddings)        │
              │  ─────────────   │   │    • all-MiniLM-L6-v2 (local)   │
              │  document_tasks  │   └──────────────────────────────────┘
              │  ai_tasks        │
              └──────────────────┘
```

## Data Flow

### 1. AI Chat Request
```
User → POST /api/v1/chat/send
     → AgentOrchestrator.classify_intent()
     → Route to specialized agent
     → GroqService.generate() [Llama3-70B]
     → Save to AIConversation (PostgreSQL)
     → Return response
```

### 2. Document OCR + Indexing
```
User → POST /api/v1/ocr/upload
     → Save file to disk
     → OCRService.extract_from_file()
       → PyMuPDF (PDFs)
       → EasyOCR (Images)
       → pdfplumber (Tables)
       → pytesseract (Fallback)
     → GroqService.summarize_text()
     → EmbeddingService.add_documents()
       → SentenceTransformer.encode()
       → FAISS.add_with_ids()
     → Save to Document (PostgreSQL)
```

### 3. HyDE-Enhanced RAG Search
```
User query
     → HyDEService.enhance_query()
       → GroqService.generate_hyde_document()
       → EmbeddingService.encode(hyde_doc)
     → EmbeddingService.search(hyde_vector, top_k=5)
       → FAISS.search() → chunk IDs
     → Retrieve document chunks (PostgreSQL)
     → Build context + original query
     → GroqService.generate(context + query)
     → Return answer + sources
```

## Database Schema (Key Tables)

```sql
users            → id, email, username, hashed_password, role, status
user_profiles    → id, user_id, bio, institution, orcid_id, ...
research_sessions→ id, user_id, title, topic, status, tags
documents        → id, user_id, session_id, file_path, extracted_text, 
                   faiss_index_id, summary, keywords
drafts           → id, user_id, session_id, title, content, draft_type
citations        → id, user_id, style, formatted_text, bibtex
plagiarism_reports → id, user_id, overall_score, matches
ai_conversations → id, user_id, title, messages(JSON), model_used
collaboration_workspaces → id, owner_id, name, is_public
workspace_members → workspace_id, user_id, role
workspace_comments → id, workspace_id, user_id, content
analytics        → id, user_id, date, sessions, documents, ...
activity_logs    → id, user_id, action, resource_type, details
recommendations  → id, user_id, title, authors, relevance_score
```
