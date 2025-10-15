# 🔗 Salesbrain - Frontend-Backend Integration Guide

> **Erstellt:** 2025-10-15
> **Für:** Frontend-Team
> **Backend Status:** Phase 3 (70% complete)
> **Frontend Status:** Phase 1 complete, wartet auf Backend-Integration

---

## 📊 EXECUTIVE SUMMARY

### Aktueller Status

| Komponente | Status | Beschreibung |
|------------|--------|--------------|
| **Backend API** | 70% complete | Salesbrain-Backend (FastAPI) auf Port 8001 |
| **Frontend UI** | Phase 1 complete | Salesbrain-UI-Beta (Next.js 15) mit Demo-Daten |
| **GitHub Repository** | Identisch | https://github.com/Civandigi/Salesbrain-UI-Beta |
| **API Integration** | 0% | Alle API-Calls sind Placeholders |

### Kritische Erkenntnisse

🔴 **KRITISCH - API-Struktur-Konflikt:**
- **Frontend erwartet:** `/api/v1/` Struktur
- **Backend liefert:** `/api/` und `/api/admin/` Struktur
- **Lösung:** Frontend muss API-Client anpassen ODER Backend Routing anpassen

🟡 **WICHTIG - Fehlende Backend-APIs:**
- User Management CRUD (erstellen, bearbeiten, löschen)
- Contact Management CRUD
- Mehrere Frontend-spezifische Endpunkte

✅ **POSITIV:**
- Backend hat solide Basis (Instantly Integration, Webhooks, Onboarding)
- Frontend ist professionell gebaut mit guter Struktur
- Klare API-Dokumentation vorhanden

---

## 🏗️ TEIL 1: VERFÜGBARE BACKEND-APIs

### Backend-Server

**Base URL:** http://localhost:8001 (Development)
**Production URL:** TBD
**Technologie:** FastAPI (Python 3.11+)
**Authentifizierung:** JWT Bearer Tokens

### 1.1 Instantly Integration APIs ✅ (100% Complete)

**Endpoint-Struktur:** `/api/admin/`

```python
# Campaign Management
GET  /api/admin/campaigns
POST /api/admin/campaigns
GET  /api/admin/campaigns/{campaign_id}
PUT  /api/admin/campaigns/{campaign_id}

# Email Accounts
GET  /api/admin/email-accounts
POST /api/admin/email-accounts
GET  /api/admin/email-accounts/{account_id}

# Message Search
POST /api/admin/messages/search
GET  /api/admin/messages/{message_id}

# Organization Stats
GET  /api/admin/organizations/{org_id}/stats
```

**Beispiel Response:**
```json
{
  "status": "success",
  "data": {
    "campaigns": [
      {
        "id": "uuid",
        "name": "Q4 Outreach",
        "status": "active",
        "type": "email",
        "instantly_campaign_id": "abc123"
      }
    ]
  }
}
```

---

### 1.2 Webhook Logs APIs ✅ (100% Complete)

**Endpoint-Struktur:** `/api/admin/webhooks/logs`

```python
# Webhook Logs
GET  /api/admin/webhooks/logs
     Query: ?limit=100&offset=0&event_type=&campaign_id=&status=

GET  /api/admin/webhooks/log/{log_id}

POST /api/admin/webhooks/log/{log_id}/retry

DELETE /api/admin/webhooks/logs/cleanup
       Body: {"older_than_days": 30}
```

**Event Types (17 total):**
- email_sent, email_opened, email_clicked, email_replied
- email_bounced, email_unsubscribed, lead_replied
- campaign_started, campaign_paused, campaign_completed
- etc.

**Beispiel Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "event_type": "email_sent",
      "campaign_id": "uuid",
      "contact_email": "lead@example.com",
      "status": "success",
      "payload": {...},
      "created_at": "2025-10-15T12:00:00Z"
    }
  ],
  "total": 1234,
  "limit": 100,
  "offset": 0
}
```

---

### 1.3 User Assignment APIs ✅ (100% Complete)

**Endpoint-Struktur:** `/api/admin/users/{user_id}/assignments`

```python
# User Assignments
GET  /api/admin/users/{user_id}/assignments
POST /api/admin/users/{user_id}/assign-campaigns
     Body: {"campaign_ids": ["uuid1", "uuid2"]}

