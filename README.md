# 💼 Financial Document Management API

A production-ready **FastAPI** application for managing financial documents with **AI-powered semantic search** using RAG (Retrieval-Augmented Generation).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT / SWAGGER UI                       │
│                    http://localhost:8000/docs                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP Requests
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FASTAPI APP                              │
│                                                                  │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐  │
│   │  /auth      │  │  /documents  │  │  /roles  │  │  /rag  │  │
│   │  register   │  │  upload      │  │  create  │  │  index │  │
│   │  login      │  │  list        │  │  assign  │  │  search│  │
│   └──────┬──────┘  └──────┬───────┘  └────┬─────┘  └───┬────┘  │
│          │                │               │             │        │
│   ┌──────▼────────────────▼───────────────▼─────────┐  │        │
│   │              JWT Auth + RBAC Middleware          │  │        │
│   │         (Admin / Analyst / Auditor / Client)     │  │        │
│   └──────────────────────────┬───────────────────────┘  │        │
│                              │                           │        │
└──────────────────────────────┼───────────────────────────┼───────┘
                               │                           │
               ┌───────────────▼──────┐    ┌──────────────▼──────────┐
               │    PostgreSQL DB      │    │      RAG Pipeline        │
               │                      │    │                          │
               │  • users             │    │  Document                │
               │  • roles             │    │      ↓                   │
               │  • permissions       │    │  Text Extraction         │
               │  • documents         │    │  (PDF/DOCX/TXT)          │
               │                      │    │      ↓                   │
               └──────────────────────┘    │  Chunking (500 words)    │
                                           │      ↓                   │
                                           │  Embeddings              │
                                           │  (all-MiniLM-L6-v2)      │
                                           │      ↓                   │
                                           │  Qdrant Vector DB        │
                                           │      ↓                   │
                                           │  Vector Search (Top 20)  │
                                           │      ↓                   │
                                           │  CrossEncoder Reranking  │
                                           │      ↓                   │
                                           │  Top 5 Results           │
                                           └──────────────────────────┘
```

---

## 📁 Project Structure

```
fin_mgmt/
│
├── app/
│   ├── main.py                    ← FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          ← Combines all routers
│   │       └── endpoints/
│   │           ├── auth.py        ← /auth/register, /auth/login
│   │           ├── roles.py       ← /roles/create, /users/assign-role
│   │           ├── documents.py   ← /documents CRUD + search
│   │           └── rag.py         ← /rag/index, /rag/search, /rag/context
│   ├── core/
│   │   ├── config.py              ← Environment settings (.env)
│   │   └── security.py           ← JWT tokens + bcrypt + RBAC
│   ├── db/
│   │   └── session.py            ← SQLAlchemy engine + session
│   ├── models/
│   │   └── user.py               ← User, Role, Permission, Document ORM
│   ├── schemas/
│   │   └── schemas.py            ← Pydantic request/response models
│   └── services/
│       └── rag_service.py        ← Embeddings + Qdrant + Reranker
│
├── alembic/                       ← Database migrations
│   └── versions/
│       └── 0001_initial.py       ← Pre-built initial migration
│
├── .env                           ← Environment variables
├── alembic.ini                    ← Alembic config
├── docker-compose.yml             ← PostgreSQL + Qdrant containers
├── requirements.txt               ← Python dependencies
└── seed.py                        ← Creates default roles + admin user
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Vector DB | Qdrant |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Reranker | CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| Containers | Docker + Docker Compose |

---

## 🔐 Role-Based Access Control (RBAC)

| Role | Permissions |
|------|------------|
| Admin | Full access (everything) |
| Analyst | upload_document, edit_document, view_document, delete_document |
| Auditor | view_document, review_document |
| Client | view_document |

---

## 🚀 How to Run — Complete Setup Guide

### Prerequisites
- Python 3.11+
- Docker Desktop
- Git

---

### Step 1 — Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/financial-document-api.git
cd financial-document-api
```

---

### Step 2 — Create Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

---

### Step 3 — Install Dependencies
```powershell
pip install -r requirements.txt
```

> ⚠️ **Windows users:** If you get a torch DLL error, install Visual C++ Redistributable first:
> 👉 https://aka.ms/vs/17/release/vc_redist.x64.exe
> Then reinstall torch:
> ```powershell
> pip install torch==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu
> ```

---

### Step 4 — Configure Environment

Copy and edit the `.env` file:
```env
APP_NAME=FinancialDocAPI
SECRET_KEY=mysupersecretkey123changethis
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_URL=postgresql://postgres:password@localhost:5432/financial_docs

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=financial_documents

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=20
```

---

### Step 5 — Start Docker Containers
```powershell
docker-compose up -d
```

Verify both are running:
```powershell
docker-compose ps
```
✅ You should see `postgres` and `qdrant` both **running**

---

### Step 6 — Run Database Migrations
```powershell
alembic upgrade head
```

✅ Expected:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial
```

If you get a password error:
```powershell
docker exec -it financial_docs-postgres-1 psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'password';"
alembic upgrade head
```

---

### Step 7 — Seed Default Roles and Admin User
```powershell
python seed.py
```

✅ Expected:
```
=============================================
  Seed complete!
  Admin login → username: admin
              → password: admin123
=============================================
```

---

### Step 8 — Start the Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Expected:
```
INFO: ✅ Database tables verified / created.
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

---

### Step 9 — Open API Docs
👉 **http://localhost:8000/docs**

---

## 📋 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register new user |
| POST | /auth/login | No | Login → get JWT token |
| POST | /documents/upload | Analyst/Admin | Upload document |
| GET | /documents | Any | List all documents |
| GET | /documents/search | Any | Search by metadata |
| GET | /documents/{id} | Any | Get document by ID |
| DELETE | /documents/{id} | Analyst/Admin | Delete document |
| POST | /roles/create | Admin | Create a role |
| POST | /users/assign-role | Admin | Assign role to user |
| GET | /users/{id}/roles | Any | Get user roles |
| GET | /users/{id}/permissions | Any | Get user permissions |
| POST | /rag/index-document | Analyst/Admin | Index document for AI |
| DELETE | /rag/remove-document/{id} | Analyst/Admin | Remove embeddings |
| POST | /rag/search | Any | Semantic AI search |
| GET | /rag/context/{id} | Any | Get document chunks |
| GET | /health | No | Health check |
| GET | /db-check | No | DB connection check |

---

## 🧪 Quick API Test

### 1. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123"
```

### 2. Upload Document
```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Q4 Report" \
  -F "company_name=Acme Corp" \
  -F "document_type=report" \
  -F "file=@report.pdf"
```

### 3. Semantic Search
```bash
curl -X POST http://localhost:8000/rag/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "financial risk high debt ratio", "top_k": 5}'
```

---

## ⚠️ Common Errors and Fixes

| Error | Fix |
|-------|-----|
| `password authentication failed` | Run `docker-compose down -v && docker-compose up -d` |
| `torch DLL error` | Install Visual C++: https://aka.ms/vs/17/release/vc_redist.x64.exe |
| `No module named app` | Make sure you are in the `fin_mgmt` folder |
| `401 Unauthorized` | Re-login — JWT token expired (60 min limit) |
| `bcrypt error` | Run `pip install bcrypt==4.0.1` |
| Port 5432 in use | Stop local PostgreSQL or change port in docker-compose.yml |

---

## 🔁 Every Time You Restart PC

```powershell
cd fin_mgmt
venv\Scripts\activate
docker-compose up -d
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open: **http://localhost:8000/docs**

---

## 📄 License
MIT License
