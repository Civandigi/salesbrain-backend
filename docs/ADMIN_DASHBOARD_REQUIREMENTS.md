# 🎛️ Admin Dashboard - Requirements Document

> **Projekt:** Salesbrain Admin Portal
> **Version:** 1.0.0
> **Erstellt:** 2025-10-10
> **Status:** Ready for Implementation
> **Zielgruppe:** Frontend/UI Development Team

---

## 📋 Übersicht

Dieses Dokument enthält alle Requirements für das Salesbrain Admin Dashboard. Es dient als Übergabe-Dokument zwischen Backend und Frontend und definiert die Must-Have Features, API-Endpunkte, Datenstrukturen und UI-Komponenten.

---

## 🎯 Kritische Features (Must-Have)

### 1. WEBHOOK LOGS & MONITORING 📊

**Priorität:** KRITISCH
**Status:** Backend API bereit, UI fehlt komplett

#### Funktionale Requirements

Das Admin Dashboard MUSS eine Webhook Logs Seite haben mit:

1. **Real-time Log Feed**
   - Zeigt alle eingehenden Webhooks in Echtzeit
   - Auto-refresh alle 5 Sekunden (konfigurierbar)
   - Neueste Events oben

2. **Event Details pro Log-Eintrag**
   - Event Type (Badge mit Farbe)
   - Timestamp (formatiert: "vor 2 Minuten", "heute 14:30", etc.)
   - Campaign Name (klickbar → Campaign Detail)
   - Contact Email (klickbar → Contact Detail)
   - Status (success/failed/retrying)
   - Full Payload (expandable JSON viewer)

3. **Filter & Search**
   - Filter nach Event Type (Dropdown mit allen 17 Typen)
   - Filter nach Campaign (Autocomplete)
   - Filter nach Status (success/failed/retrying)
   - Date Range Picker (von/bis)
   - Full-text Search in Payloads

4. **Actions**
   - Export als CSV/JSON (gefilterte Ergebnisse)
   - Retry Failed Webhooks (einzeln oder bulk)
   - Delete Old Logs (älter als X Tage)
   - View Raw Payload (Modal mit JSON)

#### Backend API Endpoints

```http
GET /api/admin/webhooks/logs
```

**Query Parameters:**
- `limit` (int, default: 100) - Anzahl Ergebnisse
- `offset` (int, default: 0) - Pagination
- `event_type` (string, optional) - Filter nach Event Type
- `campaign_id` (uuid, optional) - Filter nach Campaign
- `status` (string, optional) - Filter nach Status (success/failed/retrying)
- `date_from` (datetime, optional) - Von Datum
- `date_to` (datetime, optional) - Bis Datum
- `search` (string, optional) - Full-text search in payload

