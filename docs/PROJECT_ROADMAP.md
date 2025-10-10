# 🗺️ Salesbrain Backend - Project Roadmap

> **Version:** 1.0
> **Last Updated:** 2025-10-10
> **Status:** Phase 2 Complete ✅

---

## 📋 Overview

Salesbrain ist ein Multi-Tenant B2B Sales Orchestration Tool, das verschiedene Sales-Tools (Instantly.ai, WeConnect, Edibot) in einer intelligenten Plattform vereint.

### Architektur-Prinzipien

1. **Multi-Tenancy** - Komplette Isolation zwischen Kunden (RLS)
2. **API-First** - Alle Features via REST API
3. **Event-Driven** - Webhooks für Echtzeit-Updates
4. **Intelligence Layer** - KI-gestützte Automatisierung
5. **Scalability** - Shared Workspace (Beta) → Dedicated Workspace (Prod)

---

## ✅ Phase 1: Database Setup & Foundation (COMPLETE)

### Ziel
Robuste Multi-Tenant Datenbankarchitektur mit Row-Level Security

### Deliverables

#### 1.1 Dual Database Architecture ✅
- **Global-KB** (global_kb) - Shared Company Data
  - `company` - Firmenstammdaten (UID-CH, Domain, Branche)
  - `company_role_template` - Typische Rollen (KEINE persönlichen Daten)
  - `research_evidence` - Provenance Tracking
  - `global_kb_access_log` - Audit Log

- **Tenant-DB** (tenant_db) - Customer-specific Data
  - `organization` - Mandanten/Kunden
  - `user` - Benutzer (owner, admin, member, sb_admin, sb_operator)
  - `contact` - Kontaktdaten (leads, customers)
  - `campaign` - Kampagnen (Instantly/WeConnect)
  - `message` - Nachrichten (sent, opened, replied)
  - `event_log` - Interaktions-Events

#### 1.2 Row-Level Security (RLS) ✅
- Policies für alle Tenant-Tabellen
- Admin-Bypass für sb_admin/sb_operator
- Customer-Isolation via `app.current_org_id`

#### 1.3 Backend Setup ✅
- FastAPI Application (Python 3.11+)
- PostgreSQL Connection Pools (asyncpg)
- Health Check Endpoints
- Database Lifespan Management

#### 1.4 Authentication Grundlage ✅
- JWT Token Implementation
- User Roles (owner, admin, member, sb_admin, sb_operator)
- Configuration Management (Pydantic Settings)

### Git Commits
```
git log --oneline --grep="Phase 1"
- Complete Phase 1: Database Setup
  - 10 Tables (4 Global-KB, 6 Tenant-DB)
  - RLS Policies implemented
  - FastAPI backend running (Port 8001)
```

### Zeitraum
Start: 2025-01-15
Ende: 2025-04-10
Dauer: ~3 Monate

---

## ✅ Phase 2: Instantly.ai Integration (COMPLETE)

### Ziel
Vollständige Integration mit Instantly.ai API v2 für Campaign Management, Email Tracking und Webhook Processing

### Deliverables

#### 2.1 Database Extensions ✅
- **Phase 1.5 Migration** - Provider Connections Architecture
  - `provider_connection` - Workspace-Level Connections (shared/dedicated)
  - `email_account` - Individual Email Sending Accounts
  - Extended `campaign` - Workspace/Email Account References
  - Extended `message` - Email Account Tracking
  - RLS Policies mit Admin Bypass
  - Performance Indexes

**Migration File:** `sql/migration_phase1_5_provider_connections.sql`
**Documentation:** `docs/INSTANTLY_WORKSPACE_DESIGN.md`

#### 2.2 Instantly API Client ✅
**File:** `app/integrations/instantly/client.py`

Features:
- Bearer Token Authentication (API v2)
- Automatic Retry Logic (tenacity)
- Rate Limit Handling (429 errors)
- Comprehensive Error Handling (401, 429, 5xx)

Endpoints Implemented:
- `GET /workspaces/current` - Workspace Info
- `GET /campaigns` - List Campaigns (pagination)
- `GET /accounts` - List Email Accounts (pagination)
- `POST /leads` - Add Leads (bulk)
- `DELETE /leads/{id}` - Remove Lead

