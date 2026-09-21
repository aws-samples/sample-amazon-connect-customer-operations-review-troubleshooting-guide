# Pattern 14 — ACGR Sync Failure Recovery & Operations

## Overview

Amazon Connect Global Resiliency (ACGR) enables automatic bidirectional resource synchronization between a primary Amazon Connect instance and a replica instance in another AWS region. This guide covers:

1. **ACGR Architecture & Sync Mechanism** — how replication works
2. **CloudTrail Detection** — identifying sync issues and activity
3. **Troubleshooting Patterns** — diagnosis and remediation for each REL-009 through REL-013 finding
4. **Failover Test Campaign** — monthly verification workflow
5. **Operations Runbook** — CLI commands and verification steps

---

## Part 1: ACGR Architecture & Sync Mechanism

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Account XYZ                              │
│                                                                 │
│   us-east-1 (Primary)          us-west-2 (Replica)            │
│   ┌──────────────────┐         ┌──────────────────┐           │
│   │ Connect Instance │◄────────│ Connect Instance │           │
│   │   (i-abc1234)    │ sync    │   (i-abc1234)    │           │
│   │                  │────────►│                  │           │
│   │  Contact Flows   │         │  Contact Flows   │           │
│   │  Queues          │         │  Queues          │           │
│   │  Routing Profile │         │  Routing Profile │           │
│   │  Users           │         │  Users           │           │
│   │  etc.            │         │  etc.            │           │
│   └─────────┬────────┘         └─────────┬────────┘           │
│             │                            │                    │
│  ┌──────────▼──────────┐      ┌──────────▼──────────┐        │
│  │ TDG (Traffic        │      │ Replica resources   │        │
│  │ Distribution Group) │      │ (NOT replicated:    │        │
│  │ - Telephony         │      │  Lambda, Lex,       │        │
│  │ - Agent routing     │      │  S3 prompts, etc.)  │        │
│  │ - 50/50 split ──┐   │      │                     │        │
│  │                 │   │      │                     │        │
│  └─────────────────┘   │      └─────────────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

### Sync Roles & Permissions

| Component | Purpose | CloudTrail Identity |
|-----------|---------|---------------------|
| User (human/role) | Calls `ReplicateInstance` API | `arn:aws:iam::...:user/...` or role ARN |
| Amazon Connect Sync Service | Performs ongoing bidirectional sync | `invokedBy: synchronization.connect.amazonaws.com` |
| TDG (Traffic Distribution Group) | Routes calls between regions; no sync involved | User account |

### How to Identify a Sync Event in CloudTrail

The operation name (eventName) does not identify a sync event — the sync service can perform **any Connect resource mutation** (Create, Update, or Delete on any resource type). What uniquely identifies an event as ACGR sync is **who performed it**:

```
The two reliable, operation-agnostic sync identifiers:

  userIdentity.invokedBy  = "synchronization.connect.amazonaws.com"
  sourceIPAddress         = "synchronization.connect.amazonaws.com"

Both are constant across ALL sync events regardless of operation name.
```

> ⚠️ **Do NOT filter by `userIdentity.sessionContext.sessionIssuer.userName`** — this contains the full SLR name including a unique customer-specific suffix (e.g., `AWSServiceRoleForAmazonConnectSynchronization_11111111-2222-3333`) which varies per account. CloudTrail `LookupEvents` uses exact matching and will miss events if the suffix is unknown.

### Replication Timeline

```
User calls ReplicateInstance
  ↓
[0s] ReplicateInstance API call logged in CloudTrail
  ↓ Creates SLR: AWSServiceRoleForAmazonConnectSynchronization_<unique-id>
  ↓
[0-2s] Initial replication begins
  Status: INSTANCE_REPLICATION_IN_PROGRESS
  ↓ SLR begins reading from primary, writing to replica
  ↓
[5-8 min] Full copy of resources complete
  Status: INSTANCE_REPLICATION_COMPLETE
  ↓ Ongoing sync begins (bidirectional)
  ↓ Any change in primary is synced to replica and vice versa
  ↓ Typical latency: seconds to <1 minute
  ↓
[Ongoing] Sync service emits Connect mutation events in replica region
  ↓ invokedBy = synchronization.connect.amazonaws.com on ALL events
  ↓ HTTP 409 ResourceConflictException = benign (concurrent updates)
  ↓ HTTP 5xx / AccessDeniedException = investigate
```