POST /api/admin/users/{user_id}/assign-contacts
      Body: {"contact_ids": ["uuid1", "uuid2"]}

DELETE /api/admin/users/{user_id}/assignments/{assignment_id}
```

---

### 1.4 Onboarding Links APIs ✅ (100% Complete + Option B)

**Endpoint-Struktur:** `/api/admin/onboarding/`

```python
# Onboarding Link Management
POST /api/admin/onboarding/create-link
     Body: {
       "organization_id": "uuid",
       "campaign_types": {
         "linkedin": true,
         "email": true,
         "linkedin_ads": false,
         "google_ads": false
       },
       "template_name": "Basic",
       "expiration_days": 7,
       "welcome_message": "Welcome to Salesbrain!"
     }

GET  /api/admin/onboarding/links?status=active
GET  /api/admin/onboarding/link/{link_id}
POST /api/admin/onboarding/link/{link_id}/revoke
POST /api/admin/onboarding/link/{link_id}/extend

# Public Access (Customer Side)
GET  /api/admin/onboarding/o/{link_token}
PUT  /api/admin/onboarding/o/{link_token}/progress
POST /api/admin/onboarding/o/{link_token}/complete

# Option B Features (Dynamic Steps, Contract Blocker)
PUT  /api/admin/onboarding/o/{token}/contract-status
POST /api/admin/onboarding/o/{token}/domain-selected
GET  /api/admin/onboarding/o/{token}/steps
GET  /api/admin/onboarding/o/{token}/contract-blocker
```

**Features:**
- Dynamic step generation based on campaign_types
- Contract blocker logic (all steps disabled until contract uploaded)
- Auto-calculate Go-Live date (7 days after domain selection)
- Progress tracking

---

### 1.5 Authentication APIs ✅

**Endpoint-Struktur:** `/api/auth/`

```python
POST /api/auth/login
     Body: {"email": "admin@example.com", "password": "password"}
     Response: {"access_token": "jwt_token", "token_type": "bearer"}

POST /api/auth/register
GET  /api/auth/me
POST /api/auth/refresh
```

---

### 1.6 Health Check APIs ✅

```python
GET  /api/health
Response: {
  "status": "ok",
  "databases": {
    "global_kb": "connected",
    "tenant_db": "connected"
  }
}
```

---

## ❌ TEIL 2: FEHLENDE BACKEND-APIs

### 2.1 User Management CRUD ❌ (KRITISCH!)

**Frontend erwartet:** `/api/v1/auth/` Struktur (aus client.ts)

**Was fehlt:**
```python
# User Management (benötigt vom Admin-Portal)
POST /api/admin/users                     # User erstellen
GET  /api/admin/users                     # Liste aller User
GET  /api/admin/users/{user_id}           # User Details
PUT  /api/admin/users/{user_id}           # User bearbeiten
DELETE /api/admin/users/{user_id}         # User löschen
POST /api/admin/users/{user_id}/reset-password
POST /api/admin/users/bulk-import         # CSV Import
```

**Frontend UI wartet darauf:**
- Admin Portal - Users Page zeigt Demo-Daten
- "Neuer Benutzer" Modal fehlt
- User Edit Modal fehlt
- User Assignment Interface fehlt

---

### 2.2 Contact Management APIs ❌

**Frontend erwartet:** `/api/v1/workspaces/{id}/leads` Struktur

**Was fehlt:**
```python
GET  /api/contacts?organization_id=
POST /api/contacts
GET  /api/contacts/{contact_id}
PUT  /api/contacts/{contact_id}
DELETE /api/contacts/{contact_id}
POST /api/contacts/bulk-import
POST /api/contacts/bulk-update
```

---

### 2.3 Opportunity Management APIs ❌

**Frontend erwartet (aus client.ts):**
```typescript
/api/v1/workspaces/{id}/opportunities
/api/v1/opportunities/{id}
/api/v1/opportunities/{id}/confirm
/api/v1/opportunities/{id}/notes
/api/v1/opportunities/{id}/timeline
```

**Note:** Frontend hat umfangreichen Opportunity Management Client (Juli 2025 Spec)

---

### 2.4 Chat/AI APIs ❌

**Frontend erwartet:**
```typescript
/api/v1/workspaces/{id}/chat-sessions
/api/v1/chat-sessions/{id}/messages
```

**WebSocket:**
- Frontend hat Socket.IO Client vorbereitet
- Backend WebSocket-Integration fehlt

---

## 🔥 TEIL 3: API-STRUKTUR-KONFLIKT

### Problem

**Frontend API-Client (client.ts):**
```typescript
// Erwartet:
/api/v1/auth/login
/api/v1/workspaces/
/api/v1/campaigns/
/api/v1/leads/
/api/v1/opportunities/
```

**Backend tatsächlich:**
```python
# Liefert:
/api/auth/login
/api/admin/campaigns
/api/admin/email-accounts
/api/admin/webhooks/logs
/api/admin/onboarding/
```

### Lösungen

**Option A: Frontend anpassen** (Empfohlen für jetzt)
```typescript
// In lib/api/client.ts ändern:
const API_V1 = '/api'           // Statt /api/v1
const API_ADMIN = '/api/admin'