#### 2.3 Webhook System ✅
**File:** `app/integrations/instantly/webhooks.py`

- **17 Event Types Supported:**
  1. `email_sent` - Email successfully sent
  2. `email_opened` - Recipient opened email
  3. `email_clicked` - Link clicked
  4. `reply_received` - Reply received
  5. `email_bounced` - Bounce (soft/hard)
  6. `email_unsubscribed` - Unsubscribed
  7. `email_spam_report` - Marked as spam
  8. `lead_interested` - Lead shows interest
  9. `lead_not_interested` - Lead declined
  10. `lead_meeting_booked` - Meeting booked
  11. `lead_completed` - Lead workflow completed
  12. `lead_error` - Lead processing error
  13. `campaign_started` - Campaign activated
  14. `campaign_paused` - Campaign paused
  15. `campaign_completed` - Campaign finished
  16. `account_error` - Email account error
  17. `account_suspended` - Account suspended

- **Event Processing Pipeline:**
  1. Webhook received → Payload validation
  2. Campaign lookup → organization_id resolution
  3. Contact get/create → message record creation
  4. Stats update → event log entry
  5. Special handling (errors, meetings, lead status)

#### 2.4 Pydantic Schemas ✅
**File:** `app/integrations/instantly/schemas.py`

- 17 Webhook Event Models
- API Response Models (Workspace, Campaign, Account, Lead)
- Request/Response validation
- Type safety throughout

#### 2.5 Service Layer ✅
**Files:**
- `app/services/campaign_service.py` - Campaign CRUD + Stats
- `app/services/email_account_service.py` - Account Management + Counters
- `app/services/message_service.py` - Message Tracking + Search

Features:
- RLS-Aware Queries
- Admin Bypass (`SET LOCAL app.user_role = 'sb_admin'`)
- Customer Isolation (`SET LOCAL app.current_org_id`)
- Real-time Statistics
- Message Search Functionality

#### 2.6 REST API Endpoints ✅
**File:** `app/api/instantly.py`

**Admin Endpoints** (Cross-Organization):
- `GET /api/instantly/admin/campaigns` - All campaigns, all orgs
- `GET /api/instantly/admin/email-accounts` - All accounts, all orgs
- `GET /api/instantly/admin/campaign/{id}/stats` - Campaign stats
- `GET /api/instantly/admin/email-account/{id}/stats` - Account stats
- `POST /api/instantly/sync/workspace` - Manual sync

**Customer Endpoints** (RLS-Protected):
- `GET /api/instantly/campaigns` - Organization campaigns
- `GET /api/instantly/email-accounts` - Organization accounts
- `GET /api/instantly/campaign/{id}/messages` - Campaign messages
- `GET /api/instantly/stats` - Organization stats
- `GET /api/instantly/search/messages` - Message search

**Webhook Endpoint:**
- `POST /webhooks/instantly/webhook` - Receive all 17 event types

#### 2.7 Configuration ✅
**File:** `.env`

```bash
# Instantly.ai Integration
INSTANTLY_API_KEY=ZTRkMGRkMDEtODI0Zi00YzM2LWI2NWEtZDBlYWY4MTNhNDgxOmxCRk9JUmNleU5DRA==
INSTANTLY_WEBHOOK_URL=http://localhost:8001/webhooks/instantly/webhook
```

**File:** `app/core/config.py`
- Pydantic Settings for Instantly config
- Global settings instance

#### 2.8 Testing & Verification ✅
**Files:**
- `test_instantly_connection.py` - API Connection Test
- `explore_instantly_api.py` - API Explorer (v1 + v2)
- `fetch_instantly_data.py` - Workspace Data Export

**Test Results:**
- ✅ API Connection successful
- ✅ Workspace "Salesbrain" connected
- ✅ All 4 endpoints tested (workspace, campaigns, accounts, leads)

#### 2.9 Documentation ✅
**Files:**
- `docs/INSTANTLY_API_FEATURES.md` (English, 500+ lines)
  - Complete API Reference
  - All Endpoints documented
  - Use Cases & Best Practices

