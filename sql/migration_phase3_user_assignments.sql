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
CREATE INDEX IF NOT EXISTS idx_user_campaign_user ON user_campaign_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_user_campaign_campaign ON user_campaign_assignment(campaign_id);
CREATE INDEX IF NOT EXISTS idx_user_campaign_org ON user_campaign_assignment(organization_id);
CREATE INDEX IF NOT EXISTS idx_user_campaign_status ON user_campaign_assignment(status) WHERE status = 'active';

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
CREATE INDEX IF NOT EXISTS idx_user_contact_user ON user_contact_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_user_contact_contact ON user_contact_assignment(contact_id);
CREATE INDEX IF NOT EXISTS idx_user_contact_org ON user_contact_assignment(organization_id);
CREATE INDEX IF NOT EXISTS idx_user_contact_status ON user_contact_assignment(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_user_contact_next_followup ON user_contact_assignment(next_followup_at) WHERE next_followup_at IS NOT NULL;

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
