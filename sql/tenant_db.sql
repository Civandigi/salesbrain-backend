-- ============================================================================
-- Salesbrain Tenant Database Schema
-- Database: salesbrain_tenant
-- Purpose: Customer-specific data with Row-Level Security (RLS)
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLE: organization
-- Purpose: Multi-tenant organizations (customers)
-- ============================================================================
CREATE TABLE organization (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  plan TEXT DEFAULT 'solo' CHECK (plan IN ('solo', 'team', 'enterprise')),
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TABLE: user
-- Purpose: Users belonging to organizations
-- ============================================================================
CREATE TABLE "user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'sb_admin', 'sb_operator')),
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),

  first_name TEXT,
  last_name TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_org ON "user"(organization_id);
CREATE INDEX idx_user_email ON "user"(email);

-- Enable RLS
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON "user"
  USING (organization_id = current_setting('app.current_org_id', TRUE)::UUID);

-- ============================================================================
-- TABLE: contact
-- Purpose: Contact/Lead data (TENANT-SPECIFIC with personal data!)
-- ============================================================================
CREATE TABLE contact (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

  -- Link to Global-KB
  company_uid_ch TEXT,  -- Foreign key to global_kb.company

  -- Personal Data
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  email_hash TEXT,  -- SHA256 for deduplication
  phone TEXT,
  linkedin_url TEXT,

  -- Role
  job_title TEXT,
  department TEXT,
  seniority TEXT,

  -- Scores & Journey
  lead_score NUMERIC(5,2) DEFAULT 0.00,
  lead_score_updated_at TIMESTAMPTZ,
  journey_phase TEXT DEFAULT 'awareness' CHECK (journey_phase IN ('awareness', 'consideration', 'purchase', 'customer', 'churned')),
  journey_updated_at TIMESTAMPTZ,

  -- Status
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'unsubscribed', 'bounced')),
  tags TEXT[],
  notes TEXT,

  -- Research
  research_complete BOOLEAN DEFAULT FALSE,
  edibot_opener TEXT,
  edibot_generated_at TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contact_org ON contact(organization_id);
CREATE INDEX idx_contact_company ON contact(company_uid_ch);
CREATE INDEX idx_contact_email_hash ON contact(email_hash);
CREATE INDEX idx_contact_score ON contact(lead_score DESC);
CREATE INDEX idx_contact_journey ON contact(journey_phase);

-- Enable RLS
ALTER TABLE contact ENABLE ROW LEVEL SECURITY;

CREATE POLICY contact_isolation ON contact
  USING (organization_id = current_setting('app.current_org_id', TRUE)::UUID);

-- ============================================================================
-- TABLE: campaign
-- Purpose: Marketing campaigns (email/linkedin)
-- ============================================================================
CREATE TABLE campaign (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

  name TEXT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('email', 'linkedin', 'direct_mail', 'ads')),
  provider TEXT NOT NULL,  -- 'instantly', 'weconnect', 'n8n'
  provider_campaign_id TEXT,

  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'running', 'paused', 'completed', 'archived')),

  -- Configuration
  playbook_id UUID,
  templates JSONB,

  -- Metrics
  emails_sent INT DEFAULT 0,
  emails_opened INT DEFAULT 0,
  emails_replied INT DEFAULT 0,
  emails_bounced INT DEFAULT 0,

  -- Timestamps
  started_at TIMESTAMPTZ,
  paused_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaign_org ON campaign(organization_id);
CREATE INDEX idx_campaign_status ON campaign(status);
CREATE INDEX idx_campaign_provider ON campaign(provider, provider_campaign_id);

-- Enable RLS
ALTER TABLE campaign ENABLE ROW LEVEL SECURITY;

CREATE POLICY campaign_isolation ON campaign
  USING (organization_id = current_setting('app.current_org_id', TRUE)::UUID);