// Beispiel:
async getCampaigns() {
  return this.request('/api/admin/campaigns')  // Statt /api/v1/campaigns
}
```

**Option B: Backend Router hinzufügen** (Langfristig besser)
```python
# Backend: Aliase für /api/v1/* erstellen
@app.get("/api/v1/campaigns")
async def get_campaigns_v1():
    return await get_campaigns()  # Ruft /api/admin/campaigns auf
```

**Option C: Proxy im Frontend** (Quick Fix)
```typescript
// next.config.js
rewrites: async () => [
  {
    source: '/api/v1/:path*',
    destination: 'http://localhost:8001/api/:path*'
  }
]
```

---

## 🎯 TEIL 4: FRONTEND-TEAM AUFGABEN

### Sprint 1: Backend-Integration Vorbereitung (2-3 Tage)

#### Task 1.1: API-Client anpassen

**Datei:** `lib/api/client.ts`

**Änderungen:**
```typescript
// 1. Base URL anpassen
class APIClient {
  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001') {
    this.baseURL = baseURL
  }

  // 2. Endpunkte anpassen auf Backend-Struktur
  async getCampaigns(workspaceId: number) {
    // VORHER: return this.request('/api/v1/campaigns/?workspace_id=${workspaceId}')
    // NACHHER:
    return this.request(`/api/admin/campaigns?organization_id=${workspaceId}`)
  }
}
```

**Aufwand:** 1-2 Tage (alle Endpunkte durchgehen)

---

#### Task 1.2: Onboarding API Integration

**Datei:** `lib/api/onboarding.ts`

**Änderungen:**
```typescript
// Bereits vorbereitet! Nur Placeholder-Funktionen entfernen:

// ENTFERNEN:
export const onboardingApiPlaceholder = { ... }

// Placeholder aus Components entfernen und durch onboardingApi ersetzen:
// VORHER:
await onboardingApiPlaceholder.generateOnboardingLink(userId)

