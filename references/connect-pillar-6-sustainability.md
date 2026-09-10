# Amazon Connect Operations Review — Pillar 6: Sustainability

## Description

Assesses Amazon Connect resource efficiency and environmental impact: instance consolidation, channel optimization (async vs real-time), self-service adoption, AI-driven containment, and demand-aligned capacity.

## When to Use

- Runs when >1 instance exists (consolidation opportunities)
- User asks about sustainability, efficiency, or resource consolidation

## Execution Strategy

```
Budget: 60 seconds
APIs: ~8 calls
Depends on: Phase 0 output (instance list, classification, queues, flows, integrations)
Condition: Runs if >1 instance discovered OR user explicitly requests
```

## Pre-Flight (3 seconds)

```
Phase 0 data check:
  - >1 instance → proceed (consolidation analysis relevant)
  - 1 instance → proceed with channel/self-service checks only (skip consolidation)
  - AI integrations present → include AI containment checks
```

## Checks

### Check 6.1 — Instance Consolidation Opportunity (10 seconds max)

**Data source**: Phase 0 shared data only — NO extra API calls

**Checks**:
- [ ] Multiple instances in same region → could they be consolidated?
- [ ] Dev + Production in same region → expected, but review if dev is idle
- [ ] Instances with overlapping functionality (same queues/flow names) → merge candidate
- [ ] Abandoned instances (0 users, 0 queues) → delete candidates
- [ ] Unused features enabled — VOICEID enabled but no Voice ID integration?

**Analysis criteria**:
- Same-region instances with <5 users each → strong consolidation signal
- Instances with identical routing profile names → likely cloned, one may be stale
- Feature flags enabled but no corresponding integration → wasted feature surface

**Findings**:
- Multiple low-use instances in same region = 🟡 MEDIUM (consolidation reduces management overhead)
- Features enabled but unused = 🟢 LOW (no direct resource cost, but complexity)

### Check 6.2 — Async Channel Adoption (10 seconds max)

**Data source**: Phase 0 shared data (ListQueues)

**No extra API calls — analyze queue types from Phase 0**:

**Checks**:
- [ ] Chat queues present → async channel available (lower per-interaction cost)
- [ ] Task queues present → async work routing available
- [ ] Voice-only (0 chat/task queues) → all interactions synchronous, higher resource per contact
- [ ] Chat:Voice queue ratio → higher async ratio = more sustainable

**Sustainability rationale**:
- Voice: Real-time, 1:1 agent:customer, full agent attention per call
- Chat: Async-capable, agents handle 3-5 concurrent, lower per-contact resource
- Tasks: Fully async, no real-time interaction needed

**Findings**:
- Voice-only instance (0 chat queues) = 🟡 MEDIUM (no async channel, all contacts require real-time agent)
- Chat queues present = ✅ (async channel adopted)
- Task routing present = ✅ (async work management adopted)

### Check 6.3 — Self-Service & Bot Containment (10 seconds max)

**Data source**: Phase 0 shared data (ListIntegrationAssociations) + targeted call

**API calls**:
```
connect:ListBots OR connect:ListLexBots (MaxResults=10)
```

**Checks**:
- [ ] Bot presence on production instance → self-service layer exists
- [ ] No bots → 100% of contacts handled by human agents (highest resource per contact)
- [ ] Bot count vs queue count → adequate coverage?
- [ ] Bot language support → matches customer demographics?

**Sustainability rationale**:
- Bot-contained contact: seconds of compute, no agent time
- Agent-handled contact: minutes of human time + infrastructure
- Every 10% containment improvement = significant resource reduction

**Findings**:
- No bots on production instance = 🟡 MEDIUM (every contact requires human agent)
- Bot exists = ✅ (check containment rate in Pillar 4 if metrics available)

### Check 6.4 — AI-Driven Efficiency (10 seconds max)

**Condition**: Only if Phase 0 found WISDOM_ASSISTANT or Q_IN_CONNECT integrations.

**API calls**:
```
wisdom:ListAIAgents (MaxResults=10)
wisdom:GetAIAgent (for first agent found)
  KEEP: Name, Type, State, Configuration
```

**Checks**:
- [ ] AI agent type — CUSTOMER_SELF_SERVICE (containment) vs AGENT_ASSIST (efficiency)
- [ ] Self-service AI agent → reduces need for human agents entirely
- [ ] Agent assist AI → reduces handle time, increases throughput
- [ ] AI agent state — ACTIVE (delivering value) vs DRAFT (not yet deployed)
- [ ] Multiple AI agents → segmented use cases, higher overall containment potential

**Sustainability rationale**:
- Customer self-service AI: highest efficiency — no human agent at all
- Agent assist AI: reduces AHT by 20-40%, same agents handle more contacts
- DRAFT AI agents: built but not delivering value yet

