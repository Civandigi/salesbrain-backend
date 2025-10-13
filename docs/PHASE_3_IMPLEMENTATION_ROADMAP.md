# 🚀 PHASE 3 IMPLEMENTATION ROADMAP
## 100% Frontend Integration Ready

> **Created:** 2025-10-12
> **Status:** Active Development
> **Goal:** Ensure ALL backend APIs are ready for seamless frontend integration

---

## 📊 CURRENT STATUS OVERVIEW

### What's Been Done (Phase 1 & 2)
- ✅ **Phase 1:** Database Setup (100%)
- ✅ **Phase 2:** Instantly Integration (100%)
- ✅ **Webhook Logs Database:** Table created with 9 indexes + RLS policies
- ✅ **Webhook Logs Service:** Complete CRUD operations (358 lines)
- ✅ **Webhook Logs Admin API:** 3/5 endpoints implemented (474 lines)
- ✅ **Webhook Receiver:** Auto-logging all events to database

### Current Implementation Status

#### 1. WEBHOOK LOGS & MONITORING
**Backend Status:** 80% Complete ✅ → 20% Remaining ⚠️

**✅ Completed:**
- Database table `webhook_log` with full schema
- RLS policies for multi-tenant isolation
- Service layer with filtering, search, pagination
- 3 core API endpoints:
  - `GET /api/admin/webhooks/logs` (with filters)
  - `POST /api/admin/webhooks/logs/{id}/retry`
  - `DELETE /api/admin/webhooks/logs/cleanup`
- Additional endpoints:
  - `GET /api/admin/webhooks/logs/{id}` (detail view)
  - `GET /api/admin/webhooks/stats` (statistics)
  - `GET /api/admin/dashboard/stats` (overall dashboard)
  - `GET /api/admin/dashboard/recent-activity` (activity feed)

**⚠️ Missing (Frontend Expects These):**
- Bulk retry endpoint: `POST /api/admin/webhooks/logs/bulk-retry`
- Campaign filter API: `GET /api/admin/campaigns/filter`
- 4 missing event types (13 implemented, 17 expected)
- 7 additional webhook sources (only 'instantly' supported)
- Export functionality (CSV/JSON)

**Frontend Status:** 100% Complete ✅
- UI fully built: `app/admin-portal/webhooks/page.tsx` (545 lines)
- Real-time auto-refresh (5 second interval)
- Advanced filtering and search
- Actions: View, Retry, Bulk Retry, Cleanup, Export

#### 2. USER ASSIGNMENT & ZUWEISUNGEN
**Backend Status:** 0% Complete ❌
**Frontend Status:** 0% Complete ❌ (NOT YET BUILT)

**Required Components:**
- Database tables:
  - `user_campaign_assignment`
  - `user_contact_assignment`
- 5 Backend API endpoints
- Assignment logic (round-robin, lead-score-based)
- Permission management

#### 3. ONBOARDING LINKS GENERATOR
**Backend Status:** 0% Complete ❌
**Frontend Status:** 0% Complete ❌ (NOT READY - User confirmed)

**Required Components:**
- Database table: `onboarding_link`
- 5 Backend API endpoints
- Token generation logic
- Expiration & tracking mechanism
- Integration with onboarding platform

---

## 🎯 IMPLEMENTATION PLAN

### PART 1: WEBHOOK LOGS COMPLETION (Priority: CRITICAL)
**Estimated Time:** 2-3 hours
**Goal:** 100% frontend-backend compatibility

#### Task 1.1: Add Missing Event Types
**File:** `app/integrations/instantly/schemas.py`

```python
# Add these 4 missing event types to InstantlyEventType enum:
class InstantlyEventType(str, Enum):
    # ... existing 13 types ...

    # NEW - Missing from backend:
    LEAD_MEETING_CANCELLED = "lead.meeting_cancelled"
    LEAD_INTERESTED_MAYBE = "lead.interested_maybe"
    CAMPAIGN_STARTED = "campaign.started"
    ACCOUNT_WARNING = "account.warning"
```

**Reasoning:** Frontend expects 17 event types. Backend only has 13. Need to add 4 more.

---

#### Task 1.2: Extend Webhook Sources Support
**File:** `app/services/webhook_log_service.py`

**Current:** Only supports `event_source="instantly"`

**Frontend Expects 8 Sources:**
1. instantly ✅
2. weconnect (planned Phase 4)
3. n8n (planned)
4. zapier (planned)
5. make (planned)
6. custom (planned)
7. manual (for manual entries)
8. system (for system-generated events)

**Action:** Update database schema to VARCHAR(50) (already done ✅) and document future sources.

---

#### Task 1.3: Add Bulk Retry Endpoint
**File:** `app/api/admin.py`

```python
@router.post("/webhooks/logs/bulk-retry", status_code=status.HTTP_200_OK)
async def bulk_retry_failed_webhooks(
    log_ids: List[UUID] = Body(..., description="List of webhook log IDs to retry")
):
    """
    Retry multiple failed webhooks at once.

    **Admin Only**

    **Args:**
    - log_ids: Array of webhook log UUIDs

    **Returns:**
    - success_count: Number of webhooks queued for retry
    - failed_count: Number of webhooks that couldn't be retried
    """
    success_count = 0
    failed_count = 0

    for log_id in log_ids:
        success = await webhook_log_service.retry_webhook_log(log_id)
        if success:
            success_count += 1
        else:
            failed_count += 1

    return {
        "success": True,
        "success_count": success_count,
        "failed_count": failed_count,
        "message": f"Queued {success_count} webhooks for retry, {failed_count} failed"
    }
```

**Frontend Usage:** `app/admin-portal/webhooks/page.tsx:312`
```typescript
// Bulk retry selected failed webhooks
const handleBulkRetry = async () => {
  const response = await fetch('/api/admin/webhooks/logs/bulk-retry', {
    method: 'POST',
    body: JSON.stringify({ log_ids: selectedLogs }),
    headers: { 'Content-Type': 'application/json' }
  })
}
```

---

#### Task 1.4: Add Campaign Filter Endpoint
**File:** `app/api/admin.py`

