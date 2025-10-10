# 🎯 SALESBRAIN - MASTER PLAN
## SINGLE SOURCE OF TRUTH

> **WICHTIG:** Dies ist die EINZIGE Planungsdatei für das Salesbrain-Projekt.
> **Letzte Aktualisierung:** 2025-10-10
> **Version:** 2.0
> **Status:** Phase 2 Complete ✅ → Phase 3 Current

---

## ⚠️ PROJEKTREGELN

### 1. SINGLE SOURCE OF TRUTH
- **NUR DIESE DATEI** enthält die Projekt-Planung
- **KEINE** anderen Planungsdateien erstellen
- **KEINE** duplizierten Roadmaps/Plans
- **IMMER** diese Datei aktualisieren, nie neue erstellen

### 2. AI-CONTEXT PROTECTION
- Diese Datei verhindert Kontext-Verwirrung für AI
- Alle Änderungen NUR hier dokumentieren
- Redundante Informationen vermeiden
- Klare, eindeutige Spezifikationen

---

## 📊 PROJEKT-ÜBERSICHT

### Vision
Salesbrain ist ein **Multi-Tenant B2B Sales Orchestration Tool**, das verschiedene Sales-Tools (Instantly.ai, WeConnect, Edibot) in einer intelligenten Plattform vereint.

### Kern-Prinzipien
1. **Multi-Tenancy** - Komplette Customer-Isolation (RLS)
2. **API-First** - Alle Features via REST API
3. **Event-Driven** - Webhooks für Echtzeit-Updates
4. **Intelligence Layer** - KI-gestützte Automatisierung
5. **Unified Experience** - Ein Dashboard für alles

---

## ✅ AKTUELLE STATUS (2025-10-10)

### Phase 1: Database Setup ✅ COMPLETE
- **Dauer:** Januar - April 2025 (3 Monate)
- **Status:** 100% Complete
- **Deliverables:**
  - Dual Database Architecture (global_kb + tenant_db)
  - 10 Tables mit komplettem Schema
  - Row-Level Security (RLS) auf allen Tenant-Tabellen
  - Connection Pools & Health Checks
  - FastAPI Backend läuft auf Port 8001

### Phase 2: Instantly Integration ✅ COMPLETE
- **Dauer:** April - Oktober 2025 (6 Monate)
- **Status:** 100% Complete
- **Deliverables:**
  - ✅ Instantly API Client (v2) mit Retry-Logic
  - ✅ 17 Webhook Event Types implementiert
  - ✅ Database Extensions (provider_connection, email_account)
  - ✅ Service Layer (Campaign, Email Account, Message)
  - ✅ 12 REST API Endpoints (Admin + Customer)
  - ✅ Complete Documentation (3,250+ lines)
  - ✅ Testing Scripts (3 files)
  - ✅ Connection Tests passing

**Statistiken:**
- 20 Dateien erstellt (12 Python + 3 Tests + 5 Docs)
- 3,500+ Zeilen Code
- 3,250+ Zeilen Dokumentation
- 100% Backend funktional

---

## 🎯 PHASE 3: ADMIN PORTAL & UNIFIED INBOX (CURRENT)

### Ziele
1. Admin-Portal Frontend komplett aufbauen
2. Backend-APIs mit UI verbinden
3. Unified Inbox für alle Nachrichten
4. Lead-Scoring & KI-Kategorisierung
5. Real-time Updates via Webhooks

### 🚨 KRITISCHE ERKENNTNISSE (aus Admin Portal Analysis)

**Frontend Status:** Nur 10% complete
- ✅ Navigation structure vorhanden
- ✅ AI-powered "Brain" search (Deutsch)
- ✅ General search bar
- ✅ Notification system (F8 shortcut)
- ❌ **ALLE Daten-Views fehlen!**

**Backend Status:** 70% complete
- ✅ Campaign APIs (admin + customer)
- ✅ Email Account APIs
- ✅ Message Search API
- ✅ Organization Stats API
- ✅ Event Logging System
- ⚠️ Authentication disabled (testing)

**Critical Gap:**
**Backend hat funktionale APIs, aber KEINE UI zum Anzeigen der Daten!**

### ADMIN PORTAL - MUST-HAVE FEATURES