**Response:**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": "uuid",
        "event_type": "email_sent",
        "campaign_id": "uuid",
        "campaign_name": "Campaign ABC",
        "contact_id": "uuid",
        "contact_email": "lead@example.com",
        "status": "success",
        "payload": { /* full webhook payload */ },
        "error_message": null,
        "created_at": "2025-10-10T14:30:00Z"
      }
    ],
    "total": 1234,
    "limit": 100,
    "offset": 0
  }
}
```

```http
POST /api/admin/webhooks/logs/{log_id}/retry
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook retry queued"
}
```

```http
DELETE /api/admin/webhooks/logs/cleanup
```

**Query Parameters:**
- `older_than_days` (int, required) - Löscht Logs älter als X Tage

**Response:**
```json
{
  "success": true,
  "deleted_count": 156
}
```

#### 17 Webhook Event Types

**Email Events (7):**
1. `email_sent` - Email wurde versendet
2. `email_opened` - Email wurde geöffnet
3. `email_clicked` - Link in Email geklickt
4. `reply_received` - Antwort erhalten
5. `email_bounced` - Email nicht zustellbar
6. `email_unsubscribed` - Empfänger hat abgemeldet
7. `email_spam_report` - Als Spam markiert

**Lead Events (5):**
8. `lead_interested` - Lead zeigt Interesse
9. `lead_not_interested` - Lead lehnt ab
10. `lead_meeting_booked` - Meeting gebucht
11. `lead_completed` - Lead-Prozess abgeschlossen
12. `lead_error` - Fehler beim Lead-Processing

**Campaign Events (3):**
13. `campaign_started` - Campaign gestartet
14. `campaign_paused` - Campaign pausiert
15. `campaign_completed` - Campaign beendet

**Account Events (2):**
16. `account_error` - Fehler mit Email Account
17. `account_suspended` - Account suspendiert

#### UI Mockup (Struktur)

```
┌────────────────────────────────────────────────────────────┐
│ 🎛️ Admin Dashboard > Webhook Logs                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Filters:  [Event Type ▼] [Campaign ▼] [Status ▼]        │
│            [Date From] [Date To] [Search...    ] [Apply]  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🟢 email_sent | Campaign: ABC | lead@example.com     │ │
│  │    2 minutes ago                              [View] │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ 🔴 email_bounced | Campaign: XYZ | bad@example.com   │ │
│  │    5 minutes ago                       [View][Retry] │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ 🟡 reply_received | Campaign: ABC | lead@example.com │ │
│  │    10 minutes ago                             [View] │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Showing 1-100 of 1,234      [< Prev] [Next >]            │
│                                                            │
│  [Export CSV] [Export JSON] [Cleanup Old Logs]            │
└────────────────────────────────────────────────────────────┘
```

#### Database Schema

```sql
CREATE TABLE webhook_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    campaign_id UUID REFERENCES campaign(id),
    contact_id UUID REFERENCES contact(id),
    status VARCHAR(20) NOT NULL, -- success, failed, retrying
    payload JSONB NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    retry_count INT DEFAULT 0,
    last_retry_at TIMESTAMPTZ
);

