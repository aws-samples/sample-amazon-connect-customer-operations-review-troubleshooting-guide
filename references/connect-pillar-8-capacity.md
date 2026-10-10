# Amazon Connect Operations Review — Pillar 8: Capacity Management

## Description

Assesses whether the contact centre can absorb its expected load: the binding
constraint on each channel, headroom against applied service quotas, queue
ceilings, and whether workforce capacity planning is provisioned at all.

Distinct from Pillar 3 (Reliability), which asks *will it survive a failure*.
This pillar asks *will it survive success* — a volume increase, a campaign, a
seasonal peak.

## When to Use

- Runs for instances classified as "Production" or "DR Replica"
- User asks about capacity, headroom, scaling, concurrency, staffing, or
  "can we handle more volume"
- Before a planned campaign, launch, or migration wave

## Execution Strategy

```
Budget: 90 seconds
APIs: ~20 calls
Depends on: Phase 0 output (instance list, user/queue/routing-profile counts)
Condition: Production or DR Replica; skip for abandoned instances

Parallelization plan:
  Sequential:  8.1 → 8.2  (8.2 consumes 8.1's per-agent concurrency)
  Parallel:    8.3 + 8.4 + 8.5 + 8.6
  Estimated wall time: ~60 seconds on fast path
```

## Pre-Flight (5 seconds)

```
Test 1: servicequotas:ListServiceQuotas (ServiceCode=connect, MaxResults=1)
  - SUCCESS → quota-based checks available
  - AccessDeniedException → skip 8.3; add the permission to the IAM gap list.
    Do NOT substitute documented default quota values.

Test 2: connect:DescribeRoutingProfile on the first profile from Phase 0
  - SUCCESS → per-agent concurrency available; 8.1 and 8.2 can run
  - AccessDeniedException → skip 8.1 and 8.2, note in output

Test 3: connect:GetCurrentMetricData with a Queues filter (MaxResults=1)
  - SUCCESS → live occupancy available, run 8.5 in full
  - AccessDeniedException or session-policy error → mark 8.5
    "REQUIRES_ELEVATED_ROLE" and continue. DO NOT retry.
  - NOTE: this call REQUIRES at least one Queues or RoutingProfiles filter
    value. Calling it without one returns InvalidParameterException, which is
    a malformed request, not a permissions problem — do not report it as one.

Test 4: connect:GetMetricDataV2 (1 metric, 1 queue, 1 day)
  - SUCCESS → historical trending available, run 8.6
  - AccessDeniedException → skip 8.6, note in output
```

## Checks

### Check 8.1 — Per-Agent Concurrent Capacity (15 seconds max)

**API calls**:
```
connect:ListRoutingProfiles          (MaxResults up to 1000)
connect:DescribeRoutingProfile       (per profile)
  EXTRACT: RoutingProfile.MediaConcurrencies[]
             .Channel          (VOICE | CHAT | TASK | EMAIL)
             .Concurrency      (contacts an agent may hold on that channel)
             .CrossChannelBehavior.BehaviorType
```

**Checks**:
- [ ] Per-channel concurrency for every routing profile
- [ ] `CrossChannelBehavior` — `ROUTE_ANY_CHANNEL` vs
      `ROUTE_CURRENT_CHANNEL_ONLY`
- [ ] Profiles whose concurrency differs materially from their peers
- [ ] VOICE concurrency > 1 (unusual; voice is normally 1)

**Findings**:
- Profiles mixing `ROUTE_ANY_CHANNEL` and `ROUTE_CURRENT_CHANNEL_ONLY` = CAP-004
- `ROUTE_CURRENT_CHANNEL_ONLY` on a multi-channel profile caps blended
  utilisation — report as CAP-004, not as a defect, because it is frequently a
  deliberate policy choice. State the observation and ask.

### Check 8.2 — Binding Constraint Per Channel (20 seconds max)

