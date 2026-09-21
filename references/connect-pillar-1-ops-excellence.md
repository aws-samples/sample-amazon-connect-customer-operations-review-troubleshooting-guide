# Amazon Connect Operations Review — Pillar 1: Operational Excellence

## Description

Assesses Amazon Connect operational maturity: contact flow hygiene, monitoring coverage, logging, tagging, and change management readiness.

## When to Use

- Always runs (for any discovered instance)
- User asks about operational health, flow management, or monitoring gaps

## Execution Strategy

```
Budget: 90 seconds
APIs: ~18 calls (after shared data from Phase 0)
Depends on: Phase 0 output (instance list, shared flows/queues/routing data)
```

## Pre-Flight (5 seconds)

```
Test: connect:DescribeContactFlow on first flow from Phase 0 shared data
  - SUCCESS → proceed
  - AccessDeniedException → Mark pillar as "PARTIAL — List only, no Describe"
  - No flows in Phase 0 data → Skip flow detail checks
```

## Checks

### Check 1.1 — Contact Flow Hygiene (30 seconds max)

**Data source**: Phase 0 shared data (ListContactFlows result) + sampled DescribeContactFlow

**Sampling rule**: Describe UP TO 20 flows, prioritized:
1. Flows with State=ACTIVE and Type=CONTACT_FLOW (main IVR flows)
2. Flows with "error", "fail", "test", "copy", "old" in name
3. Most recently modified (if ModifiedTime available)

