# Amazon Connect Operations Review — Pillar 4: Performance Efficiency

## Description

Assesses Amazon Connect performance: routing efficiency, channel optimization, bot containment, campaign dialer configuration, real-time/historical metrics, and AI-assisted agent productivity.

## When to Use

- Runs for Production-classified instances
- User asks about performance, AHT, service levels, agent productivity, or bot efficiency

## Execution Strategy

```
Budget: 90 seconds
APIs: ~12 calls
Depends on: Phase 0 output (instance list, flows, queues, routing profiles)
Condition: Only for instances classified as "Production" or "Campaign"
```

## Pre-Flight (5 seconds)

```
Test: connect:GetMetricDataV2 with minimal request (1 metric, 1 hour, 1 queue)
  - SUCCESS → full performance analysis available
  - Session policy error → mark "Historical metrics: REQUIRES_ELEVATED_ROLE"
  - AccessDeniedException → mark "Historical metrics: NOT_AVAILABLE"
  In both failure cases: proceed with structural checks only (no metric data)
```

## Checks

### Check 4.1 — Routing Efficiency (15 seconds max)

**Data source**: Phase 0 shared data (ListRoutingProfiles) + targeted Describe

**API calls**:
```
connect:DescribeRoutingProfile (for each profile, max 10)
  KEEP: Name, DefaultOutboundQueueId, MediaConcurrencies, NumberOfAssociatedQueues
```