CREATE INDEX idx_webhook_log_event_type ON webhook_log(event_type);
CREATE INDEX idx_webhook_log_campaign_id ON webhook_log(campaign_id);
CREATE INDEX idx_webhook_log_status ON webhook_log(status);
CREATE INDEX idx_webhook_log_created_at ON webhook_log(created_at DESC);
CREATE INDEX idx_webhook_log_payload ON webhook_log USING gin(payload);
```

---

### 2. USER ASSIGNMENT & ZUWEISUNGEN 👥

**Priorität:** KRITISCH
**Status:** Backend API fehlt, UI fehlt komplett

#### Funktionale Requirements

Das Admin Dashboard MUSS eine User Management Seite haben mit:

1. **User List**
   - Alle Users der Organisation
   - Name, Email, Role, Status
   - Assigned Campaigns Count
   - Assigned Contacts Count

2. **Campaign Assignment**
   - Drag & Drop Interface (User ↔ Campaign)
   - Bulk Assignment (mehrere Users gleichzeitig)
   - Auto-Assignment Rules (z.B. Round-Robin)
   - Assignment History

3. **Contact Assignment**
   - Assign Contacts zu Users
   - Round-Robin Distribution
   - Lead Score Based Assignment
   - Manual Assignment
   - Bulk Operations

4. **Permission Management**
   - View: User kann sehen
   - Edit: User kann bearbeiten
   - Delete: User kann löschen
   - Assign: User kann zuweisen

5. **Activity Tracking**
   - Wer hat wann was zugewiesen
   - Änderungshistorie
   - Audit Log

#### Backend API Endpoints (NEU - MUSS IMPLEMENTIERT WERDEN)

```http
POST /api/admin/users/{user_id}/assign-campaigns
```

**Request Body:**
```json
{
  "campaign_ids": ["uuid1", "uuid2"],
  "permissions": ["view", "edit"]
}
```

**Response:**
```json
{
  "success": true,
  "assignments_created": 2
}
```

```http
POST /api/admin/users/{user_id}/assign-contacts
```

**Request Body:**
```json
{
  "contact_ids": ["uuid1", "uuid2"],
  "assignment_mode": "manual"
}
```

**Response:**
```json
{
  "success": true,
  "assignments_created": 2
}
```

```http
GET /api/admin/users/{user_id}/assignments
```

**Response:**
```json
{
  "success": true,
  "data": {
    "campaigns": [
      {
        "campaign_id": "uuid",
        "campaign_name": "Campaign ABC",
        "assigned_at": "2025-10-10T10:00:00Z",
        "assigned_by": "admin@example.com",
        "permissions": ["view", "edit"]
      }
    ],
    "contacts": [
      {
        "contact_id": "uuid",
        "contact_email": "lead@example.com",
        "assigned_at": "2025-10-10T10:00:00Z",
        "assigned_by": "admin@example.com"
      }
    ]
  }
}
```

```http
POST /api/admin/campaigns/{campaign_id}/assign-users
```

**Request Body:**
```json
{
  "user_ids": ["uuid1", "uuid2"],
  "permissions": ["view", "edit"]
}
```

```http
DELETE /api/admin/users/{user_id}/assignments/{assignment_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Assignment removed"
}
```

```http
POST /api/admin/contacts/bulk-assign
```

**Request Body:**
```json
{
  "contact_ids": ["uuid1", "uuid2", "..."],
  "assignment_mode": "round_robin", // or "lead_score" or "manual"
  "user_ids": ["uuid1", "uuid2"] // only for manual mode
}
```

**Response:**
```json
{
  "success": true,
  "assignments_created": 50,
  "distribution": {
    "user1@example.com": 25,
    "user2@example.com": 25
  }
}
```

#### UI Mockup (Struktur)

```
┌────────────────────────────────────────────────────────────┐
│ 🎛️ Admin Dashboard > User Management                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────┐  ┌────────────────────────────┐  │
│  │ 👤 Users            │  │ 📊 Assignment Overview     │  │
│  │                     │  │                            │  │
│  │ • John Doe          │  │ Campaigns: 5               │  │
│  │   john@example.com  │  │ Contacts: 150              │  │
│  │   Role: Admin       │  │ Last Action: 2h ago        │  │
│  │   📋 5 campaigns    │  │                            │  │
│  │   👥 150 contacts   │  │ [View Details]             │  │
│  │   [View] [Edit]     │  │                            │  │
│  │                     │  └────────────────────────────┘  │
│  │ • Jane Smith        │                                  │
│  │   jane@example.com  │  ┌────────────────────────────┐  │
│  │   Role: Member      │  │ 🎯 Quick Actions           │  │
│  │   📋 3 campaigns    │  │                            │  │
│  │   👥 75 contacts    │  │ [Assign Campaign]          │  │
│  │   [View] [Edit]     │  │ [Assign Contacts]          │  │
│  │                     │  │ [Bulk Assignment]          │  │
│  └─────────────────────┘  │ [Auto-Rules Setup]         │  │
│                           └────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘

Assign Campaigns Modal:
┌────────────────────────────────────────┐
│ Assign Campaigns to John Doe           │
├────────────────────────────────────────┤
│                                        │
│ Available Campaigns:                   │
│ ☐ Campaign ABC                         │
│ ☐ Campaign XYZ                         │
│ ☑ Campaign 123 (already assigned)      │
│                                        │
│ Permissions:                           │
│ ☑ View  ☑ Edit  ☐ Delete  ☐ Assign    │
│                                        │
│         [Cancel]  [Assign Selected]    │
└────────────────────────────────────────┘
```

#### Database Schema

```sql
CREATE TABLE user_campaign_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '["view"]'::jsonb,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES "user"(id),
    UNIQUE(user_id, campaign_id)
);

CREATE TABLE user_contact_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contact(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES "user"(id),
    assignment_mode VARCHAR(50) DEFAULT 'manual', -- manual, round_robin, lead_score
    UNIQUE(user_id, contact_id)
);