-- ============================================================================
-- TABLE: message
-- Purpose: Individual messages (email/linkedin)
-- ============================================================================
CREATE TABLE message (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

  contact_id UUID NOT NULL REFERENCES contact(id) ON DELETE CASCADE,
  campaign_id UUID REFERENCES campaign(id) ON DELETE SET NULL,

  direction TEXT NOT NULL CHECK (direction IN ('outgoing', 'incoming')),
  channel TEXT NOT NULL CHECK (channel IN ('email', 'linkedin', 'sms')),

  subject TEXT,
  body TEXT,

  status TEXT CHECK (status IN ('sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed')),

  provider TEXT,
  provider_message_id TEXT,

  sent_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  opened_at TIMESTAMPTZ,
  replied_at TIMESTAMPTZ,

  meta JSONB,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_message_org ON message(organization_id);
CREATE INDEX idx_message_contact ON message(contact_id);
CREATE INDEX idx_message_campaign ON message(campaign_id);
CREATE INDEX idx_message_provider ON message(provider, provider_message_id);
CREATE INDEX idx_message_status ON message(status);

-- Enable RLS
ALTER TABLE message ENABLE ROW LEVEL SECURITY;

CREATE POLICY message_isolation ON message
  USING (organization_id = current_setting('app.current_org_id', TRUE)::UUID);

-- ============================================================================
-- TABLE: event_log
-- Purpose: All interaction events (for analytics & triggers)
-- ============================================================================
CREATE TABLE event_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,

  event_type TEXT NOT NULL,  -- 'email.sent', 'email.opened', 'linkedin.connected', etc.
  occurred_at TIMESTAMPTZ NOT NULL,

  source TEXT,  -- 'instantly', 'weconnect', 'system'
  provider TEXT,

  subject_refs JSONB,  -- {"contact_id": "...", "campaign_id": "...", "message_id": "..."}
  payload JSONB,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_org ON event_log(organization_id);
CREATE INDEX idx_event_type ON event_log(event_type);
CREATE INDEX idx_event_occurred ON event_log(occurred_at DESC);
CREATE INDEX idx_event_subject_refs ON event_log USING GIN(subject_refs);

-- Enable RLS
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY event_log_isolation ON event_log
  USING (organization_id = current_setting('app.current_org_id', TRUE)::UUID);

-- ============================================================================
-- Triggers: Update updated_at columns
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organization_updated_at
  BEFORE UPDATE ON organization
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_updated_at
  BEFORE UPDATE ON "user"
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contact_updated_at
  BEFORE UPDATE ON contact
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_updated_at
  BEFORE UPDATE ON campaign
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Trigger: Auto-generate email_hash on contact insert/update
-- ============================================================================
CREATE OR REPLACE FUNCTION generate_email_hash()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.email IS NOT NULL THEN
    NEW.email_hash = encode(digest(lower(NEW.email), 'sha256'), 'hex');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contact_email_hash
  BEFORE INSERT OR UPDATE OF email ON contact
  FOR EACH ROW
  EXECUTE FUNCTION generate_email_hash();

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================
INSERT INTO organization (id, name, plan, status)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Test Organization', 'team', 'active');

INSERT INTO "user" (organization_id, email, password_hash, role, first_name, last_name)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin@test.com', '$2b$12$KIXxBVZ1FXEJvXvL0YqEZOqRfJh.M4VqH0zZHj5c8QYQxJKZqH8Oe', 'admin', 'Test', 'Admin');
  -- Password: 'password123' (bcrypt hashed)

INSERT INTO contact (organization_id, company_uid_ch, first_name, last_name, email, job_title, lead_score, journey_phase)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'CHE-123.456.789', 'Max', 'Mustermann', 'max@beispiel.ch', 'CEO', 75.5, 'consideration'),
  ('00000000-0000-0000-0000-000000000001', 'CHE-987.654.321', 'Anna', 'Test', 'anna@test-gmbh.ch', 'CTO', 50.0, 'awareness');

-- ============================================================================
-- End of Tenant Database Schema
-- ============================================================================
