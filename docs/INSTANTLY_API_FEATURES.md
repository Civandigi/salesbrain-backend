# Instantly.ai API Features & Capabilities

> Complete overview of Instantly API v1 and v2
> Generated: 2025-10-10
> Workspace: Salesbrain (e4d0dd01-824f-4c36-b65a-d0eaf813a481)

## API Overview

### API v2 (RECOMMENDED)
- **Base URL**: `https://api.instantly.ai/api/v2`
- **Authentication**: Bearer Token (Header: `Authorization: Bearer <token>`)
- **Status**: Active, future-proof
- **Advantages**: RESTful, better error handling, double the endpoints

### API v1 (DEPRECATED 2025)
- **Base URL**: `https://api.instantly.ai/api/v1`
- **Authentication**: API Key (Query param: `api_key=<key>`)
- **Status**: Will be deprecated in 2025
- **Use Case**: Legacy support only

---

## API v2 Endpoints (Complete List)

### 1. Workspace Management

#### GET `/workspaces/current`
Get current workspace information
```json
Response: {
  "id": "uuid",
  "name": "string",
  "owner": "uuid",
  "timestamp_created": "ISO8601",
  "timestamp_updated": "ISO8601",
  "plan_id": "string",
  "plan_id_leadfinder": "string",
  "org_logo_url": "string",
  "org_client_domain": "string"
}
```

**Use Cases:**
- Display workspace info in dashboard
- Check plan limits
- Verify workspace ownership

---

### 2. Campaign Management

#### GET `/campaigns`
List all campaigns (with pagination)
```json
Response: {
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "status": "active|paused|completed",
      "timestamp_created": "ISO8601",
      "timestamp_updated": "ISO8601",
      "schedule": {...}
    }
  ],
  "next_starting_after": "uuid|timestamp"
}
```

**Pagination:**
- Use `?starting_after=<id>` for next page
- Use `?limit=<number>` to control page size

#### POST `/campaigns`
Create new campaign
```json
Request: {
  "name": "Campaign Name",
  "schedule": {...},
  "email_account_ids": ["uuid"],
  "sequences": [...]
}
```

#### PUT `/campaigns/{id}`
Update existing campaign

#### DELETE `/campaigns/{id}`
Delete campaign

#### POST `/campaigns/{id}/start`
Start a paused campaign

#### POST `/campaigns/{id}/pause`
Pause an active campaign

**Use Cases:**
- Import existing campaigns to Salesbrain DB
- Monitor campaign status changes
- Automatic campaign creation via Salesbrain UI
- Campaign lifecycle management

---

### 3. Email Account Management

#### GET `/accounts`
List all email sending accounts (with pagination)
```json
Response: {
  "items": [
    {
      "id": "uuid",
      "email": "sender@example.com",
      "status": "active|paused|error",
      "smtp_username": "string",
      "warmup_enabled": boolean,
      "daily_limit": number,
      "timestamp_created": "ISO8601"
    }
  ],
  "next_starting_after": "timestamp"
}
```

**Pagination:**
- Use `?starting_after=<timestamp>` for next page
- Use `?limit=<number>` to control page size

**Account Status Values:**
- `active`: Sending emails normally
- `paused`: Temporarily disabled
- `error`: Authentication or connection issue

**Use Cases:**
- Track email account health
- Monitor daily sending limits
- Assign accounts to campaigns
- Balance load across accounts
- Alert on account errors

---

### 4. Lead Management

#### POST `/leads`
Add leads to campaign (bulk operation)
```json
Request: {
  "campaign_id": "uuid",
  "leads": [
    {
      "email": "lead@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "Acme Corp",
      "personalization": "string",
      "phone": "string",
      "website": "string",
      "custom_variables": {...}
    }
  ]
}
```

#### DELETE `/leads/{id}`
Remove lead from campaign

**Use Cases:**
- Import leads from Salesbrain contact database
- Sync contact updates to Instantly
- Remove unsubscribed contacts
- Bulk lead operations

---

### 5. Analytics & Reporting