---

## Part 2: CloudTrail Detection & Queries

### Event Source & Filtering

All ACGR sync events appear in CloudTrail under:
- **eventSource:** `connect.amazonaws.com`
- **awsRegion:** Replica region (where changes are written)
- **userIdentity.invokedBy:** `synchronization.connect.amazonaws.com` ← primary filter
- **sourceIPAddress:** `synchronization.connect.amazonaws.com` ← secondary filter

### Sample Sync Event (sanitized example)

```json
{
  "eventSource": "connect.amazonaws.com",
  "eventName": "DeleteUser",
  "awsRegion": "us-west-2",
  "sourceIPAddress": "synchronization.connect.amazonaws.com",
  "userIdentity": {
    "type": "AssumedRole",
    "invokedBy": "synchronization.connect.amazonaws.com",
    "arn": "arn:aws:sts::111122223333:assumed-role/AWSServiceRoleForAmazonConnectSynchronization_11111111-2222-3333/ResourceSynchronization",
    "sessionContext": {
      "sessionIssuer": {
        "userName": "AWSServiceRoleForAmazonConnectSynchronization_11111111-2222-3333"
      }
    }
  },
  "requestParameters": {
    "InstanceId": "arn:aws:connect:us-west-2:111122223333:instance/11111111-2222-3333-4444-555555555555",
    "UserId": "arn:aws:connect:us-west-2:111122223333:instance/11111111-2222-3333-4444-555555555555/agent/66666666-7777-8888-9999-000000000000"
  },
  "responseElements": null
}
```

Note: `responseElements: null` is normal for DELETE operations — it is NOT a failure indicator.

### CloudTrail Queries (Athena)

#### Query 1: Did ReplicateInstance ever succeed?

```sql
SELECT eventTime, userIdentity.arn, responseElements
FROM cloudtrail_logs
WHERE eventSource = 'connect.amazonaws.com'
  AND eventName = 'ReplicateInstance'
  AND errorCode IS NULL
ORDER BY eventTime DESC
LIMIT 10;
```

#### Query 2: Is the sync service active? (Last 24 hours)

```sql
SELECT COUNT(*) AS sync_events,
       MIN(eventTime) AS oldest,
       MAX(eventTime) AS newest
FROM cloudtrail_logs
WHERE eventSource = 'connect.amazonaws.com'
  AND awsRegion = 'us-west-2'
  AND useridentity.invokedby = 'synchronization.connect.amazonaws.com'
  AND eventTime > NOW() - INTERVAL '24 hours';
```

#### Query 3: Sync service errors — excluding benign 409s

```sql
SELECT eventTime, eventName, errorCode, errorMessage
FROM cloudtrail_logs
WHERE eventSource = 'connect.amazonaws.com'
  AND awsRegion = 'us-west-2'
  AND useridentity.invokedby = 'synchronization.connect.amazonaws.com'
  AND errorCode IS NOT NULL
  AND errorCode != 'ResourceConflictException'
  AND eventTime > NOW() - INTERVAL '7 days'
ORDER BY eventTime DESC;
```

#### Query 4: What resources were synced in last 30 minutes?

```sql
SELECT eventTime, eventName, requestParameters
FROM cloudtrail_logs
WHERE eventSource = 'connect.amazonaws.com'
  AND awsRegion = 'us-west-2'
  AND useridentity.invokedby = 'synchronization.connect.amazonaws.com'
  AND eventTime > NOW() - INTERVAL '30 minutes'
ORDER BY eventTime DESC;
```

#### Query 5: SLR existence (CLI)

```bash
aws iam list-roles \
  --query "Roles[?contains(Arn, 'AWSServiceRoleForAmazonConnectSynchronization')]"
```

### CloudTrail CLI — Check Sync Activity (Last 30 min)

```bash
# Filter by EventSource, then post-filter on invokedBy in results
# (LookupEvents does not support invokedBy as a lookup attribute directly)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-30M +%Y-%m-%dT%H:%M:%SZ) \
  --region us-west-2 \
  --query "Events[?contains(CloudTrailEvent, 'synchronization.connect.amazonaws.com')]" \
  --max-items 20
```