**This is the pillar's primary output.** It establishes, per channel, whether
the ceiling is the agent pool or the service quota. Every input is read-only.

**API calls**:
```
connect:ListUsers                    (MaxResults up to 1000; paginate)
connect:DescribeUser                 (per user → RoutingProfileId)
  + Check 8.1 MediaConcurrencies
  + Check 8.3 applied quota values
```

**Derivation**:
```
for each channel C:
    agent_capacity(C) = Σ over routing profiles P of
                        ( concurrency(P, C) × agents_assigned_to(P) )
    quota(C)          = applied value of "Concurrent active <C> per instance"
    binding(C)        = AGENT_POOL   if agent_capacity(C) < quota(C)
                        SERVICE_QUOTA otherwise
    headroom(C)       = min(agent_capacity(C), quota(C))
```

Report as a table with the real numbers:

```
| Channel | Agent capacity | Applied quota | Binding constraint | Effective ceiling |
|---|---|---|---|---|
| VOICE | 5 | 10 | agent pool | 5 |
```

(Illustration of format only — never copy these numbers.)

**Checks**:
- [ ] Binding constraint identified for every channel in use
- [ ] Channels where the quota is the constraint — these need a quota increase
- [ ] Channels where the agent pool is the constraint — these need hiring or a
      concurrency change, and a quota increase would achieve nothing

**Findings**:
- Quota is the binding constraint on a production channel = CAP-001
- Agent pool is the binding constraint = CAP-002 (informational unless the
  customer has stated a target volume; see must-ask below)
- A channel is enabled on a routing profile but has zero assigned agents =
  CAP-003

**Error handling**:
- If `DescribeUser` is denied, agent-to-profile assignment is unknown. Report
  `Data unavailable — agent assignment not retrievable` and do NOT compute a
  binding constraint from the user count alone; users on different profiles
  have different concurrency.

### Check 8.3 — Applied Quota Headroom (15 seconds max)

**Requires**: `servicequotas:ListServiceQuotas` (Pre-Flight Test 1).

**CRITICAL RULE — never hardcode a quota value.** Applied quotas are
per-account and per-region and are routinely raised above AWS defaults. Every
number in this check MUST come from the live response in this session. If the
call fails, the check did not run — do not substitute a documented default.

#### Preferred: fetch the quotas you need directly (4 calls, no pagination)

`ListServiceQuotas` enumerates everything; `GetServiceQuota` fetches one quota
by code. A capacity review needs a handful, so fetch them directly and skip the
enumeration entirely:

```
servicequotas:GetServiceQuota
  ServiceCode: connect
  QuotaCode:   <code from the table below>
  EXTRACT: Quota.Value, Quota.Adjustable, Quota.QuotaName
```

| Quota | QuotaCode |
|---|---|
| Concurrent active calls per instance | `L-12AB7C57` |
| Concurrent active chats per instance | `L-D4BA6F6E` |
| Concurrent active tasks per instance | `L-60553137` |
| Phone numbers per instance | `L-8F812903` |

**Quota codes are stable AWS identifiers and are safe to use as lookup keys.
Quota _values_ are not** — the `CRITICAL RULE` above still applies in full. The
code tells you which quota to ask for; only the live response tells you its
limit. Never carry a value over from this file or from AWS documentation.

If a `QuotaCode` returns `NoSuchResourceException`, that quota is not
provisioned for this account — see Check 8.7 for what that means. Fall back to
the enumeration below if you need a quota not listed here.

#### Fallback: full enumeration

```
servicequotas:ListServiceQuotas
  ServiceCode: connect
  MaxResults:  100            ← hard maximum
```

⚠️ **This is a paginated call, and it pages far more than the quota count
suggests.** Amazon Connect publishes about 338 quotas, but the service returns
roughly 30 per response regardless of `MaxResults`, so a full enumeration takes
**about 11 round trips, not four.** Ten or twelve pages is normal and is not
evidence of a pagination loop — do not abandon the enumeration or report it as
malfunctioning on page count alone. The only real loop signal is a repeated
`QuotaCode` across pages; absent that, keep going until a response omits
`NextToken`.