- `docs/INSTANTLY_FEATURES_ZUSAMMENFASSUNG_DE.md` (Deutsch, 600+ lines)
  - Strategische Empfehlungen
  - Feature-Vergleich Instantly vs Salesbrain
  - Konkrete Use Cases
  - Nächste Schritte

- `docs/INSTANTLY_WORKSPACE_DESIGN.md`
  - Multi-Workspace Architecture
  - Shared vs Dedicated Workspace
  - RLS Policy Design

- `docs/implementation/phase-2-instantly-integration.md` (760 lines)
  - Complete Implementation Guide
  - Testing Strategy
  - Deployment Notes

#### 2.10 Dependencies Added ✅
```txt
httpx==0.28.0        # Async HTTP client
tenacity==9.0.0      # Retry logic with exponential backoff
respx==0.21.1        # HTTP mocking for tests
```

### Architecture Highlights

#### Multi-Workspace Support
- **Shared Workspace (Beta):** `organization_id = NULL`
- **Dedicated Workspace (Prod):** `organization_id = UUID`
- Email account per organization tracking
- Campaign import with workspace association

#### Event Processing Pipeline
```
Webhook → Validation → Campaign Lookup → Contact Get/Create
→ Message Record → Stats Update → Event Log → Special Handling
```

#### API Design Principles
- Consistent response format: `{success: bool, data: ...}`
- Proper HTTP status codes
- Pagination support (limit/offset)
- Search and filtering capabilities

### Git Commits
```
git log --oneline --grep="Phase 2"
- Add Phase 1.5: Instantly Workspace & Email Account Architecture
- Implement Phase 2: Instantly.ai Integration (Backend Complete)
  - 12 new files (client, webhooks, schemas, services, API)
  - 17 webhook event types
  - Complete API v2 integration
  - Admin + Customer endpoints
  - Testing & Documentation
```

### Zeitraum
Start: 2025-04-15
Ende: 2025-10-10
Dauer: ~6 Monate

---

## ⏳ Phase 3: Unified Inbox & Intelligence Layer (PLANNED)

### Ziel
Echtzeit-Nachrichtenverarbeitung, KI-gestützte Lead-Qualifizierung und Unified Inbox

### Geplante Features

#### 3.1 Webhook Live Processing
- [ ] Ngrok/Public URL Setup
- [ ] Real-time webhook delivery testing
- [ ] Database event insertion verification
- [ ] Error handling & retry logic

#### 3.2 Campaign Import & Sync
- [ ] Import existing Instantly campaigns
- [ ] Sync email accounts
- [ ] Organization assignment
- [ ] Automatic periodic sync

#### 3.3 Unified Inbox
- [ ] Conversation threading (group by contact)
- [ ] All `reply_received` events in one view
- [ ] Email account filtering
- [ ] Campaign filtering
- [ ] Search & pagination

#### 3.4 Lead Scoring System
- [ ] Event-based scoring:
  - `email_opened` → +10 points
  - `email_clicked` → +25 points
  - `reply_received` → +50 points
  - `meeting_booked` → +100 points
- [ ] Hot Leads dashboard (top 10%)
- [ ] Score decay over time
- [ ] Custom scoring rules per organization

#### 3.5 Auto-Categorization (KI)
- [ ] `reply_received` → Text analysis
- [ ] Categories: Interested / Not Interested / Question / Meeting Request
- [ ] Auto-response suggestions
- [ ] Sentiment analysis

#### 3.6 Dashboard UI Components
- [ ] Campaign list (status, stats)
- [ ] Email account health monitoring
- [ ] Live message feed (WebSocket?)
- [ ] Analytics charts (D3.js/Chart.js)

### Dependencies (Estimated)
```txt
openai>=1.0.0           # KI-Analyse für Antworten
langchain>=0.1.0        # LLM Orchestration
websockets>=11.0        # Real-time updates
```

### Zeitraum (Geschätzt)
Start: 2025-10-15
Ende: 2025-12-31
Dauer: ~2.5 Monate