```python
@router.get("/campaigns/filter", status_code=status.HTTP_200_OK)
async def get_campaigns_for_filter(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search campaign names"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get campaigns for dropdown filters (lightweight).

    Returns only id, name, status for UI dropdowns.

    **Returns:**
    - List of campaigns with minimal data
    """
    from app.core import db

    where_clauses = []
    params = []
    param_count = 0

    if organization_id:
        param_count += 1
        where_clauses.append(f"organization_id = ${param_count}")
        params.append(organization_id)

    if search:
        param_count += 1
        where_clauses.append(f"name ILIKE ${param_count}")
        params.append(f"%{search}%")

    if status:
        param_count += 1
        where_clauses.append(f"status = ${param_count}")
        params.append(status)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    async with db.tenant_db_pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT id, name, status, organization_id
            FROM campaign
            {where_sql}
            ORDER BY name ASC
            LIMIT 100
        """, *params)

    campaigns = [dict(row) for row in rows]

    return {
        "success": True,
        "data": campaigns
    }
```

**Frontend Usage:** `lib/api/admin-webhooks.ts:67`
```typescript
// Load campaigns for filter dropdown
export async function getCampaignsFilter() {
  const response = await fetch('/api/admin/campaigns/filter')
  return response.json()
}
```

---

#### Task 1.5: Add Export Functionality
**File:** `app/api/admin.py`

```python
from fastapi.responses import StreamingResponse
import csv
import json
from io import StringIO

@router.get("/webhooks/logs/export", status_code=status.HTTP_200_OK)
async def export_webhook_logs(
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    event_type: Optional[str] = Query(None),
    campaign_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """
    Export webhook logs to CSV or JSON.

    **Admin Only**

    **Formats:**
    - csv: Comma-separated values
    - json: JSON array

    **Returns:**
    - File download with appropriate content-type
    """
    # Get logs with same filters
    result = await webhook_log_service.get_webhook_logs(
        limit=10000,  # Max export limit
        offset=0,
        event_type=event_type,
        campaign_id=campaign_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        user_role="sb_admin"  # Admin export sees all
    )

    logs = result["logs"]

    if format == "csv":
        # Generate CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id", "event_type", "event_source", "campaign_name",
            "contact_email", "status", "error_message", "created_at"
        ])
        writer.writeheader()

        for log in logs:
            writer.writerow({
                "id": str(log["id"]),
                "event_type": log["event_type"],
                "event_source": log["event_source"],
                "campaign_name": log.get("campaign_name", ""),
                "contact_email": log.get("contact_email", ""),
                "status": log["status"],
                "error_message": log.get("error_message", ""),
                "created_at": log["created_at"].isoformat()
            })

        content = output.getvalue()

        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=webhook_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

    else:  # json
        # Generate JSON
        # Convert datetime objects to strings
        for log in logs:
            log["created_at"] = log["created_at"].isoformat()
            if log.get("processed_at"):
                log["processed_at"] = log["processed_at"].isoformat()
            if log.get("last_retry_at"):
                log["last_retry_at"] = log["last_retry_at"].isoformat()

        content = json.dumps(logs, indent=2)

        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=webhook_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
```

**Frontend Usage:** `app/admin-portal/webhooks/page.tsx:345`
```typescript
// Export logs as CSV or JSON
const handleExport = async (format: 'csv' | 'json') => {
  const queryParams = new URLSearchParams({
    format,
    ...(filters.eventType && { event_type: filters.eventType }),
    ...(filters.status && { status: filters.status })
  })

  window.open(`/api/admin/webhooks/logs/export?${queryParams}`, '_blank')
}
```

---

#### Task 1.6: Update Webhook Receiver for New Event Types
**File:** `app/integrations/instantly/webhooks.py`

Add handlers for the 4 new event types in the routing logic:

```python
async def _route_webhook_event(payload: InstantlyWebhookPayload) -> dict:
    """Route webhook event to appropriate handler"""
    event_type = payload.event_type

    # ... existing handlers ...

    # NEW: Handle additional event types
    elif event_type == InstantlyEventType.LEAD_MEETING_CANCELLED:
        return await _handle_meeting_cancelled(payload)

    elif event_type == InstantlyEventType.LEAD_INTERESTED_MAYBE:
        return await _handle_lead_status_event(payload)

    elif event_type == InstantlyEventType.CAMPAIGN_STARTED:
        return await _handle_campaign_started(payload)

    elif event_type == InstantlyEventType.ACCOUNT_WARNING:
        return await _handle_account_warning(payload)
```

---

### PART 2: USER ASSIGNMENT SYSTEM (Priority: HIGH)
**Estimated Time:** 1-2 days
**Goal:** Complete backend API for user-campaign and user-contact assignments

#### Task 2.1: Create Database Tables

**File:** `sql/migration_phase3_user_assignments.sql`