### Evaluating CloudTrail Results

| Result | Interpretation |
|--------|----------------|
| Events found, no `errorCode` | ✅ Sync service active and healthy |
| Events found, `errorCode = ResourceConflictException` | ✅ Benign HTTP 409 — concurrent update noise, ignore |
| Events found, `errorCode = AccessDeniedException` | 🔴 SLR missing permissions → REL-011 |
| Events found, `errorCode = InternalServiceException` | 🔴 Service-side error → escalate to AWS Support |
| **Zero events in last 30 min** (status was COMPLETE) | 🟠 REL-013 — sync service may be inactive or lagging |

---

## Part 3: Troubleshooting Each Finding

### Finding REL-009: ACGR Not Configured (Production + TDG but no Replication)

**Symptom:** Production instance has a TDG but no ReplicationConfiguration block in DescribeInstance.

**Impact:** DR setup incomplete; replica instance exists but resources are NOT automatically synced.

**Remediation Steps:**

```bash
# Step 1: Verify SAML is enabled (prerequisite for ACGR)
aws connect describe-instance \
  --instance-id <INSTANCE_ID> \
  --region us-east-1 \
  --query 'Instance.IdentityManagementType'
# Expected: "SAML"
# If "CONNECT_MANAGED": ACGR cannot be enabled

# Step 2: Enable ACGR — call ONCE per instance pair
aws connect replicate-instance \
  --instance-id <INSTANCE_ID> \
  --replica-region us-west-2 \
  --replica-alias <REPLICA_INSTANCE_ALIAS> \
  --region us-east-1

# Step 3: Monitor progress (check every 30 sec, allow up to 10 min)
# Poll every 30s (portable — no `watch` dependency; Ctrl-C to stop):
while true; do
  aws connect describe-instance \
    --instance-id <INSTANCE_ID> \
    --region us-east-1 \
    --query "Instance.ReplicationConfiguration.ReplicationStatusSummaryList"
  sleep 30
done
# Wait for: "INSTANCE_REPLICATION_COMPLETE"

# Step 4: Verify SLR was created
aws iam list-roles \
  --query "Roles[?contains(Arn, 'AWSServiceRoleForAmazonConnectSynchronization')]"

# Step 5: Verify resources in replica
aws connect list-contact-flows \
  --instance-id <INSTANCE_ID> \
  --region us-west-2 \
  --query 'ContactFlowSummaryList[*].[Name,Id]'
```

---

### Finding REL-010: ACGR Replication In Progress

**Symptom:** `ReplicationStatus = INSTANCE_REPLICATION_IN_PROGRESS`

**Normal Duration:** 5–8 minutes. Flag if >15 minutes.

```bash
# Monitor until COMPLETE
# Poll every 10s (portable — no `watch` dependency; Ctrl-C to stop):
while true; do
  aws connect describe-instance \
    --instance-id <INSTANCE_ID> \
    --region us-east-1 \
    --query "Instance.ReplicationConfiguration.ReplicationStatusSummaryList"
  sleep 10
done

# If still IN_PROGRESS after 20 min — escalate to AWS Support with:
# - Instance IDs (primary + replica)
# - ReplicationStatusReason
# - ReplicateInstance CloudTrail event timestamp
# - SLR ARN
```

---

### Finding REL-011: ACGR Sync Failure

**Symptom:** `ReplicationStatus = INSTANCE_REPLICATION_FAILED` or `INSTANCE_REPLICATION_DELETION_FAILED`

**Impact:** CRITICAL — primary changes not synced to replica. Resources diverge.

#### Root Cause 1: SLR Missing Permissions

```bash
# Check SLR exists
aws iam list-roles \
  --query "Roles[?contains(Arn, 'AWSServiceRoleForAmazonConnectSynchronization')]"

# Check for AccessDeniedException from sync service in CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time $(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-6H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-west-2 \
  --query "Events[?contains(CloudTrailEvent, 'synchronization.connect.amazonaws.com') && contains(CloudTrailEvent, 'AccessDeniedException')]"
```

#### Root Cause 2: Service Quota Exceeded