// NACHHER:
await onboardingApi.generateLink(userId, { expiration_days: 7 })
```

**Aufwand:** 0.5 Tage

---

#### Task 1.3: Webhook Logs Integration

**Datei:** `lib/api/admin-webhooks.ts`

**Änderungen:**
```typescript
// Uncomment echte API-Calls:
export async function fetchWebhookLogs(filters: WebhookFilters = {}) {
  // VORHER: Return Mock-Daten

  // NACHHER:
  const params = new URLSearchParams()
  if (filters.event_type) params.append('event_type', filters.event_type)
  if (filters.campaign_id) params.append('campaign_id', filters.campaign_id)
  if (filters.status) params.append('status', filters.status)
  if (filters.limit) params.append('limit', filters.limit.toString())
  if (filters.offset) params.append('offset', filters.offset.toString())

  const response = await fetch(`${API_BASE_URL}/api/admin/webhooks/logs?${params}`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    }
  })

  return response.json()
}
```

**Aufwand:** 0.5 Tage

---

#### Task 1.4: Environment Variables

**Datei:** `.env.local`

```bash
# Erstellen:
NEXT_PUBLIC_API_URL=http://localhost:8001

# Production:
NEXT_PUBLIC_API_URL=https://api.salesbrain.ch
```

**Aufwand:** 0.5 Tage (inkl. Testing)

---

### Sprint 2: User Management Integration (3-4 Tage)

#### Task 2.1: User Create Modal

**Datei:** `components/admin/modals/CreateUserModal.tsx` (NEU erstellen)

**Komponente:**
```typescript
interface CreateUserModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (user: User) => void
}

export function CreateUserModal({ isOpen, onClose, onSuccess }: CreateUserModalProps) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'staff',
    organization_id: ''
  })

  const handleSubmit = async () => {
    // API Call:
    const response = await fetch(`${API_BASE_URL}/api/admin/users`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    })

    const user = await response.json()
    onSuccess(user)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Neuen Benutzer erstellen</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          {/* Form Fields hier */}
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

**Aufwand:** 1 Tag

---

#### Task 2.2: User List Backend Integration

**Datei:** `app/admin-portal/users/page.tsx`

**Änderungen:**
```typescript
// VORHER: const users = demoUsers

// NACHHER:
const [users, setUsers] = useState<User[]>([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  async function loadUsers() {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/users?limit=100`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      setUsers(data.users)
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setLoading(false)
    }
  }

  loadUsers()
}, [])

if (loading) return <LoadingSpinner />
```

**Aufwand:** 0.5 Tage

---

#### Task 2.3: User Assignment Interface

**Datei:** `components/admin/UserAssignmentModal.tsx` (NEU erstellen)

**UI-Struktur:**
```
┌─────────────────────────────────────────────┐
│ User zuweisen: Max Mustermann               │
├─────────────────────────────────────────────┤
│ [Campaigns] [Contacts]                      │
│                                             │
│ Verfügbare Campaigns:                       │
│ ☑ Q4 Outreach Campaign                      │
│ ☐ LinkedIn Prospecting                      │
│ ☐ Cold Email Series #1                      │
│ ☑ Webinar Follow-ups                        │
│                                             │
│ [Alle auswählen] [Keine auswählen]          │
│                                             │
│           [Abbrechen]  [Speichern]          │
└─────────────────────────────────────────────┘
```

**Backend Call:**
```typescript
await fetch(`${API_BASE_URL}/api/admin/users/${userId}/assign-campaigns`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${getAuthToken()}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    campaign_ids: selectedCampaignIds
  })
})
```

**Aufwand:** 2-3 Tage (komplex)

---

### Sprint 3: Onboarding Tool Integration (2-3 Tage)

#### Task 3.1: Dynamic Steps Integration

**Datei:** `app/onboarding/dashboard/page.tsx`

**Änderungen:**
```typescript
// VORHER: Hardcoded 7 Steps

// NACHHER: Dynamic Steps von Backend
const [steps, setSteps] = useState<Step[]>([])
const [blockerInfo, setBlockerInfo] = useState(null)

useEffect(() => {
  async function loadDynamicSteps() {
    // Dynamische Steps von Backend laden
    const response = await fetch(`${API_BASE_URL}/api/admin/onboarding/o/${token}/steps`)
    const data = await response.json()
    setSteps(data.steps)  // Basierend auf campaign_types!

    // Contract Blocker prüfen
    const blocker = await fetch(`${API_BASE_URL}/api/admin/onboarding/o/${token}/contract-blocker`)
    const blockerData = await blocker.json()
    setBlockerInfo(blockerData)
  }

  loadDynamicSteps()
}, [token])