How many pages you observe depends on which layer you call:

| Caller | Pages observed | Why |
|---|---|---|
| SDK / raw API with `MaxResults: 100` | ~11 | each response carries ~30 quotas |
| `aws` CLI with `--page-size 100 --max-items 100` | 4 | `--max-items` aggregates several service round trips per returned page |
| `aws` CLI with no paging flags | 1 | the CLI auto-paginates internally and returns the full set |

All four behaviours are correct. **If you are using the CLI and only need the
full list, issue the call with no paging flags and let it aggregate** — then
the pagination discipline below does not apply at all, and the 338 quotas
arrive in one result.

Pass `NextToken` only when the immediately preceding response returned one, use
it verbatim, and stop when a response has no `NextToken`. Reusing or
synthesising a token returns `InvalidPaginationTokenException`. Accumulate all
pages before reasoning.

**Do not omit `MaxResults`.** Left unset the page size drops further, inflating
the round trips roughly fourfold for the same data.

Of those ~338 quotas only about **55 are capacity limits**; the other ~283 are
`Rate of <Api> API requests` throttle limits irrelevant to this check. **Discard
every quota whose `QuotaName` begins with `Rate of`** and work only with the
remainder. If a response projection or `--query` is available, filter
server-side; otherwise filter the accumulated list. Do not summarise the
throttle quotas. The channel-concurrency quotas that Check 8.2 depends on sort
late in the enumeration, which is another reason to prefer the direct fetch
above when those are all you need.

**Map quota names to Phase 0 counts** (exact `QuotaName` match):

| QuotaName | Count source |
|---|---|
| `Users per instance` | `connect:ListUsers` |
| `Queues per instance` | `connect:ListQueues` |
| `Routing profiles per instance` | `connect:ListRoutingProfiles` |
| `Contact flows per instance` | `connect:ListContactFlows` |
| `Flow modules per instance` | `connect:ListContactFlowModules` |
| `Quick connects per instance` | `connect:ListQuickConnects` |
| `Hours of operation per instance` | `connect:ListHoursOfOperations` |
| `Phone numbers per instance` | `connect:ListPhoneNumbersV2`, filtered to numbers whose `TargetArn` is this instance |
| `AWS Lambda functions per instance` | `connect:ListLambdaFunctions` |
| `Amazon Lex bots per instance` | `connect:ListBots` |
| `Security profiles per instance` | `connect:ListSecurityProfiles` |
| `Amazon Connect instance count` | `connect:ListInstances` (account, per region) |

⚠️ **Counts are the numerator of every utilisation figure — measure, don't
estimate.** Count the length of the accumulated array. Never write a count as
a range or a hedge; an approximate numerator makes the percentage unusable.
Several list operations cap `MaxResults` well below 1000 and either hard-fail
or silently truncate above it:

| Operation | MaxResults max |
|---|---|
| `connect:ListInstances` | **10** |
| `connect:ListLambdaFunctions` | **25** |
| `connect:ListBots` | **25** |
| `servicequotas:ListServiceQuotas` | **100** |
| most other `connect:List*` | 1000 |

`ListInstances` capping at 10 matters especially here, because instance count
is itself a quota being measured: a truncated first page reports an account as
exactly at its limit when it may be over.

**Severity bands**:

| Utilisation | Severity | Meaning |
|---|---|---|
| ≥100% | 🔴 Critical | at or over the limit — creates are already failing |
| 80–99% | 🟠 High | request an increase now; lead time is days |
| 60–79% | 🟡 Medium | track it; plan before the next growth event |
| <60% | ✅ | adequate headroom, no finding |