```sql
-- ============================================
-- PHASE 3: USER ASSIGNMENT SYSTEM
-- ============================================
-- Migration Script for User Assignment Features
-- Created: 2025-10-12

-- ============================================
-- 1. USER CAMPAIGN ASSIGNMENT TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS user_campaign_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

    -- Assignment Details
    assigned_by UUID REFERENCES "user"(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member, viewer

    -- Permissions
    can_edit BOOLEAN DEFAULT false,
    can_view_stats BOOLEAN DEFAULT true,
    can_manage_contacts BOOLEAN DEFAULT false,

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, revoked

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, campaign_id)
);

-- Indexes
CREATE INDEX idx_user_campaign_user ON user_campaign_assignment(user_id);
CREATE INDEX idx_user_campaign_campaign ON user_campaign_assignment(campaign_id);
CREATE INDEX idx_user_campaign_org ON user_campaign_assignment(organization_id);
CREATE INDEX idx_user_campaign_status ON user_campaign_assignment(status) WHERE status = 'active';

-- ============================================
-- 2. USER CONTACT ASSIGNMENT TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS user_contact_assignment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contact(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

    -- Assignment Details
    assigned_by UUID REFERENCES "user"(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assignment_type VARCHAR(50) DEFAULT 'manual', -- manual, round_robin, lead_score, territory

    -- Lead Ownership
    is_primary_owner BOOLEAN DEFAULT true,
    ownership_percentage INT DEFAULT 100, -- For split ownership

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, transferred

    -- Performance Tracking
    last_contacted_at TIMESTAMPTZ,
    next_followup_at TIMESTAMPTZ,
    interactions_count INT DEFAULT 0,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, contact_id)
);

-- Indexes
CREATE INDEX idx_user_contact_user ON user_contact_assignment(user_id);
CREATE INDEX idx_user_contact_contact ON user_contact_assignment(contact_id);
CREATE INDEX idx_user_contact_org ON user_contact_assignment(organization_id);
CREATE INDEX idx_user_contact_status ON user_contact_assignment(status) WHERE status = 'active';
CREATE INDEX idx_user_contact_next_followup ON user_contact_assignment(next_followup_at) WHERE next_followup_at IS NOT NULL;

-- ============================================
-- 3. ROW-LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE user_campaign_assignment ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_contact_assignment ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can see all assignments
CREATE POLICY user_campaign_admin_all ON user_campaign_assignment
    FOR ALL TO PUBLIC
    USING (current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator'));

CREATE POLICY user_contact_admin_all ON user_contact_assignment
    FOR ALL TO PUBLIC
    USING (current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator'));

-- Policy: Users can see their organization's assignments
CREATE POLICY user_campaign_org_select ON user_campaign_assignment
    FOR SELECT TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('owner', 'admin', 'member')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

CREATE POLICY user_contact_org_select ON user_contact_assignment
    FOR SELECT TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('owner', 'admin', 'member')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

-- Policy: Admins/Owners can manage assignments
CREATE POLICY user_campaign_admin_manage ON user_campaign_assignment
    FOR ALL TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator', 'owner', 'admin')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

CREATE POLICY user_contact_admin_manage ON user_contact_assignment
    FOR ALL TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator', 'owner', 'admin')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

-- ============================================
-- 4. HELPER FUNCTIONS
-- ============================================

-- Function: Get user's campaign count
CREATE OR REPLACE FUNCTION get_user_campaign_count(p_user_id UUID)
RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM user_campaign_assignment
        WHERE user_id = p_user_id AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql;

-- Function: Get user's contact count
CREATE OR REPLACE FUNCTION get_user_contact_count(p_user_id UUID)
RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM user_contact_assignment
        WHERE user_id = p_user_id AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql;

-- Function: Round-robin assignment (get user with fewest contacts)
CREATE OR REPLACE FUNCTION get_next_user_round_robin(p_organization_id UUID)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT u.id INTO v_user_id
    FROM "user" u
    LEFT JOIN user_contact_assignment uca ON u.id = uca.user_id AND uca.status = 'active'
    WHERE u.organization_id = p_organization_id
      AND u.status = 'active'
      AND u.role IN ('member', 'admin', 'owner')
    GROUP BY u.id
    ORDER BY COUNT(uca.id) ASC, RANDOM()
    LIMIT 1;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'user_campaign_assignment') THEN
        RAISE NOTICE '✅ user_campaign_assignment table created successfully';
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'user_contact_assignment') THEN
        RAISE NOTICE '✅ user_contact_assignment table created successfully';
    END IF;

    RAISE NOTICE '✅ Phase 3 User Assignment migration completed';
    RAISE NOTICE 'ℹ️  Total indexes created: 8';
    RAISE NOTICE 'ℹ️  RLS policies created: 6';
    RAISE NOTICE 'ℹ️  Functions created: 3';
END $$;
```

---

#### Task 2.2: Create User Assignment Service

**File:** `app/services/user_assignment_service.py`

