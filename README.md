# 🧠 Salesbrain Backend API

**Multi-Tenant B2B Sales Orchestrator**

## 🏗️ Architecture

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 16 (2 Instances)
  - `salesbrain_global_kb` - Shared company data
  - `salesbrain_tenant` - Customer-specific data with RLS
- **Auth:** JWT Bearer Tokens
- **Deployment:** Docker Compose (Dev), Elastio (Production)

---

## 📁 Project Structure

```
salesbrain-backend/
├── app/
│   ├── core/               # Core functionality
│   │   ├── config.py       # Environment variables
│   │   ├── db.py           # Database connection pools
│   │   └── security.py     # JWT authentication
│   │
│   ├── api/                # API endpoints
│   │   ├── health.py       # Health checks
│   │   ├── auth.py         # Authentication
│   │   └── __init__.py
│   │
│   ├── models/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── contact.py
│   │   └── __init__.py
│   │
│   ├── services/           # Business logic (future phases)
│   │   ├── orchestrator/   # Phase coordination
│   │   ├── research/       # Research engine
│   │   └── sync/           # Instantly/WeConnect sync
│   │
│   └── main.py             # FastAPI application
│
├── migrations/             # Database migrations (Alembic)
│   └── versions/
│
├── sql/                    # SQL schemas
│   ├── global_kb.sql       # Global-KB schema
│   └── tenant_db.sql       # Tenant-DB schema
│
├── tests/                  # Tests
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_db.py
│
├── docker-compose.yml      # Local development (2x PostgreSQL)
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🚀 Quick Start (Local Development)

### 1. Clone Repository

```bash
git clone https://github.com/Civandigi/salesbrain-backend.git
cd salesbrain-backend
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Databases

```bash
docker-compose up -d
```

### 4. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run Migrations

```bash
# Global-KB
psql -h localhost -p 5432 -U dev -d salesbrain_global_kb < sql/global_kb.sql

# Tenant-DB
psql -h localhost -p 5433 -U dev -d salesbrain_tenant < sql/tenant_db.sql
```

### 6. Start Backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Test Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "databases": {"global_kb": "connected", "tenant": "connected"}}
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## 📊 Database Schema

### Global-KB (Shared)
- `company` - Company data (UID-CH, domain, industry, etc.)
- `company_role_template` - Typical roles per company (NO personal data!)
- `research_evidence` - Provenance tracking
- `global_kb_access_log` - Audit log

### Tenant-DB (RLS-enabled)
- `organization` - Tenants
- `user` - Users (owner, admin, member, sb_admin, sb_operator)
- `contact` - Contact data (email, phone, lead score, journey phase)
- `campaign` - Campaigns (Instantly/WeConnect)
- `message` - Messages (sent/opened/replied)
- `event_log` - All interaction events

---

## 🔐 Authentication

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "organization_id": "uuid-here"
}

# Use token
curl http://localhost:8000/api/contacts \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 🌍 Environment Variables

See `.env.example` for all configuration options.

**Required:**
- `DATABASE_GLOBAL_URL` - PostgreSQL connection string (Global-KB)
- `DATABASE_TENANT_URL` - PostgreSQL connection string (Tenant-DB)
- `JWT_SECRET_KEY` - Secret for JWT signing
- `JWT_ALGORITHM` - Algorithm (default: HS256)

---

## 🔄 Development Phases

- ✅ **Phase 1:** Database Setup (Complete)
- ✅ **Phase 2:** Instantly.ai Integration (Complete)
- 🔄 **Phase 3:** Unified Inbox & Intelligence Layer (Current)
- ⚪ **Phase 4:** WeConnect Integration
- ⚪ **Phase 5:** Research Tool & Company Enrichment
- ⚪ **Phase 6:** Advanced Analytics & Reporting
- ⚪ **Phase 7:** Team Collaboration & Automation

See: [Project Roadmap](docs/PROJECT_ROADMAP.md) | [Instantly API Features](docs/INSTANTLY_API_FEATURES.md)

---

## 📝 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Create Pull Request

---

## 📞 Links

- **Frontend:** https://github.com/Civandigi/Salesbrain-UI-Beta
- **Onboarding:** https://github.com/Civandigi/salesbrain-onboarding
- **MCP Instantly:** https://github.com/Civandigi/mcp-instantly

---

**Salesbrain Team © 2025**
