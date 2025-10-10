-- ============================================
-- PHASE 3: WEBHOOK LOGS SYSTEM
-- ============================================
-- Migration Script for Webhook Logging Feature
-- Created: 2025-10-10
-- Purpose: Enable webhook event logging for Admin Dashboard monitoring

-- ============================================
-- 1. WEBHOOK LOG TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS webhook_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event Information
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) DEFAULT 'instantly', -- instantly, weconnect, n8n, etc.

    -- Relationships
    campaign_id UUID REFERENCES campaign(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contact(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organization(id) ON DELETE CASCADE,

    -- Status & Processing
    status VARCHAR(20) NOT NULL DEFAULT 'success', -- success, failed, retrying, pending
    retry_count INT DEFAULT 0,
    last_retry_at TIMESTAMPTZ,

    -- Data Storage
    payload JSONB NOT NULL, -- Full webhook payload
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    -- Additional tracking
    ip_address INET,
    user_agent TEXT
);

-- ============================================
-- 2. INDEXES FOR PERFORMANCE
-- ============================================

-- Primary query patterns
CREATE INDEX idx_webhook_log_event_type ON webhook_log(event_type);
CREATE INDEX idx_webhook_log_status ON webhook_log(status);
CREATE INDEX idx_webhook_log_created_at ON webhook_log(created_at DESC);

-- Relationship queries
CREATE INDEX idx_webhook_log_campaign_id ON webhook_log(campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX idx_webhook_log_contact_id ON webhook_log(contact_id) WHERE contact_id IS NOT NULL;
CREATE INDEX idx_webhook_log_organization_id ON webhook_log(organization_id) WHERE organization_id IS NOT NULL;

-- Advanced queries
CREATE INDEX idx_webhook_log_event_source ON webhook_log(event_source);
CREATE INDEX idx_webhook_log_failed ON webhook_log(status, created_at DESC) WHERE status = 'failed';

-- Full-text search in payload (GIN index)
CREATE INDEX idx_webhook_log_payload_gin ON webhook_log USING gin(payload);

-- Composite index for filtered queries
CREATE INDEX idx_webhook_log_org_created ON webhook_log(organization_id, created_at DESC);
CREATE INDEX idx_webhook_log_campaign_created ON webhook_log(campaign_id, created_at DESC) WHERE campaign_id IS NOT NULL;

-- ============================================
-- 3. COMMENTS (Documentation)
-- ============================================

COMMENT ON TABLE webhook_log IS 'Stores all incoming webhook events for monitoring and debugging';
COMMENT ON COLUMN webhook_log.event_type IS 'Type of webhook event (email_sent, reply_received, etc.)';
COMMENT ON COLUMN webhook_log.event_source IS 'Source of the webhook (instantly, weconnect, n8n)';
COMMENT ON COLUMN webhook_log.status IS 'Processing status: success, failed, retrying, pending';
COMMENT ON COLUMN webhook_log.payload IS 'Full webhook payload as JSON for debugging';
COMMENT ON COLUMN webhook_log.retry_count IS 'Number of times webhook processing was retried';

-- ============================================
-- 4. ROW-LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on webhook_log
ALTER TABLE webhook_log ENABLE ROW LEVEL SECURITY;

-- Policy 1: Salesbrain Admins can see ALL webhook logs
CREATE POLICY webhook_log_admin_all ON webhook_log
    FOR ALL
    TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('sb_admin', 'sb_operator')
    );

-- Policy 2: Organization users can see ONLY their organization's logs
CREATE POLICY webhook_log_org_select ON webhook_log
    FOR SELECT
    TO PUBLIC
    USING (
        current_setting('app.user_role', true) IN ('owner', 'admin', 'member')
        AND organization_id::text = current_setting('app.current_org_id', true)
    );

-- Policy 3: System can insert webhook logs (bypass RLS for inserts)
CREATE POLICY webhook_log_system_insert ON webhook_log
    FOR INSERT
    TO PUBLIC
    WITH CHECK (true); -- Allow all inserts (logged by system)

-- ============================================
-- 5. CLEANUP FUNCTION (Delete old logs)
-- ============================================

-- Function to clean up old webhook logs
CREATE OR REPLACE FUNCTION cleanup_old_webhook_logs(days_to_keep INT DEFAULT 90)
RETURNS TABLE(deleted_count BIGINT) AS $$
DECLARE
    delete_count BIGINT;
BEGIN
    -- Delete logs older than specified days
    DELETE FROM webhook_log
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS delete_count = ROW_COUNT;

    RETURN QUERY SELECT delete_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION cleanup_old_webhook_logs IS 'Deletes webhook logs older than specified days (default: 90 days)';

-- ============================================
-- 6. STATISTICS VIEW (For Dashboard)
-- ============================================

CREATE OR REPLACE VIEW webhook_log_stats AS
SELECT
    event_type,
    event_source,
    status,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as last_hour,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    AVG(retry_count) as avg_retry_count,
    MAX(created_at) as last_received_at
FROM webhook_log
GROUP BY event_type, event_source, status;

COMMENT ON VIEW webhook_log_stats IS 'Aggregated statistics for webhook logs by event type and status';

-- ============================================
-- 7. GRANT PERMISSIONS
-- ============================================

-- Grant access to application user
-- GRANT SELECT, INSERT ON webhook_log TO your_app_user;
-- GRANT SELECT ON webhook_log_stats TO your_app_user;
-- GRANT EXECUTE ON FUNCTION cleanup_old_webhook_logs TO your_app_user;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

-- Verify table creation
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'webhook_log') THEN
        RAISE NOTICE '✅ webhook_log table created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create webhook_log table';
    END IF;

    RAISE NOTICE '✅ Phase 3 Webhook Logs migration completed';
    RAISE NOTICE 'ℹ️  Total indexes created: 9';
    RAISE NOTICE 'ℹ️  RLS policies created: 3';
    RAISE NOTICE 'ℹ️  Functions created: 1';
    RAISE NOTICE 'ℹ️  Views created: 1';
END $$;