SKIP: State=ARCHIVED flows (don't describe them)

**From List data (no extra API calls)**:
- [ ] Total flow count — flag if >50 (complexity overhead)
- [ ] Naming convention — consistent prefix/pattern? Mixed case/formats?
- [ ] State distribution — how many ACTIVE vs ARCHIVED?
- [ ] Flow types — distribution of CONTACT_FLOW, CUSTOMER_QUEUE, CUSTOMER_HOLD, etc.

**From Describe data (sampled 20)**:
- [ ] Error handling — Does flow JSON contain error branch? (look for `"Errors"` key in Actions)
- [ ] Dead ends — Flows that terminate without Transfer/Disconnect/Queue action
- [ ] Hardcoded values — Phone numbers or ARNs hardcoded in flow JSON (should use contact attributes)
- [ ] Flow modules usage — Are reusable modules used or is everything inline?

**Response trimming**: From DescribeContactFlow, extract:
```
KEEP: Name, Id, Type, State, Tags, Content (parse for structure only)
ANALYZE from Content JSON: 
  - Count of Actions
  - Presence of error handling blocks
  - Lambda invocations (ARNs)
  - Set attributes actions
DISCARD: Raw Content JSON after analysis
```

### Check 1.2 — Contact Flow Modules (10 seconds max)

**API calls**: 
```
connect:ListContactFlowModules (MaxResults=100, 1 page)
```

**Checks**:
- [ ] Module count — 0 modules in a complex environment = reusability gap
- [ ] Status — any stuck in "saved" (not published)?
- [ ] Module-to-flow ratio — low ratio with many flows = copy-paste risk

### Check 1.3 — Queue & Routing Configuration (10 seconds max)

**Data source**: Phase 0 shared data (ListQueues, ListRoutingProfiles)

**No extra API calls needed. Analyze Phase 0 data**:
- [ ] Queue naming — consistent naming convention?
- [ ] Queue types — ratio of STANDARD to AGENT queues
- [ ] Routing profile count — >20 profiles may indicate drift
- [ ] Temp/test profiles — names containing "test", "temp", "copy", "default"

**Additional call (only if <5 routing profiles)**:
```
connect:DescribeRoutingProfile (for each profile)
  KEEP: Name, MediaConcurrencies (channels + concurrency values)
  CHECK: Is voice concurrency >1? (unusual, may be misconfigured)
```

### Check 1.4 — Monitoring & Alerting (20 seconds max)

**API calls**:
```
cloudwatch:DescribeAlarms 
  Filter: AlarmNamePrefix "Connect" OR Namespace "AWS/Connect"
  MaxResults: 100

cloudwatch:ListMetrics
  Namespace: "AWS/Connect"
  Extract: Which metrics are actively publishing
```

**Checks**:
- [ ] Alarm existence — MUST have alarms on:
  - `ContactFlowErrors` (CRITICAL if missing)
  - `ContactFlowFatalErrors` (CRITICAL if missing)
  - `MissedCalls` or `QueueSize` (HIGH if missing)
  - `ConcurrentCalls` / `ConcurrentCallsPercentage` (MEDIUM if missing)
- [ ] Alarm state — any in ALARM or INSUFFICIENT_DATA?
- [ ] Custom metrics — any custom namespace metrics for Connect?

### Check 1.5 — Logging (15 seconds max)

**API calls**:
```
logs:DescribeLogGroups
  LogGroupNamePrefix: "/aws/connect/"
  MaxResults: 50
```

**Checks**:
- [ ] Log group exists per instance — `/aws/connect/{instanceId}` 
- [ ] Contact flow logging enabled — cross-ref with Phase 0 `CONTACTFLOW_LOGS` attribute
- [ ] If CONTACTFLOW_LOGS=true but no log group → something is wrong
- [ ] If CONTACTFLOW_LOGS=false → CRITICAL finding (flow errors invisible)

**Error handling**: 
- If `logs:DescribeLogGroups` fails with tag condition error → note "Log group verification blocked by IAM tag condition" and move on

### Check 1.6 — Tagging & Change Management (5 seconds max)

**Data source**: Phase 0 shared data (ListTagsForResource)

**No extra API calls. Analyze Phase 0 tags**:
- [ ] Required tags present: `Environment`, `Owner`, `Application`
- [ ] Cost allocation tags: `CostCenter` or `Project`
- [ ] IaC indicators: `aws:cloudformation:stack-name` or `terraform` tags
- [ ] No tags at all = no change management visibility

### Check 1.7 — Traffic Distribution Groups (5 seconds max)

**API calls**:
```
connect:ListTrafficDistributionGroups (if not already in Phase 0)
  MaxResults: 10
```

**Checks**:
- [ ] Production instance has TDG → DR capability exists
- [ ] Production instance WITHOUT TDG → flag for Pillar 3 (Reliability)

## Findings Output Format

```markdown
## Pillar 1: Operational Excellence — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- APIs timed out: {n}
- Assessment completeness: {%}

### Findings

#### 🔴 CRITICAL
- [OPS-001] Contact flow logging DISABLED on instance {alias}
  - Impact: Flow errors are invisible. Cannot troubleshoot customer-impacting issues.
  - API: DescribeInstanceAttribute(CONTACTFLOW_LOGS) = false
  - Fix: Enable contact flow logs in instance settings
  
- [OPS-002] No CloudWatch alarms for ContactFlowErrors
  - Impact: Flow failures go undetected until customers complain.
  - API: cloudwatch:DescribeAlarms returned 0 alarms for AWS/Connect namespace
  - Fix: Create alarm on ContactFlowErrors metric, threshold > 0, period 5 min

#### 🟡 HIGH
- [OPS-003] {n} flows have no error handling branches
  - Impact: Unhandled errors drop customers without graceful fallback.
  - Flows: {list top 5 names}
  - Fix: Add error branch with transfer to fallback queue

#### 🟡 MEDIUM
- [OPS-004] No IaC tags detected — manual change management
- [OPS-005] {n} test/copy flows in production instance
- [OPS-006] 0 contact flow modules — no reusability

#### 🟢 LOW
- [OPS-007] {n} routing profiles (consider consolidation if >15)

### Recommendations (Prioritized)
1. Enable contact flow logging immediately
2. Create minimum viable alarm set (FlowErrors, FatalErrors, MissedCalls)
3. Add error handling to top 5 most-used flows
4. Implement tagging strategy for change tracking
5. Create reusable modules for common patterns (authentication, hours check)
```

## Timeout Handling

```
At 70 seconds: Stop issuing new API calls.
At 80 seconds: Produce findings from data collected so far.
Uncompleted checks: Mark as "NOT_ASSESSED: timeout" in output.
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, ResourceNotFoundException
SKIP ENTIRE CHECK if pre-flight for that check fails.
```