#### 1. WEBHOOK LOGS & MONITORING (KRITISCH!) 📊
**Was du gesagt hast:** "Ich will unbedingt die Logs sehen auf diesen ganzen Webhooks hin und her"

**Implementierung:**
```
Admin Portal → Webhook Logs Tab
├── Real-time Log Feed
│   ├── Event Type (email_sent, reply_received, etc.)
│   ├── Timestamp
│   ├── Campaign Name
│   ├── Contact Email
│   ├── Status (success/failed)
│   └── Full Payload (expandable JSON)
│
├── Filters
│   ├── By Event Type (dropdown: alle 17 types)
│   ├── By Campaign
│   ├── By Date Range
│   └── By Status (success/failed)
│
├── Search
│   └── Full-text search in payloads
│
└── Actions
    ├── Export Logs (CSV/JSON)
    ├── Retry Failed Events
    └── Delete Old Logs
```

**Backend Endpoint:**
```
GET /api/admin/webhooks/logs?limit=100&offset=0&event_type=&campaign_id=&status=
Response: {
  logs: [
    {
      id: uuid,
      event_type: "email_sent",
      timestamp: "2025-10-10T14:30:00Z",
      campaign_id: uuid,
      campaign_name: "Q4 Outreach",
      contact_email: "lead@example.com",
      status: "success",
      payload: {...full webhook data...},
      error_message: null
    }
  ],
  total: 1234,
  limit: 100,
  offset: 0
}
```

#### 2. USER ASSIGNMENT & ZUWEISUNGEN (KRITISCH!) 👥
**Was du gesagt hast:** "Wir müssen auch die Zuweisungen machen können, pro User"

**Implementierung:**
```
Admin Portal → User Management
├── User List
│   ├── Name, Email, Role
│   ├── Organization
│   ├── Status (active/inactive)
│   ├── Assigned Campaigns (count)
│   └── Assigned Contacts (count)
│
├── Assignment Interface
│   ├── Assign Users to Campaigns
│   │   ├── Drag & Drop Interface
│   │   ├── Bulk Assignment
│   │   └── Auto-assign Rules
│   │
│   ├── Assign Contacts to Users
│   │   ├── Round-Robin Assignment
│   │   ├── Lead Score Based
│   │   ├── Manual Assignment
│   │   └── Territory/Region Based
│   │
│   └── Permission Management
│       ├── Can View All Campaigns
│       ├── Can Edit Campaigns
│       ├── Can View Contacts
│       └── Can Export Data
│
└── Activity Tracking
    ├── Last Login
    ├── Tasks Completed
    └── Response Rate
```

**Backend Endpoints:**
```
GET  /api/admin/users?organization_id=
POST /api/admin/users/{user_id}/assign-campaigns
POST /api/admin/users/{user_id}/assign-contacts
GET  /api/admin/users/{user_id}/assignments
PUT  /api/admin/users/{user_id}/permissions
```

#### 3. ONBOARDING-LINK ERSTELLEN (KRITISCH!) 🔗
**Was du gesagt hast:** "Ähnlich wie eigentlich dieses Onboarding-Link erstellen können, damit die auf das Onboarding-Plattform zugreifen kann"

**Implementierung:**
```
Admin Portal → Onboarding Management
├── Onboarding Link Generator
│   ├── Select Organization
│   ├── Select Template (Basic/Advanced/Enterprise)
│   ├── Set Expiration Date
│   ├── Custom Welcome Message
│   └── Generate Unique Link
│
├── Active Onboarding Links
│   ├── Link URL (copy button)
│   ├── Organization
│   ├── Created Date
│   ├── Expires Date
│   ├── Status (active/expired/used)
│   ├── Clicks Count
│   └── Actions (resend, revoke, extend)
│
├── Onboarding Progress Tracking
│   ├── Steps Completed
│   ├── Current Step
│   ├── Time Spent
│   └── Blockers/Issues
│
└── Templates Management
    ├── Create Onboarding Flow
    ├── Step Configuration
    └── Content Editor
```

**Backend Endpoints:**
```
POST /api/admin/onboarding/create-link
     Body: {
       organization_id: uuid,
       template_id: uuid,
       expiration_days: 7,
       welcome_message: "Welcome to Salesbrain!"
     }
     Response: {
       link_url: "https://onboarding.salesbrain.com/o/abc123def456",
       link_id: uuid,
       expires_at: "2025-10-17T00:00:00Z"
     }

GET  /api/admin/onboarding/links?status=active
GET  /api/admin/onboarding/link/{link_id}/progress
POST /api/admin/onboarding/link/{link_id}/revoke
POST /api/admin/onboarding/link/{link_id}/extend
```