// Steps anzeigen:
{steps.map(step => (
  <StepCard
    key={step.step_id}
    {...step}
    isEnabled={step.is_enabled}  // Disabled wenn Contract Blocker aktiv!
    onClick={() => step.is_enabled ? navigate(step.step_slug) : showBlockerModal()}
  />
))}
```

**Aufwand:** 1 Tag

---

#### Task 3.2: Contract Blocker UI

**Datei:** `components/onboarding/ContractBlockerModal.tsx` (NEU erstellen)

**UI:**
```
┌─────────────────────────────────────────────┐
│ 🔒 Vertrag erforderlich                     │
│                                             │
│ Bitte laden Sie zuerst Ihren Vertrag hoch, │
│ bevor Sie mit den nächsten Schritten        │
│ fortfahren können.                          │
│                                             │
│           [Zum Schritt 1 (Vertrag)]         │
└─────────────────────────────────────────────┘
```

**Aufwand:** 0.5 Tage

---

#### Task 3.3: Go-Live Date Display

**Datei:** `components/onboarding/GoLiveDateBanner.tsx` (NEU erstellen)

**Backend Call:**
```typescript
// Nach Domain-Auswahl:
const response = await fetch(`${API_BASE_URL}/api/admin/onboarding/o/${token}`)
const data = await response.json()

// Anzeigen:
<div className="golive-banner">
  🎉 Domain erfolgreich ausgewählt!

  Ihr voraussichtliches Go-Live-Datum:
  📅 {format(new Date(data.estimated_golive_date), 'dd. MMMM yyyy')}

  Setup-Zeit: 7 Werktage
</div>
```

**Aufwand:** 0.5 Tage

---

## 🔐 TEIL 5: AUTHENTICATION & SECURITY

### JWT Token Handling

**Frontend Implementierung:**

```typescript
// lib/auth.ts
export function getAuthToken(): string {
  if (typeof window === 'undefined') return ''
  return localStorage.getItem('auth_token') || ''
}

export function setAuthToken(token: string) {
  localStorage.setItem('auth_token', token)
}

export function clearAuthToken() {
  localStorage.removeItem('auth_token')
}

// Bei Login:
const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})

const { access_token } = await response.json()
setAuthToken(access_token)

// Bei jedem API-Call:
headers: {
  'Authorization': `Bearer ${getAuthToken()}`,
  'Content-Type': 'application/json'
}
```

### CORS Configuration

**Backend (bereits konfiguriert):**
```python
CORS(app, origins=[
    "https://admin.salesbrain.ch",
    "http://localhost:3000"
])
```

**Frontend:** Keine Änderungen nötig

---

## 📋 TEIL 6: TESTING-STRATEGIE

### 6.1 API Integration Testing

**Checklist:**
```bash
# 1. Backend Health Check
curl http://localhost:8001/api/health

# 2. Authentication
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# 3. Campaigns (mit Token)
curl http://localhost:8001/api/admin/campaigns \
  -H "Authorization: Bearer <TOKEN>"

# 4. Webhooks
curl http://localhost:8001/api/admin/webhooks/logs?limit=10 \
  -H "Authorization: Bearer <TOKEN>"

# 5. Onboarding
curl http://localhost:8001/api/admin/onboarding/links \
  -H "Authorization: Bearer <TOKEN>"
```

### 6.2 Frontend E2E Testing

**Test-Szenarien:**
1. ✅ Login → Token gespeichert?
2. ✅ User List → Echte Daten?
3. ✅ User Assignment → Backend Call erfolgreich?
4. ✅ Onboarding Link generieren → Link funktioniert?
5. ✅ Webhook Logs → Pagination funktioniert?

---

## 🚀 TEIL 7: DEPLOYMENT

### 7.1 Environment Variables

**Development (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Production (.env.production):**
```bash
NEXT_PUBLIC_API_URL=https://api.salesbrain.ch
```

### 7.2 Build & Deploy

```bash
# 1. Build
npm run build

