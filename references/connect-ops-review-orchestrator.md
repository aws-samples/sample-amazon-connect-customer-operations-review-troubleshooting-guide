# Amazon Connect Operations Review — Orchestrator (Phase 0)

## Description

Discovers Amazon Connect instances, classifies them, and routes to the appropriate Well-Architected pillar assessments. This is the entry point for all operations reviews.

## When to Use

- User asks for an operations review, health check, or Well-Architected review of Amazon Connect
- User wants to discover Connect resources across regions
- User wants a full or targeted pillar assessment

## Execution Strategy

```
Phase 0: Discovery → Classification → Pillar Routing
Total budget: 30 seconds
```

## Pre-Flight (5 seconds max)

```
1. Determine current region from caller identity
2. Test: connect:ListInstances (MaxResults=1) in current region
   - SUCCESS → proceed
   - AccessDeniedException → STOP. Report: "Cannot access Connect. Need connect:ListInstances permission."
   - Other error → log and attempt next region
```

## Step 1 — Discover Instances (15 seconds max)

### Region Scanning Strategy

DEFAULT (scan top 4, stop when found):
1. Caller's region (from STS)
2. us-east-1
3. eu-west-2
4. ap-southeast-2

If user says "all regions", scan all:
us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, ca-central-1, af-south-1, ap-northeast-2, eu-west-2, us-gov-west-1

### Per Region

```
connect:ListInstances (MaxResults=10)
  - Empty response (<1 second) → skip region immediately
  - Results → for each instance:
    - connect:DescribeInstance
    - connect:DescribeInstanceAttribute (all: CONTACT_FLOW_LOGS, CONTACT_LENS,
      EARLY_MEDIA, ENHANCED_CONTACT_MONITORING, ENHANCED_CHAT_MONITORING,
      MULTI_PARTY_CONFERENCE, INBOUND_CALLS, OUTBOUND_CALLS, VOICEID)
    - connect:ListIntegrationAssociations (for AI detection)
    - connect:ListTagsForResource
```

### Response Extraction (Keep Only)

```
Per instance:
  - InstanceId, InstanceAlias, IdentityManagementType
  - CreatedTime, InstanceStatus, ServiceRole
  - Attributes: {CONTACT_FLOW_LOGS: true/false, CONTACT_LENS: true/false, ...}
  - Integrations: [{IntegrationType, IntegrationArn}]  (only type + ARN)
  - Tags: {key: value}
```

## Step 2 — Classify Instances (5 seconds)

For each instance, assign a classification:

| Classification | Criteria |
|---------------|----------|
| **Production** | Has integrations OR tags contain "prod" OR >0 WISDOM/Q_IN_CONNECT integrations |
| **Dev/Test** | Tags contain "dev/test/staging/sandbox" OR alias contains "test/dev/sandbox" |
| **Abandoned** | CreatedTime >1 year ago AND 0 integrations AND no prod tags |
| **AI-Focused** | Has WISDOM_ASSISTANT or Q_IN_CONNECT integration type |
| **Campaign** | Has CONNECT_CAMPAIGNS integration type |
| **DR Replica** | Has TrafficDistributionGroup association OR alias contains "replica/dr/bak" |

Instances can have multiple classifications (e.g., "Production + AI-Focused").

## Step 3 — Collect Shared Data (10 seconds)

These resources are needed by multiple pillars. Collect ONCE here:

```
Per instance:
  connect:ListContactFlows → store: [{Name, Id, Type, State}]
    Pagination: MaxResults=100, max 3 pages (cap 300 flows)
  
  connect:ListQueues → store: [{Name, Id, QueueType}]
    Pagination: MaxResults=100, max 2 pages (cap 200 queues)
  
  connect:ListPhoneNumbers → store: [{PhoneNumber, Id, PhoneNumberType, CountryCode}]
    Pagination: Full (billing implications — no cap)
  
  connect:ListUsers → store: count only + [{Username, Id}] for first 100
    Pagination: MaxResults=100, max 5 pages. Record total count.
  
  connect:ListRoutingProfiles → store: [{Name, Id}]
    Pagination: MaxResults=100, max 1 page
```

## Step 4 — Determine Which Pillars to Run

Based on classification and shared data:

| Condition | Pillars to Run |
|-----------|---------------|
| Any instance exists | Pillar 1 (Ops), Pillar 2 (Security) — always |
| Production instance | + Pillar 3 (Reliability), Pillar 4 (Performance) |
| Phone numbers claimed | + Pillar 5 (Cost) |
| AI-Focused classification | + Pillar 7 (GenAI) |
| >1 instance | + Pillar 6 (Sustainability) — consolidation opportunities |
| User requests specific pillar | Run only that pillar |
| User says "full review" | Run all 7 |

## Step 5 — Output & Route

Produce the Phase 0 output that all pillars will consume:

```markdown
## Discovery Results

### Instances Found: {count} across {regions}

| Instance | Alias | Region | Classification | Identity | Created | Key Attributes |
|----------|-------|--------|---------------|----------|---------|----------------|
| i-xxx    | prod  | us-east-1 | Production, AI-Focused | SAML | 2022-01-15 | CL=✅ Logs=✅ VoiceID=❌ |

### Shared Resource Counts

| Instance | Flows | Queues | Users | Routing Profiles | Phone Numbers |
|----------|-------|--------|-------|-----------------|---------------|
| i-xxx    | 45    | 12     | 230   | 8               | 15            |

### Pillars to Execute: {list}

### Permission Status (from pre-flight):
- connect:List* → ✅
- connect:Describe* → ✅ 
- wisdom:* → {✅/❌/NOT_TESTED}
- cloudwatch:* → {✅/❌/NOT_TESTED}

Proceeding to pillar assessments...
```

Then execute each pillar skill in sequence (or user-selected subset).

## Timeout Handling

- If Phase 0 exceeds 30 seconds:
  1. Save whatever instances were discovered
  2. Skip remaining regions
  3. Proceed with what's available
  4. Note "Discovery incomplete — {n} regions not scanned" in output

## Error Patterns

| Error | Action |
|-------|--------|
| `AccessDeniedException` on ListInstances | STOP — cannot proceed without instance access |
| `InvalidRequestException` on a region | Region not enabled — skip silently |
| `ThrottlingException` | Wait 2 seconds, retry once |
| 0 instances found across all regions | Report "No Connect instances found" — STOP |