#### 4. CAMPAIGN MANAGEMENT UI (KRITISCH!)
- **Campaign List View** (Admin: alle Orgs, Customer: nur eigene)
- **Campaign Statistics Dashboard**
- **Campaign Creation/Edit Forms**
- **Status Controls** (pause, resume, stop)
- **Multi-Channel Configuration** (Email, LinkedIn, SMS, Ads)

#### 5. CONTACT/LEAD MANAGEMENT UI (KRITISCH!)
- **Contact List mit Lead Scoring**
- **Journey Phase Visualization**
- **Contact Detail View** mit Activity Timeline
- **Bulk Actions** (add to campaign, update tags)
- **Import/Export Functionality**

#### 6. MESSAGE CENTER (HOCH!)
- **Unified Inbox** (alle Channels)
- **Conversation Threads**
- **Message Status Indicators**
- **Quick Reply Functionality**
- **AI-powered Reply Suggestions**

#### 7. ORGANIZATION DASHBOARD (KRITISCH!)
- **Overview Statistics** (Campaigns, Contacts, Messages)
- **Recent Activity Feed**
- **Quick Actions Panel**
- **Performance Charts**

#### 8. ANALYTICS & REPORTING (MITTEL)
- **Campaign Performance Widgets**
- **Lead Scoring Analytics**
- **Journey Funnel Visualization**
- **ROI Tracking**
- **Export Functionality**

#### 9. INTEGRATION MANAGEMENT (MITTEL)
- **Provider Connections** (Instantly, WeConnect, etc.)
- **API Key Management**
- **Sync Status & Controls**
- **Webhook Configuration UI**

#### 10. SETTINGS & CONFIGURATION (NIEDRIG)
- **Organization Settings**
- **Notification Preferences**
- **Email Templates**
- **Custom Fields Management**

### DEVELOPMENT PRIORITÄT (Phase 3)

#### **Sofort (Woche 1-2)** - KRITISCH!
1. ✅ Authentication enable & testen
2. ✅ **Webhook Logs UI** (wie oben beschrieben)
3. ✅ **User Assignment Interface** (wie oben beschrieben)
4. ✅ **Onboarding Link Generator** (wie oben beschrieben)
5. Campaign List View (Admin + Customer)
6. Organization Dashboard Landing Page

#### **Sprint 1 (Woche 3-5)** - Phase 3A
1. Campaign Management UI (complete)
2. Contact List (read-only first)
3. Organization Dashboard mit Stats
4. Backend: Contact CRUD API

#### **Sprint 2 (Woche 6-10)** - Phase 3B
1. Contact CRUD Operations UI
2. Message Center (Unified Inbox)
3. Lead Scoring Display
4. Journey Phase Tracking UI
5. Backend: User Management API

#### **Sprint 3 (Woche 11-15)** - Phase 3C
1. Analytics Dashboard
2. User Management UI (complete)
3. Settings & Configuration
4. Integration Management UI
5. Performance Optimierung

### BACKEND REQUIREMENTS (Phase 3)

#### APIs to Implement:
```python
# Webhook Logs
GET  /api/admin/webhooks/logs
GET  /api/admin/webhooks/log/{log_id}
POST /api/admin/webhooks/log/{log_id}/retry
DELETE /api/admin/webhooks/logs/cleanup?older_than=30days

# User Assignment
GET  /api/admin/users?organization_id=
POST /api/admin/users/{user_id}/assign-campaigns
POST /api/admin/users/{user_id}/assign-contacts
GET  /api/admin/users/{user_id}/assignments
PUT  /api/admin/users/{user_id}/permissions

# Onboarding Links
POST /api/admin/onboarding/create-link
GET  /api/admin/onboarding/links?status=
GET  /api/admin/onboarding/link/{link_id}
POST /api/admin/onboarding/link/{link_id}/revoke
POST /api/admin/onboarding/link/{link_id}/extend

# Contact Management (CRUD)
GET  /api/contacts?organization_id=
POST /api/contacts
GET  /api/contacts/{contact_id}
PUT  /api/contacts/{contact_id}
DELETE /api/contacts/{contact_id}
POST /api/contacts/bulk-import
POST /api/contacts/bulk-update

# User Management
GET  /api/admin/users
POST /api/admin/users
GET  /api/admin/users/{user_id}
PUT  /api/admin/users/{user_id}
DELETE /api/admin/users/{user_id}
POST /api/admin/users/{user_id}/reset-password
```