**Findings**:
- Any resource ≥100% of its applied quota = CAP-005
- 80–99% = CAP-006
- 60–79% = CAP-007
- ≥80% **and** `Adjustable: false` = CAP-008 — no increase is possible, so the
  remedy is architectural, not a support ticket

**Interpreting ≥100%**: a count above the applied quota is a real observable
state, not an arithmetic error. It occurs when a quota was lowered after
resources were created, or they were created under a higher limit. Report the
numbers and the consequence — new creates will be rejected — but do not assert
which cause applies without CloudTrail evidence.

**Error handling**:
- `AccessDeniedException` → `[Not checked — servicequotas:ListServiceQuotas denied]`
- `InvalidPaginationTokenException` → restart from page one with no token and
  follow tokens strictly in order. If it recurs, mark `[Not checked —
  pagination failed]`. Do not retry with another token.
- `InvalidRequestException — Result Size cannot be larger than N` → your
  `MaxResults` exceeded that operation's cap. Re-issue with `MaxResults: N`.
- A partial enumeration is **not** a usable count. Report
  `Data unavailable — enumeration incomplete` rather than a partial total.

### Check 8.4 — Queue Depth Ceilings (10 seconds max)

**API calls**:
```
connect:ListQueues        --queue-types STANDARD
connect:DescribeQueue     (per queue)
  EXTRACT: Queue.MaxContacts, Queue.Status, Queue.HoursOfOperationId
```

**Checks**:
- [ ] `MaxContacts` set or unset per queue
- [ ] Queues with `Status: DISABLED` that still have routing profile references
- [ ] Queues with no `HoursOfOperationId`

**Findings**:
- `MaxContacts` unset on a production queue = CAP-009. An unset ceiling means
  the queue accepts contacts without bound, so overflow handling never
  triggers and callers queue indefinitely instead of being routed to an
  alternative. Report the count of affected queues.
- Queue `DISABLED` but still referenced by a routing profile = CAP-010

### Check 8.5 — Live Occupancy (15 seconds max)

**Requires**: `connect:GetCurrentMetricData` (Pre-Flight Test 3).

**API calls**:
```
connect:GetCurrentMetricData
  InstanceId: <instance-id>
  Filters:    { "Queues": [<queue-id>, ...] }      ← REQUIRED, at least one
              { "Channels": ["VOICE"] }             ← optional
  CurrentMetrics:
    AGENTS_AVAILABLE, AGENTS_ONLINE, AGENTS_STAFFED,
    CONTACTS_IN_QUEUE, OLDEST_CONTACT_AGE
```

**Checks**:
- [ ] Agents online vs agents staffed — unstaffed headroom
- [ ] Contacts in queue vs the Check 8.2 effective ceiling
- [ ] Oldest contact age against the customer's stated SLA (must-ask)

**Findings**:
- Agents online at or near the effective ceiling = CAP-011

⚠️ **If you recommend a concurrency alarm, get the unit right.**
`ConcurrentCallsPercentage` and `ConcurrentHighVolumeCallsPercentage` emit a
**decimal** (0.85 means 85%); `ConcurrentActiveChatsPercentage`,
`ConcurrentEmailsPercentage` and `ConcurrentTasksPercentage` emit an **integer**
(85 means 85%). A threshold of `80` on a voice percentage metric requires 8000%
utilisation and will never fire. Use `0.8` for voice, `80` for the others, or
avoid the ambiguity entirely by alarming on the level metric
(`ConcurrentCalls`) against the applied quota value from Check 8.3.

**Error handling**:
- Session policy error or `AccessDeniedException` → mark
  `[Not checked — REQUIRES_ELEVATED_ROLE]`. DO NOT retry, and do not fall back
  to `GetMetricDataV2` as a substitute: it answers a different question
  (historical, not current).
- A metric with no datapoints means no traffic of that type right now, which is
  not the same as zero utilisation. State which one you observed.

### Check 8.6 — Volume Trend and Growth Headroom (15 seconds max)

