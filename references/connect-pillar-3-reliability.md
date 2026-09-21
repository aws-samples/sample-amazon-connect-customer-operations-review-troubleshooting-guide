# Amazon Connect Operations Review — Pillar 3: Reliability

## Description

Assesses Amazon Connect disaster recovery readiness, multi-region resilience, capacity planning, and fault tolerance for production workloads.

## When to Use

- Runs for Production-classified instances
- User asks about DR, failover, high availability, or capacity

## Execution Strategy

```
Budget: 90 seconds
APIs: ~15 calls
Depends on: Phase 0 output (instance list, classification, phone numbers)
Condition: Only for instances classified as "Production" or "DR Replica"

Parallelization plan:
  Sequential:  3.1 → 3.2
  Parallel:    3.3 + 3.4 + 3.5 + 3.7 (run together after 3.1 + 3.2)
  Last:        3.6 (no API calls, from Phase 0 data)
  Estimated wall time: ~65 seconds on fast path
```

## Pre-Flight (5 seconds)

```
Test 1: connect:ListTrafficDistributionGroups (MaxResults=1)
  - SUCCESS → proceed with full reliability checks
  - AccessDeniedException → proceed without TDG checks, note in output

Test 2: connect:DescribeInstance (check for ReplicationConfiguration block)
  - ReplicationConfiguration present → ACGR enabled, run Check 3.7 in full
  - ReplicationConfiguration absent → ACGR not configured; report REL-009 if TDG exists
  - AccessDeniedException → skip Check 3.7, note in output
```

## Checks

### Check 3.1 — Traffic Distribution Groups / Multi-Region (25 seconds max)

**API calls**:
```
connect:ListTrafficDistributionGroups (MaxResults=10)
connect:GetTrafficDistribution (for each TDG found)
connect:ListTrafficDistributionGroupUsers (for each TDG, MaxResults=50)
```

**Checks**:
- [ ] TDG exists for each production instance — if not, single-region = no DR
- [ ] Traffic split — 100/0 is standby DR, 50/50 is active-active, other ratios = custom
- [ ] Agents in both regions — ListTrafficDistributionGroupUsers shows distribution
- [ ] TDG status — ACTIVE vs CREATION_IN_PROGRESS vs UPDATE_IN_PROGRESS

**Findings**:
- No TDG for production instance = 🔴 CRITICAL (no regional failover)
- TDG exists but 100/0 split = 🟡 MEDIUM (DR exists but untested if never shifted)
- TDG with agents in both regions = ✅ GOOD

### Check 3.2 — Phone Number Resilience (15 seconds max)

**Data source**: Phase 0 shared data (ListPhoneNumbers)

**API calls (only if TDG exists)**:
```
connect:DescribePhoneNumber (for DID/toll-free numbers, sample 10)
```

**Checks**:
- [ ] Phone number TDG association — numbers in TDG can failover
- [ ] Numbers NOT in TDG = cannot failover (customers lose connectivity)
- [ ] Phone number status — all CLAIMED? Any IN_PROGRESS or FAILED?
- [ ] Country diversity — all numbers in same country = regional concentration risk