```python
"""
User Assignment Service

Handles user-campaign and user-contact assignments.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.core import db


async def assign_user_to_campaigns(
    user_id: UUID,
    campaign_ids: List[UUID],
    assigned_by: UUID,
    organization_id: UUID,
    role: str = "member",
    can_edit: bool = False,
    can_view_stats: bool = True,
    can_manage_contacts: bool = False
) -> Dict[str, Any]:
    """
    Assign a user to multiple campaigns.

    Args:
        user_id: User UUID to assign
        campaign_ids: List of campaign UUIDs
        assigned_by: User UUID who is making the assignment
        organization_id: Organization UUID
        role: User role in campaigns (owner, admin, member, viewer)
        can_edit: Permission to edit campaigns
        can_view_stats: Permission to view statistics
        can_manage_contacts: Permission to manage contacts

    Returns:
        Dict with success count and failed campaigns
    """
    success_count = 0
    failed_campaigns = []

    async with db.tenant_db_pool.acquire() as conn:
        for campaign_id in campaign_ids:
            try:
                await conn.execute(
                    """
                    INSERT INTO user_campaign_assignment (
                        user_id, campaign_id, organization_id, assigned_by,
                        role, can_edit, can_view_stats, can_manage_contacts,
                        status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
                    ON CONFLICT (user_id, campaign_id)
                    DO UPDATE SET
                        role = EXCLUDED.role,
                        can_edit = EXCLUDED.can_edit,
                        can_view_stats = EXCLUDED.can_view_stats,
                        can_manage_contacts = EXCLUDED.can_manage_contacts,
                        status = 'active',
                        updated_at = NOW()
                    """,
                    user_id, campaign_id, organization_id, assigned_by,
                    role, can_edit, can_view_stats, can_manage_contacts
                )
                success_count += 1
            except Exception as e:
                failed_campaigns.append({
                    "campaign_id": str(campaign_id),
                    "error": str(e)
                })

    return {
        "success_count": success_count,
        "failed_count": len(failed_campaigns),
        "failed_campaigns": failed_campaigns
    }


async def assign_contacts_to_user(
    user_id: UUID,
    contact_ids: List[UUID],
    assigned_by: UUID,
    organization_id: UUID,
    assignment_type: str = "manual"
) -> Dict[str, Any]:
    """
    Assign multiple contacts to a user.

    Args:
        user_id: User UUID to assign contacts to
        contact_ids: List of contact UUIDs
        assigned_by: User UUID who is making the assignment
        organization_id: Organization UUID
        assignment_type: Type of assignment (manual, round_robin, lead_score, territory)

    Returns:
        Dict with success count and failed contacts
    """
    success_count = 0
    failed_contacts = []

    async with db.tenant_db_pool.acquire() as conn:
        for contact_id in contact_ids:
            try:
                await conn.execute(
                    """
                    INSERT INTO user_contact_assignment (
                        user_id, contact_id, organization_id, assigned_by,
                        assignment_type, is_primary_owner, status
                    ) VALUES ($1, $2, $3, $4, $5, true, 'active')
                    ON CONFLICT (user_id, contact_id)
                    DO UPDATE SET
                        assignment_type = EXCLUDED.assignment_type,
                        status = 'active',
                        updated_at = NOW()
                    """,
                    user_id, contact_id, organization_id, assigned_by,
                    assignment_type
                )
                success_count += 1
            except Exception as e:
                failed_contacts.append({
                    "contact_id": str(contact_id),
                    "error": str(e)
                })

    return {
        "success_count": success_count,
        "failed_count": len(failed_contacts),
        "failed_contacts": failed_contacts
    }


async def get_user_assignments(user_id: UUID) -> Dict[str, Any]:
    """
    Get all campaigns and contacts assigned to a user.

    Args:
        user_id: User UUID

    Returns:
        Dict with campaigns and contacts
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Get assigned campaigns
        campaigns = await conn.fetch(
            """
            SELECT
                uca.id as assignment_id,
                uca.campaign_id,
                c.name as campaign_name,
                c.status as campaign_status,
                uca.role,
                uca.can_edit,
                uca.can_view_stats,
                uca.can_manage_contacts,
                uca.assigned_at
            FROM user_campaign_assignment uca
            JOIN campaign c ON uca.campaign_id = c.id
            WHERE uca.user_id = $1 AND uca.status = 'active'
            ORDER BY uca.assigned_at DESC
            """,
            user_id
        )

        # Get assigned contacts
        contacts = await conn.fetch(
            """
            SELECT
                uca.id as assignment_id,
                uca.contact_id,
                ct.email as contact_email,
                ct.first_name,
                ct.last_name,
                ct.company,
                ct.lead_score,
                uca.assignment_type,
                uca.is_primary_owner,
                uca.last_contacted_at,
                uca.next_followup_at,
                uca.interactions_count,
                uca.assigned_at
            FROM user_contact_assignment uca
            JOIN contact ct ON uca.contact_id = ct.id
            WHERE uca.user_id = $1 AND uca.status = 'active'
            ORDER BY uca.assigned_at DESC
            """,
            user_id
        )

    return {
        "campaigns": [dict(row) for row in campaigns],
        "contacts": [dict(row) for row in contacts],
        "campaigns_count": len(campaigns),
        "contacts_count": len(contacts)
    }


async def get_organization_users_with_assignments(
    organization_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get all users in an organization with their assignment counts.

    Args:
        organization_id: Organization UUID

    Returns:
        List of users with assignment statistics
    """
    async with db.tenant_db_pool.acquire() as conn:
        users = await conn.fetch(
            """
            SELECT
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.status,
                u.created_at,
                get_user_campaign_count(u.id) as campaigns_count,
                get_user_contact_count(u.id) as contacts_count
            FROM "user" u
            WHERE u.organization_id = $1
            ORDER BY u.created_at DESC
            """,
            organization_id
        )

    return [dict(row) for row in users]


async def auto_assign_contact_round_robin(
    contact_id: UUID,
    organization_id: UUID,
    assigned_by: UUID
) -> Optional[UUID]:
    """
    Automatically assign a contact to the user with the fewest contacts (round-robin).

    Args:
        contact_id: Contact UUID to assign
        organization_id: Organization UUID
        assigned_by: User UUID who triggered the assignment

    Returns:
        User UUID who was assigned the contact, or None if no users available
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Get next user via round-robin function
        user_id = await conn.fetchval(
            """
            SELECT get_next_user_round_robin($1)
            """,
            organization_id
        )

        if not user_id:
            return None

        # Assign contact to user
        await conn.execute(
            """
            INSERT INTO user_contact_assignment (
                user_id, contact_id, organization_id, assigned_by,
                assignment_type, is_primary_owner, status
            ) VALUES ($1, $2, $3, $4, 'round_robin', true, 'active')
            ON CONFLICT (user_id, contact_id)
            DO UPDATE SET
                assignment_type = 'round_robin',
                status = 'active',
                updated_at = NOW()
            """,
            user_id, contact_id, organization_id, assigned_by
        )

    return user_id


async def remove_user_campaign_assignment(
    user_id: UUID,
    campaign_id: UUID
) -> bool:
    """
    Remove a user from a campaign (set status to inactive).

    Args:
        user_id: User UUID
        campaign_id: Campaign UUID

    Returns:
        True if removed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_campaign_assignment
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = $1 AND campaign_id = $2 AND status = 'active'
            """,
            user_id, campaign_id
        )

    return result != "UPDATE 0"


async def remove_user_contact_assignment(
    user_id: UUID,
    contact_id: UUID
) -> bool:
    """
    Remove a contact from a user (set status to inactive).

    Args:
        user_id: User UUID
        contact_id: Contact UUID

    Returns:
        True if removed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_contact_assignment
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = $1 AND contact_id = $2 AND status = 'active'
            """,
            user_id, contact_id
        )

    return result != "UPDATE 0"
```

---

#### Task 2.3: Create User Assignment API Endpoints

**File:** `app/api/user_assignments.py` (NEW)