**Requires**: `connect:GetMetricDataV2` (Pre-Flight Test 4).

**API calls**:
```
connect:GetMetricDataV2
  ResourceArn: <instance-arn>
  StartTime / EndTime: last 14 days (or the longest window permitted)
  Interval:  { "IntervalPeriod": "DAY" }
  Filters:   [{ "FilterKey": "QUEUE", "FilterValues": [<queue-id>, ...] }]
  Groupings: ["QUEUE"]
  Metrics:   CONTACTS_HANDLED, MAX_QUEUED_TIME,
             SERVICE_LEVEL (Threshold LT <sla_seconds>)
```

`SERVICE_LEVEL` requires a threshold value. Use the customer's stated SLA — it
is a must-ask (below), not a default. Do not assume 20 or 30 seconds.

**Checks**:
- [ ] Peak day vs mean day over the window
- [ ] Peak concurrent demand vs the Check 8.2 effective ceiling
- [ ] Trend direction over the window

**Findings**:
- Observed peak within 20% of the effective ceiling = CAP-012
- Fewer than 7 days of data available = CAP-013, and no trend may be asserted

**Error handling**:
- Zero datapoints across the whole window means the instance carried no traffic
  of that type. Report that as an observation — it materially changes how
  urgent every other capacity finding is — and do not infer a trend.

### Check 8.7 — Workforce Capacity Planning Provisioning (5 seconds max)

Amazon Connect's Forecasting, Capacity Planning and Scheduling feature has **no
public read API**. There is no `List`/`Describe` operation for forecasts,
schedules, staffing groups or capacity plans, so their content cannot be
assessed by an agent. What *is* observable is whether the feature is
provisioned for the account.

**Derivation** (no additional API call — reuses Check 8.3 plus one more):
```
servicequotas:ListAWSDefaultServiceQuotas  ServiceCode=connect
  → compare the set of QuotaNames against the applied set from Check 8.3
  → capacity-planning quota names (Forecast groups per instance, Schedules per
    instance, Staffing groups per instance, Shift profiles per instance,
    Agents per schedule, Capacity plans per instance, and similar) that exist
    as AWS defaults but are ABSENT from the applied list indicate the feature
    is not provisioned for this account.
```

⚠️ **Judge this on the bulk, not on any single quota.** The two lists differ by
more than this feature, and a handful of capacity-planning-adjacent quotas stay
in the applied list even when the feature is not provisioned — on a
known-unprovisioned instance, four of roughly two dozen were still applied
(including `Scheduled reports per instance`, which is a reporting limit, and
`Demand groups per forecast group`). So:

- **Not provisioned** = the large majority of capacity-planning quota names are
  absent from the applied list.
- Finding one such name in the applied list does **not** establish that the
  feature is provisioned. Do not conclude from a single hit.

Equivalently, `servicequotas:GetServiceQuota` on a capacity-planning
`QuotaCode` returns `NoSuchResourceException` when the feature is not
provisioned, which is a cheaper probe than the full set diff if you already
have a code to hand. Apply the same rule: probe several, judge on the pattern.

**Checks**:
- [ ] Capacity-planning quotas present in defaults but absent from applied
- [ ] `Scheduled reports per instance` utilisation, which *is* applied and
      readable

**Findings**:
- Production instance with no capacity-planning provisioning = CAP-014 🟢 Low.
  This is an observation, not a defect: many contact centres run workforce
  management in an external tool. Report it and ask rather than recommending
  enablement.

**Hard boundary — state this in the output.** Forecast accuracy, schedule
adherence, shrinkage and staffing adequacy **cannot be assessed from the API**.
If the customer asks about them, say so plainly and route them to the Connect
console or their AWS account team. Do not infer staffing adequacy from agent
headcount: headcount is not a schedule.

## Must-Ask Inputs

These values are not in any API and must be asked explicitly. Do not default
them, and do not derive a finding that depends on one until it is answered.