**Findings**:
- Production numbers not in TDG = 🔴 CRITICAL (failover won't redirect calls)
- All numbers same country, no TDG = 🟠 HIGH (geographic concentration)

### Check 3.3 — Hours of Operation & Coverage Gaps (15 seconds max)

**API calls**:
```
connect:ListHoursOfOperations (MaxResults=50, from Phase 0 or fresh call)
connect:DescribeHoursOfOperation (for each, max 10)
connect:DescribeHoursOfOperationOverride (for each, check holiday overrides)
```

**Checks**:
- [ ] 24/7 coverage — does at least one HoO cover all hours?
- [ ] Timezone correctness — HoO timezone matches customer base?
- [ ] Coverage gaps — any day with 0 hours configured?
- [ ] Holiday overrides — configured for major holidays?
- [ ] Multiple HoOs with same hours — consolidation opportunity

**Findings**:
- No 24/7 HoO for production = 🟡 MEDIUM (intentional or gap?)
- No holiday overrides = 🟢 LOW (may handle via flow logic instead)

### Check 3.4 — Lambda Integration Resilience (15 seconds max)

**Data source**: Phase 0 shared data (ListLambdaFunctions ARNs from instance)

**API calls**:
```
lambda:GetFunction (for each Lambda ARN, max 5)
  KEEP: FunctionName, Runtime, DeadLetterConfig, Timeout, MemorySize
```

**Checks**:
- [ ] DLQ configured — Lambda without DLQ = silent failures in contact flows
- [ ] Timeout — the flow's Lambda block times out at a configurable max of 8s (Synchronous) / 60s (Asynchronous); a Lambda whose own timeout exceeds the block setting risks being cut off (Error branch)
- [ ] Runtime — deprecated runtimes (Python 3.8, Node 14) = maintenance risk
- [ ] Same-region — Lambda in different region than Connect instance = latency

**Error handling**: If lambda:GetFunction denied → note "Lambda resilience check requires lambda:GetFunction" and skip

### Check 3.5 — Real-Time Capacity Indicators (15 seconds max)

**API calls**:
```
connect:GetCurrentMetricData ⚠️ REQUIRES ELEVATED ROLE
  Metrics: CONTACTS_IN_QUEUE, OLDEST_CONTACT_AGE, AGENTS_AVAILABLE, AGENTS_ON_CONTACT
  Filters: Queues (top 5 by name from Phase 0)

cloudwatch:DescribeAlarms
  AlarmNamePrefix: filter for queue depth / concurrency alarms

cloudwatch:GetMetricData
  Metrics: ConcurrentCalls, ConcurrentCallsPercentage
  Period: 3600 (1 hour), last 24 hours
```

**Checks**:
- [ ] Queue depth alarms — exist for QueueSize? LongestQueueWaitTime?
- [ ] Concurrency trending — approaching service quota?
- [ ] Alarms on ConcurrentCallsPercentage — threshold at 80%?
- [ ] Historical peak — what's the max concurrent calls in last 24h?

**Error handling**:
- If GetCurrentMetricData returns session policy error → mark as "REQUIRES_ELEVATED_ROLE"
- DO NOT retry. DO NOT attempt GetMetricData or GetMetricDataV2.
- Use CloudWatch data only (doesn't require elevated role)

### Check 3.6 — Service Quotas Awareness (15 seconds max)

**API call** — retrieve the account's *applied* quotas (do not rely on hardcoded defaults; applied values differ per account and Region):
```
aws service-quotas list-service-quotas --service-code connect --region <region>
# Fallback for a single quota: aws service-quotas get-service-quota --service-code connect --quota-code <L-code>
```
Compare each applied quota `Value` against the resource counts from Phase 0. If the API is denied, note "Quota check requires servicequotas:ListServiceQuotas" and fall back to the documented **new-account defaults** below (an account's applied quota may be lower than these).

**Checks** (default new-account quotas shown; prefer the live applied value):
- [ ] User count vs quota (default 500) — >80% = approaching limit
- [ ] Phone number count vs quota (default 10 per instance)
- [ ] Flows per instance vs quota (default 100) — >80% = approaching limit
- [ ] Routing profiles vs quota (default 500)
- [ ] Connect instances per Region vs quota (default 2)

**Findings**:
- Any resource >80% of known default quota = 🟡 MEDIUM (request increase proactively)

### Check 3.7 — ACGR Sync Health (10 seconds max)

**Prerequisite**: Run only when instance is "Production" AND Check 3.1 found at least one TDG.
**Runs in parallel with**: Checks 3.3, 3.4, 3.5

**Step 1 — Call DescribeInstance (primary region)**:
```
connect:DescribeInstance
  InstanceId: <instance-id>
  Region:     <primary region>
  EXTRACT ONLY:
    Instance.ReplicationConfiguration.SourceRegion
    Instance.ReplicationConfiguration.GlobalSignInEndpoint
    Instance.ReplicationConfiguration.ReplicationStatusSummaryList[]
      - Region
      - ReplicationStatus
      - ReplicationStatusReason
```

**Step 2 — Evaluate ReplicationConfiguration**:
```
IF ReplicationConfiguration block is ABSENT:
  → FINDING: [REL-009] ACGR not configured
    Severity: 🟠 MEDIUM
    Note: TDG exists but no replication — DR setup incomplete
    Fix: See references/acgr-sync-operations.md — REL-009 section

IF ReplicationConfiguration block is PRESENT:
  FOR EACH entry in ReplicationStatusSummaryList:

    "INSTANCE_REPLICATION_COMPLETE"
      → ✅ HEALTHY — log and continue

    "INSTANCE_REPLICATION_IN_PROGRESS"
      → FINDING: [REL-010] ACGR initial replication in progress
        Severity: 🟡 INFO
        Note: Expected during first setup (<8 min); flag if older

    "INSTANCE_REPLICATION_FAILED"
    "INSTANCE_REPLICATION_DELETION_FAILED"
      → FINDING: [REL-011] ACGR sync failure in region {Region}
        Severity: 🔴 CRITICAL
        Detail: {ReplicationStatusReason}
        Fix: See references/acgr-sync-operations.md — REL-011 section

    "RESOURCE_REPLICATION_NOT_STARTED"
      → FINDING: [REL-012] ACGR replication not started
        Severity: 🟠 MEDIUM
        Fix: Re-call ReplicateInstance API
```

**Step 3 — CloudTrail validation** (supplementary; run only if Step 2 status is COMPLETE):
```
cloudtrail:LookupEvents
  Region:          <REPLICA region>
  LookupAttributes:
    AttributeKey:   EventSource
    AttributeValue: connect.amazonaws.com
  StartTime: now - 30 minutes
  EndTime:   now

Post-filter results:
  Keep only events where CloudTrailEvent contains
  "synchronization.connect.amazonaws.com"
  (matches both userIdentity.invokedBy and sourceIPAddress)

Evaluate:
  0 matching events AND status was COMPLETE
    → FINDING: [REL-013] ACGR sync service inactive
      Severity: 🟠 MEDIUM
      Note: No sync activity in last 30 min — possible lag or service pause

  Matching events found with errorCode present:
    EXCLUDE: errorCode == "ResourceConflictException" (benign HTTP 409 — ignore)
    errorCode == "AccessDeniedException" → SLR permissions broken → REL-011
    Other errorCodes → log for investigation

  Matching events found, no errors:
    → ✅ Sync service active and healthy
```

**⚠️ Grounding rules for Check 3.7**:
- Report ONLY statuses from the live DescribeInstance call made this session
- Do NOT infer sync health from TDG status, instance age, or resource counts
- If DescribeInstance fails: mark as `[Not checked — DescribeInstance unavailable]`
- `ResourceConflictException` (HTTP 409) in CloudTrail is BENIGN — never report as an error
- `responseElements: null` on sync events is normal for DELETE operations — not a failure signal

## Findings Summary

| Finding | Trigger | Severity |
|---------|---------|----------|
| REL-001 | No TDG for production instance | 🔴 Critical |
| REL-002 | Production phone numbers not in TDG | 🔴 Critical |
| REL-003 | Lambda DLQ missing | 🟠 High |
| REL-004 | Lambda timeout exceeds the flow block max (8s sync / 60s async) | 🟠 High |
| REL-005 | No alarm on QueueSize | 🟡 Medium |
| REL-006 | ConcurrentCalls >80% quota | 🟡 Medium |
| REL-007 | Real-time metrics need elevated role | 🟡 Medium |
| REL-008 | No holiday overrides in HoO | 🟢 Low |
| REL-009 | No ReplicationConfiguration block | 🟠 Medium |
| REL-010 | Status = IN_PROGRESS | 🟡 Info |
| REL-011 | Status = FAILED or DELETION_FAILED | 🔴 Critical |
| REL-012 | Status = NOT_STARTED | 🟠 Medium |
| REL-013 | COMPLETE but 0 sync events in 30 min | 🟠 Medium |

## DR Readiness Summary Table

| Capability | Status |
|-----------|--------|
| Multi-region (TDG) | {✅ / ❌} |
| Phone failover | {✅ / ❌} |
| Agent failover | {✅ / ❌} |
| ACGR sync | {✅ COMPLETE / ⚠️ WARNING / ❌ FAILED / ➖ NOT_CONFIGURED / — SKIPPED} |
| Lambda DLQ | {✅ / ❌} |
| Capacity monitoring | {✅ / ❌} |

## Timeout Priority

```
MUST RUN:    3.1 (TDG) → 3.2 (Phone resilience)
HIGH VALUE:  3.7 (ACGR) — 1 API call, high signal
PARALLEL:    3.3, 3.4, 3.5
DROP LAST:   3.6 (no API calls, derive from Phase 0 data)
```

## Retry Policy (Pillar 3 Specific)

```
RETRY (once, 2s wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, session policy errors

Check 3.7: DescribeInstance failure → mark [Not checked], continue
Check 3.7: CloudTrail LookupEvents failure → skip Step 3, use Step 2 status only
Check 3.5: GetCurrentMetricData failure → skip, use CloudWatch only
Check 3.4: lambda:GetFunction failure → skip Check 3.4 entirely
```