```bash
# Connect quota codes are L-prefixed (e.g. L-12AB7C57), not names like "INSTANCE_QUOTA".
# Look the instance quota up by name rather than hardcoding a code:
aws service-quotas list-service-quotas \
  --service-code connect \
  --region us-west-2 \
  --query "Quotas[?contains(QuotaName, 'instance')].[QuotaName,QuotaCode,Value]" \
  --output table
```

#### General Remediation

```bash
# Read ReplicationStatusReason for root cause
aws connect describe-instance \
  --instance-id <INSTANCE_ID> \
  --region us-east-1 \
  --query 'Instance.ReplicationConfiguration.ReplicationStatusSummaryList[0].ReplicationStatusReason'

# Escalate to AWS Support if persists >30 min with:
# - Primary + replica instance IDs
# - ReplicationStatusReason
# - CloudTrail events from sync service around failure time
# - SLR ARN
```

---

### Finding REL-012: ACGR Replication Not Started

**Symptom:** `ReplicationStatus = RESOURCE_REPLICATION_NOT_STARTED`

```bash
# Re-initiate sync
aws connect replicate-instance \
  --instance-id <INSTANCE_ID> \
  --replica-region us-west-2 \
  --replica-alias <REPLICA_INSTANCE_ALIAS> \
  --region us-east-1

# Monitor
# Poll every 30s (portable — no `watch` dependency; Ctrl-C to stop):
while true; do
  aws connect describe-instance \
    --instance-id <INSTANCE_ID> \
    --region us-east-1 \
    --query "Instance.ReplicationConfiguration.ReplicationStatusSummaryList"
  sleep 30
done
```

---

### Finding REL-013: ACGR Sync Service Inactive

**Symptom:** `DescribeInstance` shows COMPLETE but no sync events from `synchronization.connect.amazonaws.com` in last 30 minutes.

```bash
# Check sync activity in replica region
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-west-2 \
  --query "Events[?contains(CloudTrailEvent, 'synchronization.connect.amazonaws.com')]" \
  --max-items 20

# If 0 events:
# 1. Make a test change in primary (e.g., create a contact flow)
# 2. Wait 2 minutes
# 3. Re-run the query above
# 4. If still 0 events, verify SLR trust policy
aws iam get-role \
  --role-name <SLR_ROLE_NAME> \
  --query 'Role.AssumeRolePolicyDocument'
# Should trust: synchronization.connect.amazonaws.com
```

---

## Part 4: Failover Test Campaign (Monthly)

### Pre-Test Checklist

```bash
# 1. ACGR sync status — must be COMPLETE
aws connect describe-instance \
  --instance-id <INSTANCE_ID> \
  --region us-east-1 \
  --query 'Instance.ReplicationConfiguration.ReplicationStatusSummaryList[0].ReplicationStatus'

# 2. Sync service active — events in last 30 min
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-30M +%Y-%m-%dT%H:%M:%SZ) \
  --region us-west-2 \
  --query "Events[?contains(CloudTrailEvent, 'synchronization.connect.amazonaws.com')]" \
  --max-items 5

# 3. TDG status — must be ACTIVE
aws connect list-traffic-distribution-groups --region us-east-1
aws connect get-traffic-distribution \
  --id <TDG_ID> \
  --region us-east-1 \
  --query 'TelephonyConfig.Distributions'

# 4. Resource count match between primary and replica
PRIMARY=$(aws connect list-contact-flows --instance-id <INSTANCE_ID> --region us-east-1 --query 'length(ContactFlowSummaryList)' --output text)
REPLICA=$(aws connect list-contact-flows --instance-id <INSTANCE_ID> --region us-west-2 --query 'length(ContactFlowSummaryList)' --output text)
echo "Primary: $PRIMARY | Replica: $REPLICA"
```

> **Command shape (verified against the connect API):** `update-traffic-distribution` takes three
> independent parameters, each an object with a `Distributions` list — NOT a nested
> `TelephonyDistribution` object:
> - `--telephony-config` → `{"Distributions":[{"Region":"...","Percentage":N}]}` (telephony %; must sum to 100)
> - `--agent-config` → `{"Distributions":[{"Region":"...","Percentage":N}]}` (agent %; must sum to 100)
> - `--sign-in-config` → `{"Distributions":[{"Region":"...","Enabled":true|false}]}` (sign-in uses a **boolean `Enabled`**, not a percentage)
>
> Pass only the config(s) you intend to change. The examples below shift telephony + agent traffic.