CREATE TABLE assignment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_type VARCHAR(50) NOT NULL, -- campaign, contact
    assignment_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- assigned, unassigned, permissions_changed
    user_id UUID NOT NULL,
    performed_by UUID NOT NULL REFERENCES "user"(id),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_campaign_assignment_user ON user_campaign_assignment(user_id);
CREATE INDEX idx_user_campaign_assignment_campaign ON user_campaign_assignment(campaign_id);
CREATE INDEX idx_user_contact_assignment_user ON user_contact_assignment(user_id);
CREATE INDEX idx_user_contact_assignment_contact ON user_contact_assignment(contact_id);
CREATE INDEX idx_assignment_history_created_at ON assignment_history(created_at DESC);
```

---

### 3. ONBOARDING-LINK ERSTELLEN 🔗

**Priorität:** KRITISCH
**Status:** Backend API fehlt, UI fehlt komplett

#### Funktionale Requirements

Das Admin Dashboard MUSS eine Onboarding Management Seite haben mit:

1. **Link Generator**
   - Wähle Organization (für dedizierte Links)
   - Wähle Template (vorgefertigte Onboarding-Flows)
   - Setze Expiration Date
   - Custom Welcome Message
   - Generate Unique Token

2. **Active Links List**
   - Alle aktiven Onboarding Links
   - Status (active, expired, used, revoked)
   - Click Count
   - Created Date
   - Expires Date
   - Actions (Copy Link, Revoke, Edit, View Stats)

3. **Progress Tracking**
   - Wer hat den Link benutzt
   - Onboarding Completion Status
   - Step-by-Step Progress
   - Time to Complete

4. **Templates Management**
   - Create/Edit Onboarding Templates
   - Define Steps
   - Customize Messages
   - Set Required Fields

#### Backend API Endpoints (NEU - MUSS IMPLEMENTIERT WERDEN)

```http
POST /api/admin/onboarding/create-link
```

**Request Body:**
```json
{
  "organization_id": "uuid", // optional, null = shared workspace
  "template_id": "uuid", // optional
  "welcome_message": "Welcome to Salesbrain!",
  "expires_at": "2025-12-31T23:59:59Z", // optional
  "max_uses": 1 // optional, null = unlimited
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "link_token": "abc123xyz",
    "full_url": "https://onboarding.salesbrain.com/start/abc123xyz",
    "expires_at": "2025-12-31T23:59:59Z",
    "created_at": "2025-10-10T14:00:00Z"
  }
}
```

```http
GET /api/admin/onboarding/links
```

**Query Parameters:**
- `status` (string, optional) - Filter: active, expired, used, revoked
- `organization_id` (uuid, optional)
- `limit` (int, default: 50)
- `offset` (int, default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "links": [
      {
        "id": "uuid",
        "link_token": "abc123xyz",
        "full_url": "https://onboarding.salesbrain.com/start/abc123xyz",
        "organization_id": "uuid",
        "organization_name": "ACME Corp",
        "template_id": "uuid",
        "template_name": "Standard Onboarding",
        "welcome_message": "Welcome!",
        "status": "active",
        "clicks_count": 5,
        "max_uses": 1,
        "times_used": 0,
        "expires_at": "2025-12-31T23:59:59Z",
        "created_at": "2025-10-10T14:00:00Z",
        "created_by": "admin@example.com"
      }
    ],
    "total": 25
  }
}
```

```http
POST /api/admin/onboarding/link/{link_id}/revoke
```

**Response:**
```json
{
  "success": true,
  "message": "Link revoked successfully"
}
```

```http
GET /api/admin/onboarding/link/{link_id}/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "clicks_count": 15,
    "times_used": 3,
    "completion_rate": 66.67,
    "average_completion_time": "00:45:30",
    "users_onboarded": [
      {
        "user_id": "uuid",
        "email": "user@example.com",
        "started_at": "2025-10-10T10:00:00Z",
        "completed_at": "2025-10-10T10:45:30Z",
        "completion_percentage": 100
      }
    ]
  }
}
```