#### Database Tables to Add:
```sql
-- Webhook Logs Table
CREATE TABLE webhook_log (
    id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    campaign_id UUID REFERENCES campaign(id),
    contact_id UUID REFERENCES contact(id),
    status VARCHAR(20), -- success, failed, retrying
    payload JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_webhook_log_created ON webhook_log(created_at DESC);
CREATE INDEX idx_webhook_log_event_type ON webhook_log(event_type);

-- User Campaign Assignment
CREATE TABLE user_campaign_assignment (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    campaign_id UUID REFERENCES campaign(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES "user"(id),
    UNIQUE(user_id, campaign_id)
);

-- User Contact Assignment
CREATE TABLE user_contact_assignment (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    contact_id UUID REFERENCES contact(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES "user"(id),
    UNIQUE(user_id, contact_id)
);

-- Onboarding Links
CREATE TABLE onboarding_link (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organization(id),
    link_token VARCHAR(100) UNIQUE NOT NULL,
    template_id UUID,
    welcome_message TEXT,
    status VARCHAR(20), -- active, expired, used, revoked
    expires_at TIMESTAMPTZ,
    clicks_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES "user"(id)
);
CREATE INDEX idx_onboarding_link_token ON onboarding_link(link_token);
```

---

## 🔮 PHASE 4-7 (GEPLANT)

### Phase 4: WeConnect Integration (Jan-Mar 2026)
- LinkedIn-Automatisierung
- Contact Enrichment
- Multi-Channel Campaigns (Email + LinkedIn)

### Phase 5: Research Tool & Edibot (Apr-Jun 2026)
- Automatische Firmen-Research
- Swiss Company Data (UID-CH)
- Smart Lead Enrichment

### Phase 6: Advanced Analytics (Jul-Sep 2026)
- ROI Tracking
- Custom Reports
- A/B Testing Framework

### Phase 7: Team Collaboration (Okt-Dez 2026)
- Workflow Automation
- CRM Integrationen (Pipedrive, HubSpot)
- Slack Notifications

---

## 📚 DOKUMENTATIONS-STRUKTUR

### Core Documents (Immer aktuell halten!)
- ✅ **MASTER_PLAN.md** (DIES!) - SINGLE SOURCE OF TRUTH
- ✅ **README.md** - Quick Start & Setup
- ✅ **.env** - Environment Configuration (sauber strukturiert!)

### Phase-Specific Docs
- ✅ **docs/PHASE_2_SUMMARY.md** - Phase 2 Abschluss-Report
- ✅ **docs/PHASE_2_CHECKLIST.md** - Phase 2 Checklist (100%)
- 📝 **docs/PHASE_3_REQUIREMENTS.md** - Phase 3 Detailed Specs (TODO)

### API Documentation
- ✅ **docs/INSTANTLY_API_FEATURES.md** - Instantly API Reference (EN)
- ✅ **docs/INSTANTLY_FEATURES_ZUSAMMENFASSUNG_DE.md** - Strategy Guide (DE)

### Admin Portal
- ✅ **docs/ADMIN_PORTAL_ANALYSIS.md** - Current State Analysis
- ✅ **docs/ADMIN_PORTAL_EXECUTIVE_SUMMARY.md** - Executive Summary
- ✅ **docs/ADMIN_PORTAL_CURRENT_STATE.json** - UI Export (Backup)

### Testing
- ✅ **test_instantly_connection.py** - API Connection Test
- ✅ **explore_instantly_api.py** - API Explorer
- ✅ **fetch_instantly_data.py** - Data Export Tool

### Architecture
- 📝 **docs/DATABASE_SCHEMA.md** - Complete DB Schema (TODO)
- 📝 **docs/API_ARCHITECTURE.md** - API Design Guide (TODO)

---

## 🎯 SUCCESS METRICS