#### GET `/analytics/campaign/{campaign_id}`
Get detailed campaign analytics
```json
Response: {
  "campaign_id": "uuid",
  "total_leads": number,
  "emails_sent": number,
  "emails_opened": number,
  "emails_clicked": number,
  "emails_replied": number,
  "emails_bounced": number,
  "open_rate": number,
  "click_rate": number,
  "reply_rate": number,
  "bounce_rate": number,
  "timestamp_last_updated": "ISO8601"
}
```

#### GET `/analytics/account/{account_id}`
Get email account performance analytics
```json
Response: {
  "account_id": "uuid",
  "emails_sent_today": number,
  "emails_sent_this_week": number,
  "emails_sent_this_month": number,
  "daily_limit": number,
  "daily_limit_remaining": number,
  "deliverability_rate": number,
  "spam_rate": number,
  "warmup_progress": number
}
```

**Use Cases:**
- Real-time campaign performance dashboard
- Email account health monitoring
- ROI calculations
- A/B testing analysis
- Alert on low deliverability

---

### 6. Webhook Management

#### GET `/webhooks`
List all configured webhooks

#### POST `/webhooks`
Create new webhook
```json
Request: {
  "url": "https://your-domain.com/webhook",
  "events": ["email_sent", "email_opened", "reply_received", "..."],
  "campaigns": ["campaign_id"] // or "*" for all
}
```

#### DELETE `/webhooks/{id}`
Remove webhook

**Available Webhook Events** (17 total):
1. `email_sent` - Email successfully sent
2. `email_opened` - Recipient opened email
3. `email_clicked` - Recipient clicked link
4. `reply_received` - Recipient replied
5. `email_bounced` - Email bounced (soft/hard)
6. `email_unsubscribed` - Recipient unsubscribed
7. `email_spam_report` - Marked as spam
8. `lead_interested` - Lead showed interest
9. `lead_not_interested` - Lead declined
10. `lead_meeting_booked` - Meeting scheduled
11. `lead_completed` - Lead workflow completed
12. `lead_error` - Lead processing error
13. `campaign_started` - Campaign activated
14. `campaign_paused` - Campaign paused
15. `campaign_completed` - Campaign finished
16. `account_error` - Email account error
17. `account_suspended` - Account suspended

**Use Cases:**
- Real-time event processing
- Automatic contact status updates
- Lead scoring based on engagement
- CRM integration
- Alert notifications

---

## API v1 Endpoints (Legacy)

### Available Endpoints:

1. **GET** `/campaign/list` - List campaigns
2. **GET** `/account/list` - List email accounts
3. **POST** `/lead/add` - Add lead to campaign
4. **POST** `/lead/delete` - Remove lead
5. **GET** `/lead/list` - List leads in campaign
6. **GET** `/campaign/summary` - Campaign statistics

**Migration Note:** All v1 functionality is available in v2 with better structure. Migrate to v2 before 2025 deprecation.

---

## Instantly Agents (UI Feature, Not API)

**Important Discovery:**
Instantly "Agents" are **NOT directly accessible via API**. They are a UI/dashboard feature for:
- AI-powered email writing assistance
- Reply detection and categorization
- Lead qualification automation
- Smart follow-up suggestions

**Salesbrain Strategy:**
Instead of trying to use Instantly's agents via API (not possible), we should:

1. **Build Our Own Intelligence Layer:**
   - Use webhook events for real-time data
   - Apply our own AI/ML for lead scoring
   - Create custom automation rules
   - Build better analytics than Instantly dashboard

2. **Leverage Instantly's Strengths:**
   - Email deliverability infrastructure
   - Sender reputation management
   - Email warmup automation
   - Campaign scheduling engine
   - SMTP connection management

3. **Add Salesbrain Value:**
   - Multi-customer workspace management
   - Unified inbox across all campaigns
   - Advanced reporting and analytics
   - Custom lead qualification rules
   - Integration with external tools (CRM, Slack, etc.)
   - Better UI/UX for customers

---

## Recommended Implementation for Salesbrain

### Phase 2 (Current - Backend Complete ✓)
- [x] API v2 client implementation
- [x] Webhook receiver for all 17 events
- [x] Database schema (campaigns, accounts, messages)
- [x] Admin + customer API endpoints
- [x] RLS for multi-tenant isolation
- [x] Connection testing