```http
GET /api/admin/onboarding/templates
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Standard Onboarding",
      "description": "Default onboarding flow",
      "steps": [
        {
          "order": 1,
          "title": "Welcome",
          "description": "Introduction",
          "required": true
        },
        {
          "order": 2,
          "title": "Setup Profile",
          "description": "Complete your profile",
          "required": true
        }
      ],
      "estimated_time": "00:30:00"
    }
  ]
}
```

```http
POST /api/admin/onboarding/templates
```

**Request Body:**
```json
{
  "name": "Custom Onboarding",
  "description": "Custom flow for enterprise",
  "steps": [
    {
      "order": 1,
      "title": "Step 1",
      "description": "Description",
      "required": true
    }
  ]
}
```

#### UI Mockup (Struktur)

```
┌────────────────────────────────────────────────────────────┐
│ 🎛️ Admin Dashboard > Onboarding Management                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🔗 Create New Onboarding Link                      │   │
│  │                                                    │   │
│  │ Organization: [Select Organization ▼]             │   │
│  │ Template: [Standard Onboarding ▼]                 │   │
│  │ Welcome Message:                                  │   │
│  │ ┌──────────────────────────────────────────────┐  │   │
│  │ │ Welcome to Salesbrain! Let's get started...  │  │   │
│  │ └──────────────────────────────────────────────┘  │   │
│  │ Expires: [2025-12-31] Max Uses: [1]              │   │
│  │                                                    │   │
│  │              [Generate Link]                       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Active Links:                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🟢 abc123xyz | ACME Corp | Clicks: 5 | Used: 0/1    │ │
│  │    Created: 2h ago | Expires: Dec 31, 2025          │ │
│  │    [📋 Copy] [👁️ Stats] [🚫 Revoke]                 │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ 🟡 def456uvw | Beta Inc | Clicks: 12 | Used: 1/1    │ │
│  │    Created: 1 day ago | Expires: Dec 31, 2025       │ │
│  │    [📋 Copy] [👁️ Stats] [🚫 Revoke]                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [Manage Templates] [View All Links] [Export Report]      │
└────────────────────────────────────────────────────────────┘
```

#### Database Schema

```sql
CREATE TABLE onboarding_link (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_token VARCHAR(100) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organization(id), -- null = shared workspace
    template_id UUID REFERENCES onboarding_template(id),
    welcome_message TEXT,
    status VARCHAR(20) DEFAULT 'active', -- active, expired, used, revoked
    clicks_count INT DEFAULT 0,
    max_uses INT, -- null = unlimited
    times_used INT DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES "user"(id),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES "user"(id)
);

CREATE TABLE onboarding_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    estimated_time INTERVAL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL REFERENCES onboarding_link(id),
    user_id UUID NOT NULL REFERENCES "user"(id),
    current_step INT DEFAULT 0,
    total_steps INT NOT NULL,
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    data JSONB -- step-specific data
);

CREATE TABLE onboarding_link_clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL REFERENCES onboarding_link(id),
    ip_address INET,
    user_agent TEXT,
    clicked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_onboarding_link_token ON onboarding_link(link_token);
CREATE INDEX idx_onboarding_link_status ON onboarding_link(status);
CREATE INDEX idx_onboarding_link_organization ON onboarding_link(organization_id);
CREATE INDEX idx_onboarding_progress_user ON onboarding_progress(user_id);
CREATE INDEX idx_onboarding_link_clicks_link ON onboarding_link_clicks(link_id);
```

---

## 🔐 Authentication & Authorization

### Admin Roles

Das System MUSS folgende Rollen unterstützen:

1. **sb_admin** (Salesbrain Admin)
   - Vollzugriff auf ALLE Organisationen
   - Kann User Assignment verwalten
   - Kann Webhook Logs sehen (alle)
   - Kann Onboarding Links erstellen