**Checks**:
- [ ] Channel configuration — Voice + Chat + Task concurrency settings
- [ ] Voice concurrency >1 — unusual, likely misconfigured (agents can't take 2 calls)
- [ ] Chat concurrency — typically 3-5, >8 may impact quality
- [ ] Task concurrency — typically 1-5
- [ ] Profile proliferation — >15 profiles with similar config = consolidation opportunity
- [ ] Default outbound queue — pointing to valid queue?
- [ ] Test/temp profiles — "test", "copy", "temp" in name in production instance

**Findings**:
- Voice concurrency >1 = 🟡 HIGH (misconfiguration)
- >15 profiles in production = 🟡 MEDIUM (drift, consolidation needed)
- Test profiles in production = 🟡 MEDIUM (cleanup)

### Check 4.2 — Contact Flow Complexity (10 seconds max)

**Data source**: Phase 0 shared data (ListContactFlows)

**No extra API calls — analyze from Phase 0 list data**:

**Checks**:
- [ ] Total active flow count — >50 = overhead, consider modularization
- [ ] Flow type distribution — CONTACT_FLOW should be <30% of total (rest should be queue/hold/whisper)
- [ ] If all flow types are CONTACT_FLOW — modules and specialized flows underused

**Findings**:
- >50 active flows = 🟡 MEDIUM (complexity, consider flow modules)
- >80% CONTACT_FLOW type = 🟢 LOW (specialized flow types underused)

### Check 4.3 — Bot & Self-Service Containment (15 seconds max)

**API calls**:
```
connect:ListBots OR connect:ListLexBots (depending on Lex version)
  MaxResults: 20
```

**If bots found**:
```
lex:DescribeBot (for each, max 3)
  KEEP: BotName, BotStatus, IdleSessionTTLInSeconds
```

**Checks**:
- [ ] Bot presence — production instance without bots = no self-service layer
- [ ] Bot status — AVAILABLE vs BUILDING vs FAILED
- [ ] Session timeout — too short (<120s) = customers cut off mid-conversation
- [ ] Multiple bots — is routing clear or overlapping?
- [ ] Bot language coverage — matches customer demographics?

**Findings**:
- No bots on production instance = 🟡 MEDIUM (no self-service containment)
- Bot in FAILED status = 🟡 HIGH (broken IVR path)

### Check 4.4 — Historical Metrics (25 seconds max)

**Condition**: Only if pre-flight GetMetricDataV2 succeeded.

**API calls**:
```
connect:GetMetricDataV2
  Metrics: 
    - AVG_HANDLE_TIME
    - SERVICE_LEVEL (20 seconds threshold)
    - AVG_ABANDON_TIME
    - ABANDONMENT_RATE
    - AGENT_OCCUPANCY
    - CONTACTS_HANDLED
  ResourceArn: Instance ARN
  StartTime: 24 hours ago
  EndTime: now
  Interval: TOTAL (single aggregate)
  Filters: top 5 queues from Phase 0
```

**Checks**:
- [ ] AHT — >600 seconds (10 min) for voice = HIGH, investigate
- [ ] Service level — <80% at 20 seconds = not meeting typical target
- [ ] Abandonment rate — >5% = HIGH, capacity or routing issue
- [ ] Agent occupancy — >90% = burnout risk, <50% = overstaffed
- [ ] Contact volume — baseline for capacity planning

**Error handling**: If GetMetricDataV2 returns session policy error → skip entire check, already noted in pre-flight.

**Response trimming**: Keep only metric name + value. Discard raw response envelope.

### Check 4.5 — Campaign Dialer Performance (10 seconds max)

**Condition**: Only if Phase 0 found CONNECT_CAMPAIGNS integration.

**API calls**:
```
connectcampaignsv2:ListCampaigns (MaxResults=10)
connectcampaignsv2:DescribeCampaign (for each, max 3)
  KEEP: Name, DialerConfig (type, bandwidth), Status
```

**Checks**:
- [ ] Dialer type — Predictive (most efficient), Progressive (safer), Agentless (no agent needed)
- [ ] Bandwidth allocation — too aggressive = abandoned outbound calls
- [ ] Campaign status — RUNNING campaigns with no scheduled contacts?
- [ ] Multiple campaigns on same instance — resource contention risk

**Findings**:
- Campaign stuck in RUNNING with no activity = 🟡 MEDIUM (resource waste)
- Aggressive predictive dialer bandwidth = 🟡 MEDIUM (customer experience risk)

### Check 4.6 — AI-Assisted Productivity (10 seconds max)

**Condition**: Only if Phase 0 found WISDOM_ASSISTANT or Q_IN_CONNECT integrations.

**API calls**:
```
wisdom:ListKnowledgeBases (MaxResults=10)
wisdom:GetKnowledgeBase (for each, max 3)
  KEEP: Name, Status, KnowledgeBaseType, LastContentModificationTime
```

**Checks**:
- [ ] Knowledge base status — ACTIVE or SYNC_FAILED?
- [ ] Last sync time — stale KB (>30 days since last content update) = outdated answers
- [ ] KB type — what source is feeding it? (S3, ServiceNow, etc.)
- [ ] Multiple KBs — proper segmentation or redundant?

**Findings**:
- KB in SYNC_FAILED = 🟡 HIGH (agents getting no recommendations)
- KB last updated >30 days = 🟡 MEDIUM (potentially outdated content)
- No KB on AI-enabled instance = 🟡 HIGH (Q has no knowledge to recommend)

## Findings Output Format

```markdown
## Pillar 4: Performance Efficiency — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- Historical metrics: {AVAILABLE / REQUIRES_ELEVATED_ROLE / NOT_AVAILABLE}
- Assessment completeness: {%}

### Key Metrics (if available)
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Handle Time | {n}s | <300s | {✅/⚠️/❌} |
| Service Level (20s) | {n}% | >80% | {✅/⚠️/❌} |
| Abandonment Rate | {n}% | <5% | {✅/⚠️/❌} |
| Agent Occupancy | {n}% | 70-85% | {✅/⚠️/❌} |

### Findings

#### 🔴 CRITICAL
- [PERF-001] Knowledge base in SYNC_FAILED status
  - Impact: AI agent cannot provide recommendations — agents operating without assist
  - Fix: Check KB source connectivity, re-trigger sync

#### 🟡 HIGH
- [PERF-002] Voice concurrency set to {n} (expected: 1)
- [PERF-003] Service level at {n}% (below 80% target)
- [PERF-004] No self-service bot configured

#### 🟡 MEDIUM
- [PERF-005] {n} routing profiles — consolidation opportunity
- [PERF-006] Agent occupancy at {n}% (burnout risk if >90%)
- [PERF-007] Knowledge base content >30 days stale

#### 🟢 LOW
- [PERF-008] >50 active contact flows (consider modularization)

### Recommendations (Prioritized)
1. Fix knowledge base sync failure immediately
2. Correct voice concurrency to 1 per routing profile
3. Investigate service level — routing or staffing issue
4. Deploy Lex bot for common self-service intents
5. Consolidate routing profiles with identical configurations
```

## Timeout Handling

```
At 70 seconds: Stop issuing new API calls.
Priority order if timeout: 4.4 → 4.1 → 4.6 → 4.3 → 4.5 → 4.2
At 80 seconds: Produce findings from data collected so far.
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, session policy errors
GetMetricDataV2 failure → skip Check 4.4 entirely
wisdom:* failure → skip Check 4.6 entirely
connectcampaignsv2:* failure → skip Check 4.5 entirely
```