# 2. Test Production Build
npm run start

# 3. Deploy zu GitHub
git add .
git commit -m "Integrate Backend APIs - Phase 2 complete"
git push origin main
```

---

## 📊 TEIL 8: TIMELINE & AUFWAND

### Geschätzter Aufwand

| Sprint | Aufgaben | Aufwand | Priorität |
|--------|----------|---------|-----------|
| **Sprint 1** | API-Client anpassen, Onboarding/Webhooks integrieren | 2-3 Tage | 🔴 KRITISCH |
| **Sprint 2** | User Management Integration (Create, Edit, Assignment) | 3-4 Tage | 🔴 KRITISCH |
| **Sprint 3** | Onboarding Tool Dynamic Steps & Contract Blocker | 2-3 Tage | 🟡 WICHTIG |
| **Sprint 4** | Campaign/Contact Management (wenn Backend bereit) | 4-5 Tage | 🟢 SPÄTER |

**GESAMT:** 11-15 Tage (~2-3 Wochen)

---

## ✅ TEIL 9: SUCCESS CRITERIA

### Sprint 1 erfolgreich wenn:
- ✅ API-Client kann Backend erreichen
- ✅ Authentication funktioniert (Login, Token Storage)
- ✅ Webhook Logs zeigen echte Daten
- ✅ Onboarding API funktioniert
- ✅ Keine Mock-Daten mehr in Webhook/Onboarding Seiten

### Sprint 2 erfolgreich wenn:
- ✅ Admin kann neue User erstellen (Modal funktioniert)
- ✅ User-Liste zeigt echte Backend-Daten
- ✅ User Assignment Interface funktioniert
- ✅ User kann zu Campaigns zugewiesen werden
- ✅ Backend erhält korrekte Assignment-Calls

### Sprint 3 erfolgreich wenn:
- ✅ Onboarding Tool lädt Dynamic Steps von Backend
- ✅ Contract Blocker funktioniert (Steps disabled bis Upload)
- ✅ Go-Live Datum wird korrekt berechnet & angezeigt
- ✅ Kunden können Onboarding-Prozess durchlaufen

---

## 🔗 TEIL 10: WICHTIGE LINKS & RESSOURCEN

### Dokumentation (Backend)

**Lokales Projekt:**
- `salesbrain-backend/MASTER_PLAN.md` - Phase 1-7 Roadmap
- `salesbrain-backend/docs/PHASE_2_SUMMARY.md` - Instantly Integration Details
- `salesbrain-backend/docs/BACKEND_TASKS_OPTION_B.md` - Option B Features

**Root-Projekt:**
- `PROJECT_ORCHESTRATOR_AUDIT_REPORT.md` - Vollständiger Projekt-Audit
- `COMPREHENSIVE_PROJECT_AUDIT_2025.md` - Sprint-Details

### Dokumentation (Frontend GitHub)

**GitHub Repository:**
- `BACKEND_ANFORDERUNGEN.md` - Was Frontend erwartet (5 Endpoints)
- `ADMIN_PORTAL_AUDIT_2025.md` - Hard Audit Report
- `ONBOARDING_MASTER_PLAN.md` - Onboarding Konzept
- `README.md` - Project Overview

### API Documentation

**Swagger UI (wenn Backend läuft):**
```
http://localhost:8001/docs
```

**ReDoc:**
```
http://localhost:8001/redoc
```

---

## 📞 TEIL 11: KONTAKT & SUPPORT

### Bei Fragen zu:

**Backend APIs:**
- Siehe `salesbrain-backend/docs/` für Details
- Swagger UI für Live-Dokumentation
- MASTER_PLAN.md für Roadmap

**Frontend Integration:**
- Siehe dieses Dokument
- `FRONTEND_UMSETZUNG.md` im GitHub Repo
- `BACKEND_ANFORDERUNGEN.md` im GitHub Repo

### Team-Koordination

**Backend-Team:**
- Kommuniziert Deployment-Status
- Dokumentiert API-Änderungen vor Implementierung

**Frontend-Team:**
- Entwickelt mit Mock-Daten
- Integriert APIs nach Deployment
- Testet mit echtem Backend

---

## 🎯 NEXT STEPS (Konkret)

### Für Frontend-Team:

**SOFORT (Heute/Morgen):**
1. ✅ Dieses Dokument durchlesen & verstehen
2. ✅ Backend lokal starten & testen:
   ```bash
   cd salesbrain-backend
   uvicorn app.main:app --reload --port 8001
   ```
3. ✅ API-Endpunkte mit curl testen (siehe Teil 6.1)
4. ✅ `.env.local` erstellen mit `NEXT_PUBLIC_API_URL=http://localhost:8001`