2. **sb_operator** (Salesbrain Operator)
   - Lesezugriff auf alle Organisationen
   - Kann User Assignment sehen (nicht ändern)
   - Kann Webhook Logs sehen (alle)
   - Kann Onboarding Links sehen (nicht erstellen)

3. **owner** (Organization Owner)
   - Vollzugriff auf eigene Organisation
   - Kann User Assignment verwalten (nur eigene Org)
   - Kann Webhook Logs sehen (nur eigene Org)
   - Kann Onboarding Links erstellen (nur eigene Org)

4. **admin** (Organization Admin)
   - Wie Owner, aber kann keine kritischen Settings ändern

5. **member** (Organization Member)
   - Lesezugriff auf zugewiesene Ressourcen
   - Kann keine User Assignments machen
   - Kann keine Webhook Logs sehen
   - Kann keine Onboarding Links erstellen

### JWT Token Structure

```json
{
  "user_id": "uuid",
  "email": "admin@example.com",
  "organization_id": "uuid",
  "role": "sb_admin",
  "permissions": ["admin.view_all", "admin.manage_users", "admin.webhooks"],
  "exp": 1234567890
}
```

### Backend Authentication Check

Alle `/api/admin/*` Endpoints MÜSSEN prüfen:

```python
if user_role not in ["sb_admin", "sb_operator", "owner", "admin"]:
    raise HTTPException(status_code=403, detail="Admin access required")
```

---

## 📊 Dashboard Overview (Hauptseite)

### Layout

```
┌────────────────────────────────────────────────────────────┐
│ 🎛️ Salesbrain Admin Dashboard                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Statistics Cards (Top Row):                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ 📊 Campaigns│ │ 👥 Contacts │ │ 📨 Messages │         │
│  │    125      │ │   15,234    │ │   45,678    │         │
│  │ +12 today   │ │ +234 today  │ │ +1,234 tod. │         │
│  └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ 🔗 Webhooks │ │ ⚡ API Calls│ │ 👤 Users    │         │
│  │   1,234     │ │   98,765    │ │    45       │         │
│  │ 15/sec avg  │ │ Healthy ✓   │ │ 3 active    │         │
│  └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                            │
│  Recent Activity:                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🟢 Webhook received: email_sent (2 min ago)          │ │
│  │ 🟡 Campaign started: Q4 Outreach (5 min ago)         │ │
│  │ 👤 New user assigned to Campaign ABC (10 min ago)    │ │
│  │ 🔗 Onboarding link created for ACME Corp (1h ago)    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Quick Actions:                                            │
│  [📊 View Webhook Logs] [👥 Manage Users]                 │
│  [🔗 Create Onboarding Link] [📈 View Analytics]          │
└────────────────────────────────────────────────────────────┘
```

### Backend API Endpoint

```http
GET /api/admin/dashboard/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "campaigns": {
      "total": 125,
      "today": 12,
      "active": 45
    },
    "contacts": {
      "total": 15234,
      "today": 234,
      "lead_score_avg": 65.5
    },
    "messages": {
      "total": 45678,
      "today": 1234,
      "open_rate": 45.2,
      "reply_rate": 12.3
    },
    "webhooks": {
      "total": 1234,
      "avg_per_second": 15,
      "failed_last_hour": 3
    },
    "api_calls": {
      "total": 98765,
      "status": "healthy",
      "avg_response_time": 120
    },
    "users": {
      "total": 45,
      "active_now": 3
    }
  }
}
```

```http
GET /api/admin/dashboard/recent-activity
```

