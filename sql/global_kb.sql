-- ============================================================================
-- Salesbrain Global-KB Schema
-- Database: salesbrain_global_kb
-- Purpose: Shared company data across all tenants (NO personal data!)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: company
-- Purpose: Public company information (UID-CH as primary key)
-- ============================================================================
CREATE TABLE company (
  uid_ch TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  name_normalized TEXT,  -- For fuzzy matching
  domain TEXT,
  domain_status TEXT CHECK (domain_status IN ('FOUND', 'NO_DOMAIN_CERTIFIED', 'UNKNOWN')),

  -- Location
  address_street TEXT,
  address_plz TEXT,
  address_city TEXT,
  address_canton TEXT,
  country TEXT DEFAULT 'CH',

  -- Company Data
  industry TEXT,
  noga_code TEXT,
  headcount_range TEXT,
  legal_form TEXT,
  founded_year INT,
  status TEXT DEFAULT 'active',

  -- Social & Web
  linkedin_company_url TEXT,
  facebook_url TEXT,
  instagram_handle TEXT,
  phone_main TEXT,
  tech_stack JSONB,

  -- Research Metadata
  last_researched_at TIMESTAMPTZ,
  research_quality_score NUMERIC(3,2),  -- 0.00 - 1.00
  research_source TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_company_domain ON company(domain);
CREATE INDEX idx_company_city_canton ON company(address_city, address_canton);
CREATE INDEX idx_company_industry ON company(industry);
CREATE INDEX idx_company_researched ON company(last_researched_at);
CREATE INDEX idx_company_name_normalized ON company(name_normalized);

-- ============================================================================
-- TABLE: company_role_template
-- Purpose: Typical roles per company (NOT person-specific!)
-- ============================================================================
CREATE TABLE company_role_template (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_uid_ch TEXT NOT NULL REFERENCES company(uid_ch) ON DELETE CASCADE,

  role_title TEXT NOT NULL,
  department TEXT,
  seniority TEXT,
  typical_count INT DEFAULT 1,

  last_verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_role_company ON company_role_template(company_uid_ch);
CREATE INDEX idx_role_title ON company_role_template(role_title);

-- ============================================================================
-- TABLE: research_evidence
-- Purpose: Provenance tracking for all research data
-- ============================================================================
CREATE TABLE research_evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_uid_ch TEXT REFERENCES company(uid_ch) ON DELETE CASCADE,

  source TEXT NOT NULL,  -- 'moneyhouse', 'apollo', 'website', 'linkedin'
  source_url TEXT,
  collected_at TIMESTAMPTZ DEFAULT NOW(),
  valid_until TIMESTAMPTZ,

  snapshot JSONB,  -- Original data
  confidence NUMERIC(3,2),  -- 0.00 - 1.00

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_company ON research_evidence(company_uid_ch);
CREATE INDEX idx_evidence_source ON research_evidence(source);
CREATE INDEX idx_evidence_collected ON research_evidence(collected_at);

-- ============================================================================
-- TABLE: global_kb_access_log
-- Purpose: Audit trail - which tenant researched which company
-- ============================================================================
CREATE TABLE global_kb_access_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,  -- Tenant ID (from tenant DB)
  company_uid_ch TEXT NOT NULL,
  action TEXT NOT NULL,  -- 'research', 'read', 'enrich'
  cost_incurred NUMERIC(10,2) DEFAULT 0.00,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_access_log_org ON global_kb_access_log(organization_id);
CREATE INDEX idx_access_log_company ON global_kb_access_log(company_uid_ch);
CREATE INDEX idx_access_log_timestamp ON global_kb_access_log(timestamp);

-- ============================================================================
-- Trigger: Update updated_at on company changes
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_company_updated_at
  BEFORE UPDATE ON company
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================
INSERT INTO company (uid_ch, name, name_normalized, domain, domain_status, address_city, address_canton, country, industry, headcount_range, legal_form, status)
VALUES
  ('CHE-123.456.789', 'Beispiel AG', 'beispiel', 'beispiel.ch', 'FOUND', 'Zürich', 'ZH', 'CH', 'IT Services', '11-50', 'AG', 'active'),
  ('CHE-987.654.321', 'Test GmbH', 'test', 'test-gmbh.ch', 'FOUND', 'Bern', 'BE', 'CH', 'Consulting', '51-200', 'GmbH', 'active');

-- ============================================================================
-- End of Global-KB Schema
-- ============================================================================