```python
"""
User Assignment API Endpoints

Provides APIs for managing user-campaign and user-contact assignments.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel

from app.services import user_assignment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["User Assignments"])


# ========================================
# Request/Response Models
# ========================================

class AssignCampaignsRequest(BaseModel):
    """Request to assign user to campaigns"""
    campaign_ids: List[UUID]
    role: str = "member"
    can_edit: bool = False
    can_view_stats: bool = True
    can_manage_contacts: bool = False


class AssignContactsRequest(BaseModel):
    """Request to assign contacts to user"""
    contact_ids: List[UUID]
    assignment_type: str = "manual"


class AssignmentResponse(BaseModel):
    """Response from assignment operation"""
    success: bool
    success_count: int
    failed_count: int
    failed_items: List[dict]


# ========================================
# Endpoints
# ========================================

@router.get("/{user_id}/assignments", status_code=status.HTTP_200_OK)
async def get_user_assignments(user_id: UUID):
    """
    Get all campaigns and contacts assigned to a user.

    **Returns:**
    - campaigns: List of assigned campaigns with permissions
    - contacts: List of assigned contacts with metadata
    - counts: Total assignments
    """
    try:
        result = await user_assignment_service.get_user_assignments(user_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Failed to fetch user assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/assign-campaigns", status_code=status.HTTP_200_OK)
async def assign_user_to_campaigns(
    user_id: UUID,
    request: AssignCampaignsRequest,
    assigned_by: UUID = Body(..., embed=True),
    organization_id: UUID = Body(..., embed=True)
):
    """
    Assign a user to multiple campaigns.

    **Args:**
    - user_id: User UUID to assign
    - campaign_ids: List of campaign UUIDs
    - role: User role (owner, admin, member, viewer)
    - permissions: can_edit, can_view_stats, can_manage_contacts

    **Returns:**
    - success_count: Number of successful assignments
    - failed_count: Number of failed assignments
    """
    try:
        result = await user_assignment_service.assign_user_to_campaigns(
            user_id=user_id,
            campaign_ids=request.campaign_ids,
            assigned_by=assigned_by,
            organization_id=organization_id,
            role=request.role,
            can_edit=request.can_edit,
            can_view_stats=request.can_view_stats,
            can_manage_contacts=request.can_manage_contacts
        )

        return {
            "success": True,
            "success_count": result["success_count"],
            "failed_count": result["failed_count"],
            "failed_items": result["failed_campaigns"]
        }

    except Exception as e:
        logger.error(f"Failed to assign user to campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{user_id}/assign-contacts", status_code=status.HTTP_200_OK)
async def assign_contacts_to_user(
    user_id: UUID,
    request: AssignContactsRequest,
    assigned_by: UUID = Body(..., embed=True),
    organization_id: UUID = Body(..., embed=True)
):
    """
    Assign multiple contacts to a user.

    **Args:**
    - user_id: User UUID to assign contacts to
    - contact_ids: List of contact UUIDs
    - assignment_type: manual, round_robin, lead_score, territory

    **Returns:**
    - success_count: Number of successful assignments
    - failed_count: Number of failed assignments
    """
    try:
        result = await user_assignment_service.assign_contacts_to_user(
            user_id=user_id,
            contact_ids=request.contact_ids,
            assigned_by=assigned_by,
            organization_id=organization_id,
            assignment_type=request.assignment_type
        )

        return {
            "success": True,
            "success_count": result["success_count"],
            "failed_count": result["failed_count"],
            "failed_items": result["failed_contacts"]
        }

    except Exception as e:
        logger.error(f"Failed to assign contacts to user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_organization_users(
    organization_id: UUID
):
    """
    Get all users in an organization with assignment counts.

    **Returns:**
    - List of users with campaigns_count and contacts_count
    """
    try:
        users = await user_assignment_service.get_organization_users_with_assignments(
            organization_id
        )

        return {
            "success": True,
            "data": users
        }

    except Exception as e:
        logger.error(f"Failed to fetch organization users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/campaigns/{campaign_id}", status_code=status.HTTP_200_OK)
async def remove_user_from_campaign(
    user_id: UUID,
    campaign_id: UUID
):
    """
    Remove a user from a campaign.

    **Returns:**
    - success: True if removed
    """
    try:
        success = await user_assignment_service.remove_user_campaign_assignment(
            user_id, campaign_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already inactive"
            )

        return {
            "success": True,
            "message": "User removed from campaign"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove user from campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}/contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def remove_contact_from_user(
    user_id: UUID,
    contact_id: UUID
):
    """
    Remove a contact from a user.

    **Returns:**
    - success: True if removed
    """
    try:
        success = await user_assignment_service.remove_user_contact_assignment(
            user_id, contact_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or already inactive"
            )

        return {
            "success": True,
            "message": "Contact removed from user"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove contact from user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

#### Task 2.4: Register User Assignment Router

**File:** `app/main.py`

```python
from app.api.user_assignments import router as user_assignments_router

# Include routers
app.include_router(user_assignments_router)  # User Assignment API
```

---

### PART 3: ONBOARDING LINKS SYSTEM (Priority: MEDIUM)
**Estimated Time:** 1-2 days
**Goal:** Complete backend API for onboarding link generation and management

**⚠️ IMPORTANT:** User confirmed frontend is NOT ready yet for this feature.
**Strategy:** Build backend now, so when frontend is ready, integration is instant.

#### Task 3.1: Create Database Table

**File:** `sql/migration_phase3_onboarding_links.sql`

```sql
-- ============================================
-- PHASE 3: ONBOARDING LINKS SYSTEM
-- ============================================
-- Migration Script for Onboarding Link Generator
-- Created: 2025-10-12