| Input | Why it cannot be inferred | Blocks |
|---|---|---|
| Target service level and answer-time SLA | Contractual or operational policy; not stored in Connect | 8.6 SERVICE_LEVEL, CAP-011 |
| Expected volume growth or seasonality | A business forecast | CAP-002, CAP-012 |
| Shrinkage and occupancy targets | Workforce-management policy | staffing adequacy |
| Planned campaigns or launches in the window | External to Connect | CAP-012 |

An unanswered must-ask makes the dependent finding `BLOCKED`, never a pass.

## Findings Summary

| Finding | Trigger | Severity |
|---------|---------|----------|
| CAP-001 | Service quota is the binding constraint on a production channel | 🟠 High |
| CAP-002 | Agent pool is the binding constraint | 🟡 Medium |
| CAP-003 | Channel enabled on a routing profile with zero assigned agents | 🟡 Medium |
| CAP-004 | Mixed or restrictive `CrossChannelBehavior` across profiles | 🟢 Low |
| CAP-005 | Resource count ≥100% of applied quota | 🔴 Critical |
| CAP-006 | Resource count 80–99% of applied quota | 🟠 High |
| CAP-007 | Resource count 60–79% of applied quota | 🟡 Medium |
| CAP-008 | ≥80% of a quota with `Adjustable: false` | 🔴 Critical |
| CAP-009 | Production queue with no `MaxContacts` ceiling | 🟡 Medium |
| CAP-010 | Disabled queue still referenced by a routing profile | 🟡 Medium |
| CAP-011 | Agents online at or near the effective ceiling | 🟠 High |
| CAP-012 | Observed peak within 20% of the effective ceiling | 🟠 High |
| CAP-013 | Fewer than 7 days of metric history available | 🟡 Info |
| CAP-014 | No workforce capacity-planning provisioning | 🟢 Low |
| CAP-015 | `servicequotas:ListServiceQuotas` denied — headroom unknown | 🟡 Medium |

**CAP-005 through CAP-008 and CAP-015 require live values from Check 8.3.** If
8.3 did not run, these findings cannot be raised. Never raise a quota finding
from a remembered default.

## Capacity Summary Table

| Dimension | Status |
|-----------|--------|
| Binding constraint identified per channel | {✅ / ➖ NOT CHECKED} |
| Quota headroom | {✅ all <60% / ⚠️ 60–99% / ❌ ≥100% / ➖ NOT CHECKED} |
| Queue ceilings set | {✅ / ❌ / ➖} |
| Live occupancy visibility | {✅ / ⚠️ REQUIRES_ELEVATED_ROLE} |
| Volume trend available | {✅ / ⚠️ <7 days / ➖} |
| Workforce planning provisioned | {✅ / ➖ NOT PROVISIONED / — NOT ASSESSABLE} |

## Timeout Priority

```
MUST RUN:    8.2 (binding constraint) → 8.3 (quota headroom)
HIGH VALUE:  8.1 (per-agent concurrency) — 8.2 depends on it
HIGH VALUE:  8.4 (queue ceilings) — cheap, high signal
PARALLEL:    8.5, 8.6
DROP FIRST:  8.7 (provisioning), then 8.6 (trend)
```

If a check must be dropped, report it as `[Not checked — time budget]`. Never
emit a capacity figure that was not measured.

## Retry Policy (Pillar 8 Specific)

```
RETRY (once, 2s wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, session policy errors,
              InvalidPaginationTokenException

Check 8.2: DescribeUser failure → no binding constraint, mark Data unavailable
Check 8.3: pagination failure → [Not checked], never a partial total
Check 8.5: GetCurrentMetricData denial → REQUIRES_ELEVATED_ROLE, continue
Check 8.6: GetMetricDataV2 denial → skip 8.6 entirely
Check 8.7: ListAWSDefaultServiceQuotas denial → skip, do not infer
```