---

## ⏳ Phase 4: WeConnect Integration (PLANNED)

### Ziel
LinkedIn-Automatisierung via WeConnect für B2B Lead Generation

### Geplante Features

#### 4.1 WeConnect API Client
- [ ] Authentication & Session Management
- [ ] Campaign Management
- [ ] Contact Sync
- [ ] Message Tracking
- [ ] Webhook Processing

#### 4.2 LinkedIn Contact Enrichment
- [ ] Profile scraping (via WeConnect)
- [ ] Company data enrichment
- [ ] Job title/role detection
- [ ] Contact deduplication (Email vs LinkedIn)

#### 4.3 Multi-Channel Campaigns
- [ ] Instantly (Email) + WeConnect (LinkedIn) Kombination
- [ ] Cross-channel analytics
- [ ] Unified contact view (Email + LinkedIn)

### Zeitraum (Geschätzt)
Start: 2026-01-15
Ende: 2026-03-31
Dauer: ~2.5 Monate

---

## ⏳ Phase 5: Research Tool & Company Enrichment (PLANNED)

### Ziel
Automatische Firmen-Research via Edibot/Perplexity + Swiss Company Data

### Geplante Features

#### 5.1 Edibot Integration
- [ ] Research API Client
- [ ] Automated company research
- [ ] Evidence tracking (Provenance)
- [ ] Global-KB population

#### 5.2 Swiss Company Data (UID-CH)
- [ ] Handelsregister API
- [ ] Company validation
- [ ] Industry classification
- [ ] Company size detection

#### 5.3 Smart Lead Enrichment
- [ ] Auto-research on new contact
- [ ] Company profile auto-fill
- [ ] Contact role suggestion
- [ ] Personalization data for campaigns

### Zeitraum (Geschätzt)
Start: 2026-04-01
Ende: 2026-06-30
Dauer: ~3 Monate

---

## ⏳ Phase 6: Advanced Analytics & Reporting (PLANNED)

### Ziel
ROI-Tracking, Advanced Analytics, Custom Reports

### Geplante Features

#### 6.1 ROI Tracking
- [ ] Campaign cost tracking
- [ ] Conversion attribution
- [ ] Revenue per campaign
- [ ] Customer Lifetime Value (CLV)

#### 6.2 Advanced Analytics
- [ ] Multi-campaign dashboards
- [ ] Cross-channel attribution
- [ ] A/B testing framework
- [ ] Funnel analysis

#### 6.3 Custom Reporting
- [ ] Report builder (drag & drop)
- [ ] Scheduled reports (email)
- [ ] Export (PDF, Excel)
- [ ] White-label reports for customers

### Zeitraum (Geschätzt)
Start: 2026-07-01
Ende: 2026-09-30
Dauer: ~3 Monate

---

## ⏳ Phase 7: Team Collaboration & Automation (PLANNED)

### Ziel
Team-Features, Workflow-Automation, Integrationen

### Geplante Features

#### 7.1 Team Management
- [ ] User roles & permissions (erweitert)
- [ ] Lead assignment (round-robin, manual)
- [ ] Team-wide dashboards
- [ ] Activity tracking

#### 7.2 Workflow Automation
- [ ] Rule engine (if/then)
- [ ] Auto-assign leads based on criteria
- [ ] Auto-follow-ups
- [ ] Task automation

#### 7.3 Integrationen
- [ ] CRM Integration (Pipedrive, HubSpot)
- [ ] Slack notifications
- [ ] Zapier/Make.com
- [ ] Calendar integration (Calendly)

### Zeitraum (Geschätzt)
Start: 2026-10-01
Ende: 2026-12-31
Dauer: ~3 Monate

---

## 📊 Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.104.1
- **ORM:** Direct SQL (asyncpg)
- **Validation:** Pydantic 2.x
- **Testing:** pytest + respx

### Database
- **DBMS:** PostgreSQL 17
- **Instances:** 2 (global_kb + tenant_db)
- **Features:** RLS, JSONB, Full-Text Search
- **Hosting:** Digital Ocean Managed PostgreSQL (Prod)