**DIESE WOCHE (Sprint 1):**
1. API-Client anpassen (`lib/api/client.ts`)
2. Onboarding API integrieren (Placeholder entfernen)
3. Webhook Logs API integrieren
4. Testen mit echtem Backend

**NÄCHSTE WOCHE (Sprint 2):**
1. User Create Modal bauen
2. User List Backend-Integration
3. User Assignment Interface bauen
4. Testen

---

## 🚨 WICHTIGE HINWEISE

### Builder.io Klarstellung

❌ **FALSCH:** "Frontend wird komplett auf Builder.io gemacht"
✅ **RICHTIG:** Builder.io wird nur für Lottie-Animationen genutzt

```typescript
// Nur in AppIcon.tsx:
animationUrl = 'https://cdn.builder.io/o/assets%2F...'
```

**Das gesamte Frontend ist reguläres Next.js/React!**

### API-Struktur-Konflikt

⚠️ **KRITISCH:** Frontend und Backend nutzen unterschiedliche API-Strukturen!

**Lösung (kurzfristig):** Frontend API-Client anpassen (Option A)
**Lösung (langfristig):** Backend Router für `/api/v1/*` hinzufügen (Option B)

### Demo-Daten entfernen

🔴 **WICHTIG:** Alle Demo-Daten durch Backend-Calls ersetzen!

**Dateien prüfen:**
- `lib/demo-data.ts` - Kann bleiben (für Fallback)
- `lib/data/demo-webhooks.ts` - Backend-Integration bevorzugen
- `app/admin-portal/users/page.tsx` - demoUsers ersetzen!
- `lib/api/admin-webhooks.ts` - Mock-Logik durch echte Calls ersetzen

---

## ✅ ZUSAMMENFASSUNG

### Was Backend bereitstellt:
- ✅ Instantly Integration (Campaigns, Email Accounts, Messages)
- ✅ Webhook Logs (17 Event Types)
- ✅ User Assignments (Campaigns, Contacts)
- ✅ Onboarding Links (mit Dynamic Steps & Contract Blocker)
- ✅ Authentication (JWT)

### Was Backend noch braucht:
- ❌ User Management CRUD
- ❌ Contact Management CRUD
- ❌ Opportunity Management APIs
- ❌ Chat/WebSocket APIs

### Was Frontend tun muss:
1. API-Client anpassen (API-Struktur-Konflikt lösen)
2. Onboarding API integrieren (Placeholder entfernen)
3. Webhook Logs API integrieren
4. User Management UIs bauen (Create, Edit, Assignment)
5. Onboarding Dynamic Steps integrieren
6. Demo-Daten durch Backend-Calls ersetzen

### Timeline:
- Sprint 1: 2-3 Tage (API Integration Basics)
- Sprint 2: 3-4 Tage (User Management)
- Sprint 3: 2-3 Tage (Onboarding Tool)
- **GESAMT: 2-3 Wochen bis Phase 2 Complete**

---

**Status:** ✅ Ready for Frontend-Team
**Erstellt von:** Claude (AI Project Orchestrator)
**Für:** Frontend-Team
**Datum:** 2025-10-15
**Version:** 1.0