**Query Parameters:**
- `limit` (int, default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "type": "webhook",
      "event_type": "email_sent",
      "description": "Webhook received: email_sent",
      "timestamp": "2025-10-10T14:28:00Z"
    },
    {
      "type": "campaign",
      "action": "started",
      "description": "Campaign started: Q4 Outreach",
      "timestamp": "2025-10-10T14:25:00Z"
    }
  ]
}
```

---

## 🎨 UI/UX Guidelines

### Design System

- **Framework:** React + Tailwind CSS (basierend auf aktuellem Frontend)
- **Component Library:** shadcn/ui oder ähnlich
- **Icons:** Lucide React
- **Colors:**
  - Success: Green (#10B981)
  - Warning: Yellow (#F59E0B)
  - Error: Red (#EF4444)
  - Info: Blue (#3B82F6)
  - Admin: Purple (#8B5CF6)

### Responsive Design

- Desktop-First (Admin Dashboard wird primär am Desktop benutzt)
- Minimum Width: 1280px
- Tablet Support (1024px+)
- Mobile Support optional (kann Fehlermeldung zeigen: "Please use desktop")

### Loading States

Alle API-Calls MÜSSEN Loading States haben:
- Skeleton Loaders für Listen
- Spinner für Actions
- Toast Notifications für Erfolg/Fehler

### Error Handling

- Toast Notifications für Fehler
- Inline Validation für Forms
- Fallback UI bei API-Fehlern
- Retry-Button bei gescheiterten Requests

---

## 🔗 API Base URLs

### Development
```
Backend API: http://localhost:8001
Frontend: http://localhost:3000
```

### Production
```
Backend API: https://api.salesbrain.com
Frontend: https://app.salesbrain.com
Onboarding: https://onboarding.salesbrain.com
```

---

## 📋 Implementation Checklist

### Phase 3.1: Webhook Logs (Week 1-2)

- [ ] Backend: Implementiere `webhook_log` Tabelle
- [ ] Backend: Implementiere GET `/api/admin/webhooks/logs`
- [ ] Backend: Implementiere POST `/api/admin/webhooks/logs/{id}/retry`
- [ ] Backend: Implementiere DELETE `/api/admin/webhooks/logs/cleanup`
- [ ] Backend: Update Webhook Receiver um Logs zu schreiben
- [ ] Frontend: Erstelle Webhook Logs Seite
- [ ] Frontend: Implementiere Filter & Search
- [ ] Frontend: Implementiere Real-time Updates (polling oder WebSocket)
- [ ] Frontend: Implementiere JSON Payload Viewer (Modal)
- [ ] Frontend: Implementiere Export (CSV/JSON)
- [ ] Testing: Unit Tests für Backend
- [ ] Testing: Integration Tests
- [ ] Testing: UI Tests mit echten Webhooks

### Phase 3.2: User Assignment (Week 3-4)

- [ ] Backend: Implementiere `user_campaign_assignment` Tabelle
- [ ] Backend: Implementiere `user_contact_assignment` Tabelle
- [ ] Backend: Implementiere `assignment_history` Tabelle
- [ ] Backend: Implementiere POST `/api/admin/users/{id}/assign-campaigns`
- [ ] Backend: Implementiere POST `/api/admin/users/{id}/assign-contacts`
- [ ] Backend: Implementiere GET `/api/admin/users/{id}/assignments`
- [ ] Backend: Implementiere POST `/api/admin/contacts/bulk-assign`
- [ ] Backend: Implementiere Round-Robin Assignment Logic
- [ ] Backend: Implementiere Lead Score Based Assignment Logic
- [ ] Frontend: Erstelle User Management Seite
- [ ] Frontend: Implementiere Campaign Assignment UI (Drag & Drop optional)
- [ ] Frontend: Implementiere Contact Assignment UI
- [ ] Frontend: Implementiere Bulk Assignment Modal
- [ ] Frontend: Implementiere Assignment History Viewer
- [ ] Testing: Unit Tests für Assignment Logic
- [ ] Testing: Integration Tests mit Multiple Users
- [ ] Testing: UI Tests

### Phase 3.3: Onboarding Links (Week 5-6)

- [ ] Backend: Implementiere `onboarding_link` Tabelle
- [ ] Backend: Implementiere `onboarding_template` Tabelle
- [ ] Backend: Implementiere `onboarding_progress` Tabelle
- [ ] Backend: Implementiere `onboarding_link_clicks` Tabelle
- [ ] Backend: Implementiere POST `/api/admin/onboarding/create-link`
- [ ] Backend: Implementiere GET `/api/admin/onboarding/links`
- [ ] Backend: Implementiere POST `/api/admin/onboarding/link/{id}/revoke`
- [ ] Backend: Implementiere GET `/api/admin/onboarding/link/{id}/stats`
- [ ] Backend: Implementiere GET/POST `/api/admin/onboarding/templates`
- [ ] Backend: Implementiere Token Generation (secure random)
- [ ] Backend: Implementiere Link Expiration Check
- [ ] Frontend: Erstelle Onboarding Management Seite
- [ ] Frontend: Implementiere Link Generator UI
- [ ] Frontend: Implementiere Active Links List
- [ ] Frontend: Implementiere Link Stats Viewer
- [ ] Frontend: Implementiere Template Manager
- [ ] Frontend: Implementiere Copy Link Functionality
- [ ] Testing: Unit Tests
- [ ] Testing: Integration Tests
- [ ] Testing: End-to-End Tests mit Onboarding Flow

### Phase 3.4: Dashboard Overview (Week 7)

- [ ] Backend: Implementiere GET `/api/admin/dashboard/stats`
- [ ] Backend: Implementiere GET `/api/admin/dashboard/recent-activity`
- [ ] Frontend: Erstelle Dashboard Hauptseite
- [ ] Frontend: Implementiere Statistics Cards
- [ ] Frontend: Implementiere Recent Activity Feed
- [ ] Frontend: Implementiere Quick Actions
- [ ] Frontend: Implementiere Auto-Refresh
- [ ] Testing: Unit Tests
- [ ] Testing: UI Tests
- [ ] Testing: Performance Tests (Dashboard muss schnell laden)

---

## 🚀 Deployment Notes

### Environment Variables

```bash
# Backend (.env)
INSTANTLY_API_KEY=your_api_key_here
DATABASE_TENANT_URL=postgresql://user:pass@host:5433/tenant_db
DATABASE_GLOBAL_URL=postgresql://user:pass@host:5432/global_kb
JWT_SECRET_KEY=your_secret_key_here
FRONTEND_URL=http://localhost:3000
ONBOARDING_URL=https://onboarding.salesbrain.com
```

### CORS Configuration

Backend MUSS folgende Origins erlauben:
- `http://localhost:3000` (dev)
- `https://app.salesbrain.com` (prod)
- `https://onboarding.salesbrain.com` (prod)