### Phase 1: Shallow Failover (1%, 5 min)

```bash
# Shift 1% traffic to replica
aws connect update-traffic-distribution \
  --id <TDG_ID> \
  --telephony-config '{"Distributions":[{"Region":"us-east-1","Percentage":99},{"Region":"us-west-2","Percentage":1}]}' \
  --agent-config '{"Distributions":[{"Region":"us-east-1","Percentage":99},{"Region":"us-west-2","Percentage":1}]}' \
  --region us-east-1

# Monitor replica for 5 min, then revert to primary
aws connect update-traffic-distribution \
  --id <TDG_ID> \
  --telephony-config '{"Distributions":[{"Region":"us-east-1","Percentage":100},{"Region":"us-west-2","Percentage":0}]}' \
  --agent-config '{"Distributions":[{"Region":"us-east-1","Percentage":100},{"Region":"us-west-2","Percentage":0}]}' \
  --region us-east-1
```

### Phase 2: Full Failover (50%, 15 min)

```bash
# Shift 50% traffic to replica
aws connect update-traffic-distribution \
  --id <TDG_ID> \
  --telephony-config '{"Distributions":[{"Region":"us-east-1","Percentage":50},{"Region":"us-west-2","Percentage":50}]}' \
  --agent-config '{"Distributions":[{"Region":"us-east-1","Percentage":50},{"Region":"us-west-2","Percentage":50}]}' \
  --region us-east-1

# Monitor 15 min, then revert to primary
aws connect update-traffic-distribution \
  --id <TDG_ID> \
  --telephony-config '{"Distributions":[{"Region":"us-east-1","Percentage":100},{"Region":"us-west-2","Percentage":0}]}' \
  --agent-config '{"Distributions":[{"Region":"us-east-1","Percentage":100},{"Region":"us-west-2","Percentage":0}]}' \
  --region us-east-1
```

### Post-Test Report Template

```markdown
## Failover Test Report — [Date]

### Pre-Test Verification
- [✓/✗] ACGR status: INSTANCE_REPLICATION_COMPLETE
- [✓/✗] Sync service active (last event: [timestamp])
- [✓/✗] TDG status: ACTIVE
- [✓/✗] Resource count match: Primary=[n], Replica=[n]

### Phase 1 (1%, 5 min)
- Calls routed to replica: [n] | Success rate: [n%] | Errors: [n]

### Phase 2 (50%, 15 min)
- Calls routed to replica: [n] | Success rate: [n%] | Errors: [n]

### Issues Found
- [Description] → [Action]

### Sign-Off
- Conducted by: [Name] | Date: [Date]
- Status: ✓ PASSED / ⚠️ WARNING / ✗ FAILED
```

---

## Part 5: Operations Runbook (Quick Reference)

```bash
# Enable ACGR
aws connect replicate-instance \
  --instance-id <INSTANCE_ID> --replica-region us-west-2 --replica-alias <REPLICA_INSTANCE_ALIAS> --region us-east-1

# Check ACGR status
aws connect describe-instance \
  --instance-id <INSTANCE_ID> --region us-east-1 \
  --query 'Instance.ReplicationConfiguration'

# Check sync service active (last 24h)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-24H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-west-2 \
  --query "Events[?contains(CloudTrailEvent, 'synchronization.connect.amazonaws.com')]" \
  --max-items 50

# Verify SLR exists
aws iam list-roles \
  --query "Roles[?contains(Arn, 'AWSServiceRoleForAmazonConnectSynchronization')]"
```

---

## Resources NOT Replicated (Customer Responsibility)

- Lambda function integrations
- Lex bot integrations
- Amazon Q integrations
- Wisdom content bases
- S3 prompts (region-specific S3 buckets)
- Custom vocabulary for Contact Lens
- Saved report schedules
- Draft views (published views only are replicated)

---

## Related Findings

- **REL-001:** Traffic Distribution Group setup
- **REL-002:** Phone number resilience
- **REL-009 through REL-013:** ACGR sync issues (this pattern)
