# Amazon Connect Operations Review — Pillar 5: Cost Optimization

## Description

Identifies waste and cost-saving opportunities in Amazon Connect: idle instances, unused phone numbers, stale resources, recording storage costs, and campaign efficiency.

## When to Use

- Runs when phone numbers are claimed (billing is active)
- User asks about cost reduction, unused resources, or billing optimization

## Execution Strategy

```
Budget: 60 seconds
APIs: ~10 calls
Depends on: Phase 0 output (instance list, flows, queues, users, phone numbers, tags)
Condition: Runs if any phone numbers claimed OR user explicitly requests cost review
```

## Pre-Flight (3 seconds)

```
Phase 0 data check:
  - Phone numbers present → proceed (billing is active, cost review relevant)
  - 0 phone numbers AND 0 users → likely abandoned, flag and skip deep analysis
```

## Checks

### Check 5.1 — Idle / Abandoned Instance Detection (10 seconds max)

**Data source**: Phase 0 shared data only — NO extra API calls

**Checks**:
- [ ] Instances with 0 users AND 0 standard queues → idle (paying for phone numbers only)
- [ ] Instances with 0 users BUT claimed phone numbers → abandoned resource, still billing
- [ ] Instances with <3 users AND no integrations → likely dev/test, verify need
- [ ] Multiple instances in same region with similar names → consolidation candidate

**Cost impact estimates**:
- DID number: ~$0.03/day (~$1/month)
- Toll-free number: ~$0.06/day (~$2/month)
- Idle instance with 5 DIDs + 2 toll-free: ~$9/month, $108/year

**Findings**:
- Instance with 0 users + claimed numbers = 🟡 HIGH ($X/month waste)
- Multiple dev instances in same region = 🟡 MEDIUM (consolidation opportunity)

### Check 5.2 — Unused Phone Numbers (10 seconds max)

**Data source**: Phase 0 shared data (ListPhoneNumbers)

**Analysis (no extra API calls)**:
- [ ] Total number count × estimated monthly cost
- [ ] DID count: {n} × $1/mo = ${n}/mo
- [ ] Toll-free count: {n} × $2/mo = ${n}/mo
- [ ] Numbers on instances with 0 users → definitely unused
- [ ] Numbers on instances with 0 queues → no routing destination, unused

**Cross-reference with flows**: If a phone number isn't referenced in any contact flow's InboundPhoneNumber association, it's potentially unused (requires DescribePhoneNumber to check association — sample max 10).

**API calls (only if >10 numbers)**:
```
connect:DescribePhoneNumber (sample 10 numbers on low-activity instances)
  KEEP: ContactFlowId association — NULL = number not routed anywhere
```

**Findings**:
- Phone number with no contact flow association = 🟡 HIGH (paying but not routing)
- >20 phone numbers on single instance = 🟡 MEDIUM (review if all needed)

### Check 5.3 — Stale Contact Flows (5 seconds max)

**Data source**: Phase 0 shared data (ListContactFlows)

**No extra API calls — name-based analysis**:

**Checks**:
- [ ] Flows with "test", "copy", "old", "backup", "v1", "v2", "temp", "draft" in name
- [ ] Flows with State=ACTIVE but clearly test/temp naming → could be archived
- [ ] Count of potentially stale flows → cleanup effort estimate

**Findings**:
- >5 stale-named flows in production instance = 🟢 LOW (cleanup, no direct cost but operational overhead)

### Check 5.4 — Cost Allocation Tags (5 seconds max)

**Data source**: Phase 0 shared data (ListTagsForResource)

**No extra API calls**:

**Checks**:
- [ ] `CostCenter` or `Project` tag present → cost attribution possible
- [ ] `Environment` tag → can filter Cost Explorer by env
- [ ] No cost-related tags at all → cannot track Connect spend by team/project
- [ ] Inconsistent tagging across instances → partial visibility

**Findings**:
- No cost allocation tags = 🟡 MEDIUM (cannot attribute Connect costs to business units)
- Partial tagging (some instances tagged, others not) = 🟢 LOW

