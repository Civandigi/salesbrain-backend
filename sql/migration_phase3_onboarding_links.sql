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