### Phase 3 Completion Criteria:
- [ ] Admin kann Webhook Logs sehen (real-time)
- [ ] Admin kann Users zu Campaigns/Contacts zuweisen
- [ ] Admin kann Onboarding-Links erstellen & verwalten
- [ ] Campaign List View funktional (Admin + Customer)
- [ ] Contact Management CRUD komplett
- [ ] Message Center (Unified Inbox) funktional
- [ ] Organization Dashboard mit Stats
- [ ] Authentication enabled und getestet
- [ ] All APIs connected to UI
- [ ] Real-time updates via WebSockets/Polling

### KPIs:
- Backend API Response Time: < 200ms
- Frontend Load Time: < 2s
- Webhook Processing: < 1s
- Database Uptime: > 99.9%
- Test Coverage: > 80%

---

## 🔧 TECH STACK (Aktuell)

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.104.1
- **Database:** PostgreSQL 17 (2 instances)
- **ORM:** Direct SQL (asyncpg)
- **Validation:** Pydantic 2.x
- **Testing:** pytest + respx
- **HTTP Client:** httpx 0.28.0
- **Retry Logic:** tenacity 9.0.0

### Frontend (Admin Portal)
- **Framework:** React (assumed from UI builder)
- **UI Builder:** Custom component system
- **Language:** German (Deutsch)
- **Icons:** Lucide
- **Animations:** Lottie

### Infrastructure
- **Hosting:** Digital Ocean App Platform
- **Database:** Digital Ocean Managed PostgreSQL
- **CI/CD:** GitHub Actions (planned)
- **Monitoring:** (TODO - Phase 6)

### Integrations
- **Instantly.ai:** Email Campaigns (API v2) ✅
- **WeConnect:** LinkedIn (Planned - Phase 4)
- **Edibot:** Research (Planned - Phase 5)

---

## 📝 OPEN TODOS (High Priority)

### Sofort:
- [ ] Webhook Logs Backend API implementieren
- [ ] Webhook Logs UI bauen
- [ ] User Assignment Backend API implementieren
- [ ] User Assignment UI bauen
- [ ] Onboarding Links Backend API implementieren
- [ ] Onboarding Links UI bauen
- [ ] Authentication enable & testen

### Phase 3:
- [ ] Campaign List UI (Admin + Customer)
- [ ] Contact CRUD Backend API
- [ ] Contact Management UI
- [ ] Message Center UI
- [ ] Organization Dashboard
- [ ] Analytics Dashboard

### Technical Debt:
- [ ] Unit Tests (Services, Webhooks)
- [ ] Integration Tests (Mock Instantly API)
- [ ] Load Testing (1000+ users)
- [ ] Security Audit
- [ ] Database Backup Strategy

---

## 🚨 WICHTIGE HINWEISE

### Environment Variables (.env)
**IMMER sauber strukturiert halten!**
- Klare Kommentare zu jedem Key
- Metadaten (Generated Date, Permissions, etc.)
- Verwendungszweck dokumentieren
- Legacy-Keys kennzeichnen

**Beispiel:**
```bash
# ============================================
# INSTANTLY.AI INTEGRATION
# ============================================
# API v2 Key (Bearer Token Authentication)
# Workspace: Salesbrain
# Generated: 2025-10-10
# Permissions: Full API access
INSTANTLY_API_KEY=ZTRk...
```

### Git Commits
**Struktur:**
- Clear, descriptive messages
- Include Co-Authored-By: Claude
- Reference issue/phase numbers
- Group related changes

### Code Style
- Type hints überall (Python)
- Pydantic validation für alle APIs
- Error handling mit Details
- Logging für alle kritischen Operations

---

## 📞 NEXT STEPS (Konkret!)

### Diese Woche:
1. **MASTER_PLAN.md** finalisieren und committen
2. **Webhook Logs** Backend API implementieren
3. **Webhook Logs** Frontend UI bauen
4. **User Assignment** Backend API implementieren
5. **User Assignment** Frontend UI bauen

### Nächste Woche:
1. **Onboarding Links** Backend + Frontend
2. Campaign List View UI
3. Authentication enable & testen
4. Organization Dashboard

---

**ENDE DES MASTER PLANS**

**Letzte Aktualisierung:** 2025-10-10
**Nächste Review:** Bei Phase 3 Completion
**Verantwortlich:** Ivan (Product Owner) + Claude (AI Assistant)

---

**Salesbrain © 2025**