### Check 5.5 — Campaign Cost Efficiency (10 seconds max)

**Condition**: Only if Phase 0 found CONNECT_CAMPAIGNS integration.

**API calls**:
```
connectcampaignsv2:ListCampaigns (MaxResults=10)
connectcampaignsv2:GetCampaignState (for each campaign)
```

**Checks**:
- [ ] Campaigns in RUNNING state with no recent contacts → resource waste
- [ ] Predictive dialer with high abandon rate → regulatory risk + wasted minutes
- [ ] Multiple campaigns on same instance → shared capacity, potential contention cost
- [ ] Agentless campaigns → lower cost per contact (no agent time)

**Findings**:
- Campaign stuck RUNNING with no activity = 🟡 MEDIUM (paying for capacity)
- Could switch Progressive → Agentless for notification-only = 🟢 LOW (cost reduction opportunity)

### Check 5.6 — Recording Storage Costs (10 seconds max)

**API calls**:
```
s3:GetBucketLifecycleConfiguration (for recording bucket from DescribeInstanceStorageConfig)
```

**Checks**:
- [ ] Lifecycle policy exists — transition to Glacier/Deep Archive?
- [ ] No lifecycle = indefinite Standard storage ($0.023/GB/month)
- [ ] Estimate: if Contact Lens enabled, ~2MB per 5-min call × contact volume
- [ ] Recordings + transcripts + analytics all stored

**Error handling**: If s3:GetBucketLifecycleConfiguration denied → note and skip

**Findings**:
- No S3 lifecycle policy on recording bucket = 🟡 MEDIUM (storage costs grow unbounded)
- Lifecycle exists but >365 days before transition = 🟢 LOW (could be more aggressive)

### Check 5.7 — Cost Explorer Data (10 seconds max)

**API calls**:
```
ce:GetCostAndUsage
  TimePeriod: last 3 complete months
  Granularity: MONTHLY
  Metrics: UnblendedCost
  Filter: SERVICE = "Amazon Connect" OR "Amazon Lex" OR "Amazon Kinesis Video Streams"
  GroupBy: SERVICE
```

**Checks**:
- [ ] Monthly trend — increasing, stable, or decreasing?
- [ ] Service breakdown — how much is Connect vs Lex vs KVS?
- [ ] Month-over-month change >20% → investigate (growth or waste?)
- [ ] KVS cost present → streaming/recording active

**Error handling**: If ce:GetCostAndUsage denied → note "Cost data requires ce:GetCostAndUsage permission" and skip

**Findings**:
- >20% month-over-month increase without known growth = 🟡 MEDIUM (investigate)
- KVS costs but no Contact Lens = 🟢 LOW (streaming without analytics — intentional?)

## Findings Output Format

```markdown
## Pillar 5: Cost Optimization — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- Cost Explorer data: {AVAILABLE / NOT_AVAILABLE}
- Assessment completeness: {%}

### Cost Summary
| Category | Monthly Estimate | Action |
|----------|-----------------|--------|
| Unused phone numbers | ${n}/mo | Release numbers |
| Idle instances (numbers only) | ${n}/mo | Delete instances |
| Recording storage (no lifecycle) | ${n}/mo growing | Add lifecycle policy |
| Stuck campaigns | Unknown | Stop campaigns |
| **Total identifiable waste** | **${n}/mo** | |

### Recommendations (Prioritized)
1. Release unused phone numbers on idle instances (immediate savings)
2. Add S3 lifecycle policy to recording bucket
3. Implement cost allocation tags (CostCenter, Project, Environment)
4. Stop/delete stuck campaigns
5. Consolidate dev/test instances
```

## Timeout Handling

```
At 45 seconds: Stop issuing new API calls.
Priority order if timeout: 5.1 → 5.2 → 5.7 → 5.6 → 5.5 → 5.4 → 5.3
At 55 seconds: Produce findings from data collected so far.
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException
ce:GetCostAndUsage failure → skip Check 5.7
s3:* failure → skip Check 5.6
connectcampaignsv2:* failure → skip Check 5.5
```