**Findings**:
- Self-service AI agent active = ✅ EXCELLENT (automated containment)
- Agent assist active = ✅ GOOD (AHT reduction)
- AI agent in DRAFT state = 🟡 MEDIUM (investment made but not deployed)
- AI integration exists but 0 AI agents configured = 🟡 HIGH (integration without implementation)

### Check 6.5 — Hours of Operation vs Demand Alignment (10 seconds max)

**API calls**:
```
connect:DescribeHoursOfOperation (for primary HoO, max 3)
  KEEP: Name, TimeZone, Config (days + hours)
```

**Checks**:
- [ ] 24/7 HoO with no self-service → agents staffed round-the-clock?
- [ ] Extended hours (>16h/day) without AI/bots → high agent cost outside peak
- [ ] Multiple HoOs with different hours → demand-aligned routing (good)
- [ ] Single HoO applied to all queues → no differentiation by demand pattern

**Sustainability rationale**:
- 24/7 human staffing without AI: maximum resource consumption
- 24/7 with AI self-service for off-hours: efficient (AI handles low-volume periods)
- Demand-aligned hours with overflow to AI: optimal

**Findings**:
- 24/7 HoO + no bots + no AI = 🟡 MEDIUM (consider AI for off-peak hours)
- Demand-aligned HoOs with AI fallback = ✅ GOOD

### Check 6.6 — Campaign Efficiency (5 seconds max)

**Condition**: Only if Phase 0 found CONNECT_CAMPAIGNS integration.

**Data source**: Phase 0 integrations data + Phase 5 campaign data if available

**No extra API calls — use data from Phase 5 if it ran, otherwise**:
```
connectcampaignsv2:DescribeCampaign (for first campaign, max 1)
  KEEP: DialerConfig type only
```

**Checks**:
- [ ] Agentless campaigns → lowest resource per outbound contact
- [ ] Predictive dialer → efficient use of agent time (less idle)
- [ ] Progressive dialer → more agent idle time, but better customer experience
- [ ] Agentless option available but using Progressive for notification-only → inefficiency

**Findings**:
- Notification-only use case using agent-based dialer = 🟢 LOW (switch to agentless)
- Agentless for automated messages = ✅ (efficient)

## Findings Output Format

```markdown
## Pillar 6: Sustainability — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- Assessment completeness: {%}

### Efficiency Profile
| Dimension | Status | Impact |
|-----------|--------|--------|
| Instance consolidation | {Opportunity / Optimized} | Mgmt overhead |
| Async channels (chat/task) | {Adopted / Voice-only} | Resource per contact |
| Self-service (bots) | {Present / Absent} | Agent requirement |
| AI containment | {Active / Draft / None} | Automation level |
| Demand-aligned hours | {Aligned / Always-on} | Off-peak efficiency |
| Campaign efficiency | {Agentless / Agent-based / N/A} | Outbound cost |

### Findings

#### 🟡 HIGH
- [SUS-001] AI integration configured but 0 AI agents deployed
  - Impact: Paid for integration setup but not delivering automated containment
  - Fix: Deploy at least one self-service AI agent for common intents

#### 🟡 MEDIUM
- [SUS-002] Voice-only instance — no async channels configured
  - Impact: Every interaction requires real-time 1:1 agent engagement
  - Fix: Enable chat channel for text-based inquiries

- [SUS-003] 24/7 Hours of Operation with no self-service for off-peak
  - Impact: Human agents staffed for low-volume periods
  - Fix: Deploy bot/AI for off-peak containment, route to agents during business hours

- [SUS-004] {n} instances in same region — consolidation candidate
  - Impact: Management overhead, duplicated configuration
  - Fix: Evaluate merge feasibility for low-use instances

#### 🟢 LOW
- [SUS-005] AI agent in DRAFT state — not yet delivering value
- [SUS-006] Progressive dialer for notification-only campaign (could be agentless)
- [SUS-007] Features enabled but no corresponding integration (VOICEID without Voice ID)

### Recommendations (Prioritized)
1. Deploy self-service AI agent (highest containment impact)
2. Enable chat/task channels for async-eligible interactions
3. Add bot coverage for off-peak hours
4. Consolidate low-use instances in same region
5. Activate DRAFT AI agents or disable unused feature flags
```

## Timeout Handling

```
At 45 seconds: Stop issuing new API calls.
Priority order if timeout: 6.4 → 6.3 → 6.2 → 6.1 → 6.5 → 6.6
At 55 seconds: Produce findings from data collected so far.
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException
wisdom:* failure → skip Check 6.4, note in output
connectcampaignsv2:* failure → skip Check 6.6
```