### Infrastructure
- **Hosting:** Digital Ocean App Platform
- **CI/CD:** GitHub Actions
- **Monitoring:** (TODO - Phase 6)
- **Logging:** (TODO - Phase 6)

### Integrations
- **Instantly.ai:** Email Campaigns (API v2)
- **WeConnect:** LinkedIn Automation (Planned - Phase 4)
- **Edibot/Perplexity:** Research (Planned - Phase 5)

---

## 🎯 Success Metrics

### Phase 1-2 (Current)
- ✅ Database uptime: 99.9%
- ✅ API response time: <200ms
- ✅ All tests passing
- ✅ Documentation complete

### Phase 3 (Target)
- [ ] Real-time webhook delivery: <1s
- [ ] Lead scoring accuracy: >80%
- [ ] Auto-categorization accuracy: >85%
- [ ] Inbox load time: <500ms

### Phase 4-7 (Target)
- [ ] Multi-channel campaign ROI: >150%
- [ ] Customer satisfaction: >90%
- [ ] Platform uptime: 99.95%
- [ ] Support ticket resolution: <24h

---

## 📝 Open TODOs (Cross-Phase)

### High Priority
- [ ] Unit Tests für Phase 2 (Services, Webhooks)
- [ ] Integration Tests (Mock Instantly API)
- [ ] API Authentication (currently disabled for testing)
- [ ] Rate Limiting (Instantly API)
- [ ] Error Logging & Monitoring

### Medium Priority
- [ ] Database Backup Strategy
- [ ] Migration Rollback Testing
- [ ] Load Testing (1000+ concurrent users)
- [ ] Security Audit

### Low Priority
- [ ] API Versioning Strategy
- [ ] GraphQL API (Alternative zu REST?)
- [ ] Admin Panel (separate UI?)

---

## 📚 Documentation Index

### Setup & Configuration
- `README.md` - Quick Start Guide
- `.env.example` - Environment Variables Template

### Architecture
- `docs/PROJECT_ROADMAP.md` - This file
- `docs/INSTANTLY_WORKSPACE_DESIGN.md` - Multi-Workspace Architecture
- `docs/DATABASE_SCHEMA.md` - (TODO)

### API Documentation
- `docs/INSTANTLY_API_FEATURES.md` - Instantly API Reference (EN)
- `docs/INSTANTLY_FEATURES_ZUSAMMENFASSUNG_DE.md` - Feature Summary (DE)
- `/docs` - Swagger UI (when running)
- `/redoc` - ReDoc (when running)

### Implementation Guides
- `docs/implementation/phase-1-database-setup.md` - (TODO)
- `docs/implementation/phase-2-instantly-integration.md` - Complete ✅

### Testing
- `test_instantly_connection.py` - API Connection Test
- `explore_instantly_api.py` - API Explorer (v1 + v2)
- `fetch_instantly_data.py` - Data Export

---

## 🔗 Related Repositories

- **Frontend:** [Salesbrain-UI-Beta](https://github.com/Civandigi/Salesbrain-UI-Beta)
- **Onboarding:** [salesbrain-onboarding](https://github.com/Civandigi/salesbrain-onboarding)
- **MCP Instantly:** [mcp-instantly](https://github.com/Civandigi/mcp-instantly)

---

## 👥 Team

- **Product Owner:** Ivan
- **Backend Development:** Claude (AI Assistant)
- **Frontend Development:** (Planned)

---

## 📅 Timeline Overview

```
2025-01  ████████ Phase 1: Database Setup (Complete)
2025-04  ████████████████ Phase 2: Instantly Integration (Complete)
2025-10  ████ Phase 3: Intelligence Layer (Planned)
2026-01  ████ Phase 4: WeConnect (Planned)
2026-04  ████ Phase 5: Research Tool (Planned)
2026-07  ████ Phase 6: Analytics (Planned)
2026-10  ████ Phase 7: Automation (Planned)
```

---

**Last Updated:** 2025-10-10
**Status:** Phase 2 Complete ✅ → Phase 3 Planning
**Version:** 1.0

---

**Salesbrain © 2025**