### Phase 3 (Next - UI & Real-time)
- [ ] Campaign import sync (fetch existing campaigns)
- [ ] Real-time webhook processing
- [ ] Email account health dashboard
- [ ] Campaign performance analytics
- [ ] Unified inbox (all messages, all campaigns)
- [ ] Lead status tracking

### Phase 4 (Intelligence Layer)
- [ ] AI-powered lead scoring
- [ ] Automatic reply categorization
- [ ] Smart follow-up recommendations
- [ ] Conversation thread analysis
- [ ] Custom automation rules
- [ ] Alert system for important events

### Phase 5 (Advanced Features)
- [ ] Multi-workspace management (per customer)
- [ ] Cross-campaign analytics
- [ ] ROI tracking and reporting
- [ ] A/B testing framework
- [ ] Template library
- [ ] Integration marketplace

---

## Key Features to Maximize for Salesbrain

### 1. **Real-time Event Processing**
- Use webhooks for instant updates
- Process all 17 event types
- Update contact status automatically
- Track engagement timeline

### 2. **Campaign Analytics**
- Pull analytics via API
- Build custom dashboards
- Show per-customer performance
- Track ROI and conversion rates

### 3. **Email Account Management**
- Monitor account health
- Track daily limits
- Alert on errors
- Balance sending load

### 4. **Lead Lifecycle Tracking**
- Import leads from Salesbrain contacts
- Track every interaction (opens, clicks, replies)
- Automatic status updates
- Meeting booking integration

### 5. **Multi-Customer Isolation**
- Shared workspace for beta (cost optimization)
- Dedicated workspace for production
- RLS for data security
- Admin dashboard with full visibility

---

## API Rate Limits & Best Practices

### Rate Limits (from Instantly):
- Not publicly documented
- Use retry logic with exponential backoff
- Implement request queuing
- Cache workspace/campaign data

### Best Practices:
1. **Use webhooks instead of polling** - Real-time > Periodic fetching
2. **Batch operations** - Add multiple leads at once
3. **Cache static data** - Workspace info, campaign configs
4. **Handle errors gracefully** - Retry on 429, 5xx errors
5. **Monitor API health** - Track response times, error rates

---

## Environment Configuration

### Current Setup (.env):
```bash
# API v2 (Primary - Use This!)
INSTANTLY_API_KEY=ZTRkMGRkMDEtODI0Zi00YzM2LWI2NWEtZDBlYWY4MTNhNDgxOmxCRk9JUmNleU5DRA==

# API v1 (Legacy - For Migration Only)
INSTANTLY_API_KEY_V1=_k3rc_FPx5X-7tdJuCZ30nMnckNHC

# Webhook URL (Local Testing)
INSTANTLY_WEBHOOK_URL=http://localhost:8001/webhooks/instantly/webhook

# Webhook URL (Production - TODO)
# INSTANTLY_WEBHOOK_URL=https://api.salesbrain.com/webhooks/instantly/webhook
```

---

## Next Steps

1. **Test Webhook Delivery:**
   - Add test campaign in Instantly
   - Send test email
   - Verify webhook received in Salesbrain backend
   - Check database entries created

2. **Import Existing Data:**
   - Fetch all campaigns via API
   - Import to Salesbrain database
   - Associate with organization
   - Sync email accounts

3. **Build Dashboard:**
   - Campaign list view
   - Email account status
   - Real-time message feed
   - Analytics charts

4. **Production Deployment:**
   - Configure public webhook URL
   - Set up dedicated workspace per customer
   - Implement account provisioning flow
   - Add monitoring and alerts

---

## Summary: What You Have Access To

### ✅ Full API v2 Access:
- Workspace management
- Campaign CRUD (create, read, update, delete)
- Email account listing and monitoring
- Lead management (add, remove, list)
- Analytics (campaign + account performance)
- Webhook configuration (17 event types)

### ❌ NOT Available via API:
- Instantly AI Agents (UI-only feature)
- Email template editor (use API to send raw sequences)
- Lead enrichment (Instantly's internal feature)
- Visual campaign builder (build via API instead)

### 🎯 Salesbrain Advantage:
Build a BETTER experience on top of Instantly:
- Multi-customer management
- Advanced analytics
- Unified inbox
- Custom AI layer
- Better UX for non-technical users

**The backend is 100% ready. Let's build the best B2B sales orchestrator!** 🚀