-- ============================================
-- 1. ONBOARDING LINK TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS onboarding_link (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    created_by UUID REFERENCES "user"(id) ON DELETE SET NULL,

    -- Link Details
    link_token VARCHAR(100) UNIQUE NOT NULL, -- Unique, secure token
    link_url TEXT NOT NULL, -- Full URL (https://onboarding.salesbrain.com/o/{token})

    -- Template & Customization
    template_id UUID, -- Reference to onboarding template (future)
    template_name VARCHAR(100), -- Template name for quick reference
    welcome_message TEXT, -- Custom welcome message

    -- Status & Expiration
    status VARCHAR(20) DEFAULT 'active', -- active, expired, used, revoked
    expires_at TIMESTAMPTZ NOT NULL,

    -- Usage Tracking
    clicks_count INT DEFAULT 0,
    first_accessed_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ, -- When onboarding was completed

    -- Progress Tracking
    current_step INT DEFAULT 1, -- Current step in onboarding
    total_steps INT DEFAULT 5, -- Total steps in flow
    progress_percentage INT DEFAULT 0, -- 0-100

    -- Metadata
    ip_addresses JSONB DEFAULT '[]'::JSONB, -- Track IPs that accessed the link
    user_agents JSONB DEFAULT '[]'::JSONB, -- Track user agents

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES "user"(id) ON DELETE SET NULL,
    revoked_reason TEXT
);

-- ============================================
-- 2. INDEXES
-- ============================================

-- Primary lookup
CREATE UNIQUE INDEX idx_onboarding_link_token ON onboarding_link(link_token);

-- Organization queries
CREATE INDEX idx_onboarding_link_org ON onboarding_link(organization_id);

-- Status queries
CREATE INDEX idx_onboarding_link_status ON onboarding_link(status);
CREATE INDEX idx_onboarding_link_active ON onboarding_link(organization_id, status)
    WHERE status = 'active';

-- Expiration queries
CREATE INDEX idx_onboarding_link_expires ON onboarding_link(expires_at)
    WHERE status = 'active';

-- Created by queries
CREATE INDEX idx_onboarding_link_creator ON onboarding_link(created_by)
    WHERE created_by IS NOT NULL;

-- ============================================
-- 3. ROW-LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE onboarding_link ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can see all onboarding links
CREATE POLICY onboarding_link_admin_all ON onboarding_link
    FOR ALL TO PUBLIC
    USING (current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator'));

-- Policy: Users can see their organization's links
CREATE POLICY onboarding_link_org_select ON onboarding_link
    FOR SELECT TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('owner', 'admin', 'member')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

-- Policy: Admins/Owners can create/manage links
CREATE POLICY onboarding_link_admin_manage ON onboarding_link
    FOR ALL TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator', 'owner', 'admin')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

-- ============================================
-- 4. HELPER FUNCTIONS
-- ============================================

-- Function: Generate unique link token
CREATE OR REPLACE FUNCTION generate_onboarding_token()
RETURNS VARCHAR AS $$
DECLARE
    token VARCHAR;
    token_exists BOOLEAN;
BEGIN
    LOOP
        -- Generate random 32-character token
        token := encode(gen_random_bytes(24), 'base64');
        token := replace(replace(replace(token, '/', ''), '+', ''), '=', '');
        token := substring(token, 1, 32);

        -- Check if token exists
        SELECT EXISTS(SELECT 1 FROM onboarding_link WHERE link_token = token) INTO token_exists;

        -- Exit loop if unique
        EXIT WHEN NOT token_exists;
    END LOOP;

    RETURN token;
END;
$$ LANGUAGE plpgsql;

-- Function: Auto-expire old links
CREATE OR REPLACE FUNCTION expire_old_onboarding_links()
RETURNS INT AS $$
DECLARE
    expired_count INT;
BEGIN
    UPDATE onboarding_link
    SET status = 'expired', updated_at = NOW()
    WHERE status = 'active'
      AND expires_at < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;

    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Track link access
CREATE OR REPLACE FUNCTION track_onboarding_link_access(
    p_link_token VARCHAR,
    p_ip_address INET,
    p_user_agent TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE onboarding_link
    SET
        clicks_count = clicks_count + 1,
        first_accessed_at = COALESCE(first_accessed_at, NOW()),
        last_accessed_at = NOW(),
        ip_addresses = COALESCE(ip_addresses, '[]'::JSONB) || jsonb_build_object(
            'ip', p_ip_address::TEXT,
            'timestamp', NOW()
        ),
        user_agents = COALESCE(user_agents, '[]'::JSONB) || jsonb_build_object(
            'user_agent', p_user_agent,
            'timestamp', NOW()
        ),
        updated_at = NOW()
    WHERE link_token = p_link_token;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. SCHEDULED JOBS (Cron)
-- ============================================

-- Auto-expire links daily (if using pg_cron extension)
-- SELECT cron.schedule('expire_onboarding_links', '0 0 * * *', 'SELECT expire_old_onboarding_links()');

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'onboarding_link') THEN
        RAISE NOTICE '✅ onboarding_link table created successfully';
    END IF;

    RAISE NOTICE '✅ Phase 3 Onboarding Links migration completed';
    RAISE NOTICE 'ℹ️  Total indexes created: 6';
    RAISE NOTICE 'ℹ️  RLS policies created: 3';
    RAISE NOTICE 'ℹ️  Functions created: 3';
END $$;
```

---

#### Task 3.2: Create Onboarding Links Service

**File:** `app/services/onboarding_link_service.py`

```python
"""
Onboarding Link Service

Handles creation and management of onboarding links.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

from app.core import db


async def create_onboarding_link(
    organization_id: UUID,
    created_by: UUID,
    template_name: str = "Basic Onboarding",
    welcome_message: str = "Welcome to Salesbrain!",
    expiration_days: int = 7,
    total_steps: int = 5
) -> Dict[str, Any]:
    """
    Create a new onboarding link.

    Args:
        organization_id: Organization UUID
        created_by: User UUID who created the link
        template_name: Onboarding template name
        welcome_message: Custom welcome message
        expiration_days: Days until link expires
        total_steps: Total steps in onboarding flow

    Returns:
        Dict with link details
    """
    async with db.tenant_db_pool.acquire() as conn:
        # Generate unique token
        link_token = await conn.fetchval(
            """
            SELECT generate_onboarding_token()
            """
        )

        # Build full URL
        link_url = f"https://onboarding.salesbrain.com/o/{link_token}"

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        # Insert link
        link_id = await conn.fetchval(
            """
            INSERT INTO onboarding_link (
                organization_id, created_by, link_token, link_url,
                template_name, welcome_message, expires_at, total_steps,
                status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')
            RETURNING id
            """,
            organization_id, created_by, link_token, link_url,
            template_name, welcome_message, expires_at, total_steps
        )

        # Get created link
        link = await conn.fetchrow(
            """
            SELECT * FROM onboarding_link WHERE id = $1
            """,
            link_id
        )

    return dict(link)


async def get_onboarding_links(
    organization_id: Optional[UUID] = None,
    status: Optional[str] = None,
    created_by: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get onboarding links with filters.

    Args:
        organization_id: Filter by organization
        status: Filter by status (active, expired, used, revoked)
        created_by: Filter by creator
        limit: Number of links to return
        offset: Pagination offset

    Returns:
        Dict with links and pagination info
    """
    where_clauses = []
    params = []
    param_count = 0

    if organization_id:
        param_count += 1
        where_clauses.append(f"organization_id = ${param_count}")
        params.append(organization_id)

    if status:
        param_count += 1
        where_clauses.append(f"status = ${param_count}")
        params.append(status)

    if created_by:
        param_count += 1
        where_clauses.append(f"created_by = ${param_count}")
        params.append(created_by)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Add limit and offset
    param_count += 1
    limit_param = param_count
    params.append(limit)

    param_count += 1
    offset_param = param_count
    params.append(offset)

    async with db.tenant_db_pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval(
            f"""
            SELECT COUNT(*) FROM onboarding_link {where_sql}
            """,
            *params[:-2]
        )

        # Get links with creator info
        rows = await conn.fetch(
            f"""
            SELECT
                ol.*,
                o.name as organization_name,
                u.email as created_by_email,
                u.first_name as created_by_first_name,
                u.last_name as created_by_last_name
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            LEFT JOIN "user" u ON ol.created_by = u.id
            {where_sql}
            ORDER BY ol.created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
            """,
            *params
        )

        links = [dict(row) for row in rows]

    return {
        "links": links,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


async def get_onboarding_link_by_id(link_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a single onboarding link by ID.

    Args:
        link_id: Onboarding link UUID

    Returns:
        Link dict or None
    """
    async with db.tenant_db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ol.*,
                o.name as organization_name,
                u.email as created_by_email
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            LEFT JOIN "user" u ON ol.created_by = u.id
            WHERE ol.id = $1
            """,
            link_id
        )

    return dict(row) if row else None


async def get_onboarding_link_by_token(link_token: str) -> Optional[Dict[str, Any]]:
    """
    Get an onboarding link by its token (for public access).

    Args:
        link_token: Link token

    Returns:
        Link dict or None
    """
    async with db.tenant_db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                ol.*,
                o.name as organization_name
            FROM onboarding_link ol
            JOIN organization o ON ol.organization_id = o.id
            WHERE ol.link_token = $1
            """,
            link_token
        )

    return dict(row) if row else None


async def track_link_access(
    link_token: str,
    ip_address: str,
    user_agent: str
) -> bool:
    """
    Track an access to an onboarding link.

    Args:
        link_token: Link token
        ip_address: IP address of accessor
        user_agent: User agent string

    Returns:
        True if tracked successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        await conn.execute(
            """
            SELECT track_onboarding_link_access($1, $2, $3)
            """,
            link_token, ip_address, user_agent
        )

    return True


async def update_link_progress(
    link_token: str,
    current_step: int,
    progress_percentage: int
) -> bool:
    """
    Update onboarding progress for a link.

    Args:
        link_token: Link token
        current_step: Current step number
        progress_percentage: Progress (0-100)

    Returns:
        True if updated successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                current_step = $2,
                progress_percentage = $3,
                updated_at = NOW()
            WHERE link_token = $1 AND status = 'active'
            """,
            link_token, current_step, progress_percentage
        )

    return result != "UPDATE 0"


async def complete_onboarding(link_token: str) -> bool:
    """
    Mark an onboarding link as completed.

    Args:
        link_token: Link token

    Returns:
        True if completed successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                status = 'used',
                completed_at = NOW(),
                progress_percentage = 100,
                updated_at = NOW()
            WHERE link_token = $1 AND status = 'active'
            """,
            link_token
        )

    return result != "UPDATE 0"


async def revoke_onboarding_link(
    link_id: UUID,
    revoked_by: UUID,
    reason: str = "Revoked by admin"
) -> bool:
    """
    Revoke an onboarding link.

    Args:
        link_id: Link UUID
        revoked_by: User UUID who revoked the link
        reason: Reason for revocation

    Returns:
        True if revoked successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                status = 'revoked',
                revoked_at = NOW(),
                revoked_by = $2,
                revoked_reason = $3,
                updated_at = NOW()
            WHERE id = $1 AND status IN ('active', 'expired')
            """,
            link_id, revoked_by, reason
        )

    return result != "UPDATE 0"


async def extend_onboarding_link(
    link_id: UUID,
    additional_days: int = 7
) -> bool:
    """
    Extend the expiration of an onboarding link.

    Args:
        link_id: Link UUID
        additional_days: Days to add to expiration

    Returns:
        True if extended successfully
    """
    async with db.tenant_db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE onboarding_link
            SET
                expires_at = expires_at + ($2 || ' days')::INTERVAL,
                status = CASE
                    WHEN status = 'expired' THEN 'active'
                    ELSE status
                END,
                updated_at = NOW()
            WHERE id = $1
            """,
            link_id, additional_days
        )

    return result != "UPDATE 0"


async def expire_old_links() -> int:
    """
    Expire all onboarding links past their expiration date.

    Returns:
        Number of links expired
    """
    async with db.tenant_db_pool.acquire() as conn:
        expired_count = await conn.fetchval(
            """
            SELECT expire_old_onboarding_links()
            """
        )

    return expired_count
```

---

#### Task 3.3: Create Onboarding Links API Endpoints

**File:** `app/api/onboarding_links.py` (NEW)

```python
"""
Onboarding Links API Endpoints

Provides APIs for generating and managing onboarding links.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel

from app.services import onboarding_link_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/onboarding", tags=["Onboarding Links"])


# ========================================
# Request/Response Models
# ========================================

class CreateOnboardingLinkRequest(BaseModel):
    """Request to create onboarding link"""
    organization_id: UUID
    template_name: str = "Basic Onboarding"
    welcome_message: str = "Welcome to Salesbrain!"
    expiration_days: int = 7
    total_steps: int = 5


class ExtendLinkRequest(BaseModel):
    """Request to extend link expiration"""
    additional_days: int = 7


class RevokeLinkRequest(BaseModel):
    """Request to revoke link"""
    reason: str = "Revoked by admin"


class UpdateProgressRequest(BaseModel):
    """Request to update onboarding progress"""
    current_step: int
    progress_percentage: int


# ========================================
# Endpoints
# ========================================

@router.post("/create-link", status_code=status.HTTP_201_CREATED)
async def create_onboarding_link(
    request: CreateOnboardingLinkRequest,
    created_by: UUID = Query(..., description="User UUID creating the link")
):
    """
    Create a new onboarding link.

    **Args:**
    - organization_id: Organization UUID
    - template_name: Onboarding template (Basic/Advanced/Enterprise)
    - welcome_message: Custom welcome message
    - expiration_days: Days until link expires
    - total_steps: Total steps in onboarding flow

    **Returns:**
    - link_url: Full onboarding URL
    - link_id: UUID of created link
    - expires_at: Expiration timestamp
    """
    try:
        link = await onboarding_link_service.create_onboarding_link(
            organization_id=request.organization_id,
            created_by=created_by,
            template_name=request.template_name,
            welcome_message=request.welcome_message,
            expiration_days=request.expiration_days,
            total_steps=request.total_steps
        )

        return {
            "success": True,
            "data": {
                "link_url": link["link_url"],
                "link_id": str(link["id"]),
                "link_token": link["link_token"],
                "expires_at": link["expires_at"].isoformat(),
                "status": link["status"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to create onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/links", status_code=status.HTTP_200_OK)
async def get_onboarding_links(
    organization_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    created_by: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get onboarding links with filters.

    **Filters:**
    - organization_id: Filter by organization
    - status: Filter by status (active, expired, used, revoked)
    - created_by: Filter by creator

    **Returns:**
    - List of onboarding links with metadata
    """
    try:
        result = await onboarding_link_service.get_onboarding_links(
            organization_id=organization_id,
            status=status_filter,
            created_by=created_by,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Failed to fetch onboarding links: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/link/{link_id}", status_code=status.HTTP_200_OK)
async def get_onboarding_link_detail(link_id: UUID):
    """
    Get detailed information for a single onboarding link.

    **Returns:**
    - Complete link details with tracking data
    """
    try:
        link = await onboarding_link_service.get_onboarding_link_by_id(link_id)

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Onboarding link {link_id} not found"
            )

        return {
            "success": True,
            "data": link
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch onboarding link detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/link/{link_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_onboarding_link(
    link_id: UUID,
    request: RevokeLinkRequest,
    revoked_by: UUID = Query(..., description="User UUID revoking the link")
):
    """
    Revoke an onboarding link.

    **Admin Only**

    **Args:**
    - link_id: Link UUID
    - reason: Reason for revocation

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.revoke_onboarding_link(
            link_id=link_id,
            revoked_by=revoked_by,
            reason=request.reason
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or already revoked/used"
            )

        return {
            "success": True,
            "message": f"Onboarding link {link_id} revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/link/{link_id}/extend", status_code=status.HTTP_200_OK)
async def extend_onboarding_link(
    link_id: UUID,
    request: ExtendLinkRequest
):
    """
    Extend the expiration of an onboarding link.

    **Args:**
    - link_id: Link UUID
    - additional_days: Days to add to expiration

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.extend_onboarding_link(
            link_id=link_id,
            additional_days=request.additional_days
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )

        return {
            "success": True,
            "message": f"Link expiration extended by {request.additional_days} days"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# Public Onboarding Access Endpoints
# ========================================

@router.get("/o/{link_token}", status_code=status.HTTP_200_OK)
async def access_onboarding_link(
    link_token: str,
    request: Request
):
    """
    Access an onboarding link (public endpoint).

    Tracks access and returns link details.

    **Args:**
    - link_token: Unique link token

    **Returns:**
    - Link details and onboarding configuration
    """
    try:
        # Get link
        link = await onboarding_link_service.get_onboarding_link_by_token(link_token)

        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding link not found"
            )

        # Check if expired
        if link["status"] == "expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This onboarding link has expired"
            )

        # Check if revoked
        if link["status"] == "revoked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This onboarding link has been revoked"
            )

        # Check if already used
        if link["status"] == "used":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This onboarding link has already been used"
            )

        # Track access
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")

        await onboarding_link_service.track_link_access(
            link_token=link_token,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "data": {
                "organization_name": link["organization_name"],
                "welcome_message": link["welcome_message"],
                "total_steps": link["total_steps"],
                "current_step": link["current_step"],
                "progress_percentage": link["progress_percentage"],
                "template_name": link["template_name"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to access onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/o/{link_token}/progress", status_code=status.HTTP_200_OK)
async def update_onboarding_progress(
    link_token: str,
    request: UpdateProgressRequest
):
    """
    Update progress for an onboarding session.

    **Args:**
    - link_token: Unique link token
    - current_step: Current step number
    - progress_percentage: Progress (0-100)

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.update_link_progress(
            link_token=link_token,
            current_step=request.current_step,
            progress_percentage=request.progress_percentage
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or not active"
            )

        return {
            "success": True,
            "message": "Progress updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update onboarding progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/o/{link_token}/complete", status_code=status.HTTP_200_OK)
async def complete_onboarding(link_token: str):
    """
    Mark onboarding as completed.

    **Args:**
    - link_token: Unique link token

    **Returns:**
    - Success message
    """
    try:
        success = await onboarding_link_service.complete_onboarding(link_token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or not active"
            )

        return {
            "success": True,
            "message": "Onboarding completed successfully! 🎉"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

#### Task 3.4: Register Onboarding Links Router

**File:** `app/main.py`

```python
from app.api.onboarding_links import router as onboarding_links_router

# Include routers
app.include_router(onboarding_links_router)  # Onboarding Links API
```

---

## 🔄 INTEGRATION READINESS CHECKLIST

### Frontend Integration Prerequisites

#### For Webhook Logs (READY FOR INTEGRATION)
- [x] Database table `webhook_log` exists
- [x] RLS policies configured
- [x] Service layer complete
- [ ] All 5 API endpoints implemented (3/5 done)
- [ ] All 17 event types supported (13/17 done)
- [ ] All 8 webhook sources supported (1/8 done)
- [ ] Export functionality complete
- [x] Frontend UI complete (545 lines)

**Remaining Work:** 2-3 hours

#### For User Assignment (NOT STARTED)
- [ ] Database tables created
- [ ] RLS policies configured
- [ ] Service layer complete
- [ ] All 5 API endpoints implemented
- [ ] Frontend UI (not built yet)

**Remaining Work:** 1-2 days

#### For Onboarding Links (NOT STARTED - Frontend NOT Ready)
- [ ] Database table created
- [ ] RLS policies configured
- [ ] Service layer complete
- [ ] All 5 admin endpoints implemented
- [ ] Public access endpoints implemented
- [ ] Frontend UI (not built yet - user confirmed)

**Remaining Work:** 1-2 days (backend only)

---

## 📅 PROPOSED TIMELINE

### Week 1: Complete Webhook Logs (100%)
**Days 1-2:**
- Implement 2 missing API endpoints
- Add 4 missing event types
- Add export functionality
- Test frontend-backend integration

**Goal:** Webhook Logs feature 100% integration-ready

### Week 2: User Assignment System
**Days 3-5:**
- Run database migration
- Implement service layer
- Implement 5 API endpoints
- Test assignment logic

**Days 6-7:**
- Frontend builds UI (separate team)
- Integration testing when UI ready

**Goal:** User Assignment backend 100% ready

### Week 3: Onboarding Links System
**Days 8-10:**
- Run database migration
- Implement service layer
- Implement admin + public APIs
- Test token generation & expiration

**Days 11-12:**
- Documentation & API testing
- Wait for frontend UI (user confirmed not ready yet)

**Goal:** Onboarding Links backend 100% ready for future integration

---

## 🎯 SUCCESS CRITERIA

### Definition of "100% Integration Ready"

A feature is considered "100% Integration Ready" when:

1. **Database:** All tables, indexes, RLS policies exist
2. **Service Layer:** All business logic implemented and tested
3. **API Endpoints:** All endpoints implemented with proper:
   - Request/response validation
   - Error handling
   - Pagination (where applicable)
   - Filtering (where applicable)
4. **Schema Compatibility:** Backend schemas match frontend expectations exactly
5. **Documentation:** API endpoints documented with examples
6. **Testing:** Manual testing confirms all endpoints work
7. **Frontend Confirmation:** UI team confirms backend meets their needs

---

## 📞 NEXT ACTIONS

### Immediate (Today):
1. Review this implementation roadmap with user
2. Get confirmation on priorities
3. Start implementing missing webhook endpoints

### This Week:
1. Complete webhook logs system (100%)
2. Test integration with frontend
3. Start user assignment backend

### Next 2 Weeks:
1. Complete user assignment backend
2. Complete onboarding links backend
3. Be ready for frontend integration when UI is complete

---

**END OF PHASE 3 IMPLEMENTATION ROADMAP**

**Created:** 2025-10-12
**Next Update:** After each major milestone
**Owner:** Ivan (Product) + Claude (Implementation)

---

**Salesbrain © 2025**