### Database Migrations

Alle neuen Tabellen MÜSSEN via Migration erstellt werden:
- `migrations/versions/XXX_add_webhook_logs.py`
- `migrations/versions/XXX_add_user_assignments.py`
- `migrations/versions/XXX_add_onboarding_links.py`

### Performance

- Webhook Logs: Index auf `created_at DESC` für schnelle Abfragen
- User Assignments: Index auf `user_id` und `campaign_id`
- Onboarding Links: Index auf `link_token` für schnellen Lookup
- Dashboard Stats: Consider caching (Redis) für aggregierte Stats

---

## 📞 Support & Contact

Bei Fragen zur Implementierung:
- **Backend Lead:** Ivan (Salesbrain)
- **Documentation:** MASTER_PLAN.md
- **Repository:** https://github.com/Civandigi/salesbrain-backend

---

**Version:** 1.0.0
**Letzte Aktualisierung:** 2025-10-10
**Status:** Ready for Implementation

---

**🎯 Ziel:** Diese Requirements sollen dem Frontend-Team alle nötigen Informationen geben, um das Admin Dashboard zu implementieren, ohne dass weitere Backend-Spezifikationen nötig sind. Alle API Endpoints sind dokumentiert, alle Datenstrukturen sind definiert, alle UI Mockups sind vorhanden.
