-- Migration: Add Provider Connection Tables
-- Phase 1.5: Instantly Multi-Workspace Support
-- Date: 2025-10-10

-- =====================================================
-- 1. PROVIDER CONNECTION (Workspace-Level)
-- =====================================================

CREATE TABLE provider_connection (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organization(id) ON DELETE CASCADE,

  -- Provider Info
  provider TEXT NOT NULL CHECK (provider IN ('instantly', 'lemlist', 'weconnect')),

  -- Instantly Workspace
  workspace_id TEXT,
  workspace_name TEXT,

  -- Auth (Encrypted!)
  api_key_encrypted TEXT NOT NULL,

  -- Status
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
  last_synced_at TIMESTAMPTZ,
  sync_error TEXT,

  -- Metadata
  config JSONB,  -- Provider-specific config

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_provider_conn_org ON provider_connection(organization_id);
CREATE INDEX idx_provider_conn_workspace ON provider_connection(provider, workspace_id);
CREATE INDEX idx_provider_conn_status ON provider_connection(status);

COMMENT ON TABLE provider_connection IS 'Connects Organization to Instantly Workspace (or other providers)';
COMMENT ON COLUMN provider_connection.organization_id IS 'NULL = Shared Beta Workspace (multiple orgs)';
COMMENT ON COLUMN provider_connection.workspace_id IS 'Instantly Workspace ID';


-- =====================================================
-- 2. EMAIL ACCOUNT (Account-Level)
-- =====================================================

CREATE TABLE email_account (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
  provider_connection_id UUID NOT NULL REFERENCES provider_connection(id) ON DELETE CASCADE,

  -- Email Info
  email_address TEXT NOT NULL,
  display_name TEXT,

  -- Provider Info
  provider TEXT NOT NULL,
  provider_account_id TEXT,  -- Instantly's internal ID

  -- Settings
  daily_limit INT DEFAULT 50,
  warmup_enabled BOOLEAN DEFAULT TRUE,

  -- Status
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'warming', 'suspended', 'bounced')),

  -- Stats (cached from provider)
  emails_sent_today INT DEFAULT 0,
  emails_sent_total INT DEFAULT 0,
  last_email_sent_at TIMESTAMPTZ,

  -- Metadata
  metadata JSONB,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_account_org ON email_account(organization_id);
CREATE INDEX idx_email_account_provider_conn ON email_account(provider_connection_id);
CREATE INDEX idx_email_account_email ON email_account(email_address);
CREATE INDEX idx_email_account_provider_id ON email_account(provider, provider_account_id);
CREATE INDEX idx_email_account_status ON email_account(status);

COMMENT ON TABLE email_account IS 'Email sending accounts from Instantly (or other providers)';


-- =====================================================
-- 3. UPDATE CAMPAIGN TABLE
-- =====================================================

ALTER TABLE campaign ADD COLUMN provider_connection_id UUID REFERENCES provider_connection(id) ON DELETE SET NULL;
ALTER TABLE campaign ADD COLUMN email_account_id UUID REFERENCES email_account(id) ON DELETE SET NULL;
ALTER TABLE campaign ADD COLUMN workspace_id TEXT;
ALTER TABLE campaign ADD COLUMN imported_at TIMESTAMPTZ;

CREATE INDEX idx_campaign_provider_conn ON campaign(provider_connection_id);
CREATE INDEX idx_campaign_email_account ON campaign(email_account_id);
CREATE INDEX idx_campaign_workspace ON campaign(workspace_id);

COMMENT ON COLUMN campaign.provider_connection_id IS 'Which workspace this campaign belongs to';
COMMENT ON COLUMN campaign.email_account_id IS 'Which email account sends this campaign';
COMMENT ON COLUMN campaign.imported_at IS 'When this campaign was imported from provider';


-- =====================================================
-- 4. UPDATE MESSAGE TABLE
-- =====================================================

ALTER TABLE message ADD COLUMN email_account_id UUID REFERENCES email_account(id) ON DELETE SET NULL;
ALTER TABLE message ADD COLUMN from_email TEXT;
ALTER TABLE message ADD COLUMN to_email TEXT;

CREATE INDEX idx_message_email_account ON message(email_account_id);
CREATE INDEX idx_message_from_email ON message(from_email);

COMMENT ON COLUMN message.email_account_id IS 'Which email account sent/received this message';
COMMENT ON COLUMN message.from_email IS 'Sender email address';
COMMENT ON COLUMN message.to_email IS 'Recipient email address';


-- =====================================================
-- 5. TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_provider_connection_updated_at BEFORE UPDATE ON provider_connection
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_account_updated_at BEFORE UPDATE ON email_account
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- 6. ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS on new tables
ALTER TABLE provider_connection ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_account ENABLE ROW LEVEL SECURITY;

-- Provider Connection: Customers see only their own, Admins see all
CREATE POLICY provider_connection_isolation ON provider_connection
  USING (
    organization_id = current_setting('app.current_org_id', TRUE)::UUID
    OR organization_id IS NULL  -- Shared Beta Workspace
    OR current_setting('app.user_role', TRUE) IN ('sb_admin', 'sb_operator')
  );

-- Email Account: Customers see only their own, Admins see all
CREATE POLICY email_account_isolation ON email_account
  USING (
    organization_id = current_setting('app.current_org_id', TRUE)::UUID
    OR current_setting('app.user_role', TRUE) IN ('sb_admin', 'sb_operator')
  );


-- =====================================================
-- 7. SAMPLE DATA (for testing)
-- =====================================================

-- Example: Shared Beta Workspace (organization_id = NULL)
/*
INSERT INTO provider_connection (organization_id, provider, workspace_id, workspace_name, api_key_encrypted, status)
VALUES (NULL, 'instantly', 'shared-beta-workspace', 'Salesbrain Beta Workspace', 'ENCRYPTED_KEY_HERE', 'active');

-- Example: Customer-specific Workspace
INSERT INTO provider_connection (organization_id, provider, workspace_id, workspace_name, api_key_encrypted, status)
VALUES ('org-uuid-here', 'instantly', 'customer-workspace-123', 'Acme Corp Workspace', 'ENCRYPTED_KEY_HERE', 'active');
*/
