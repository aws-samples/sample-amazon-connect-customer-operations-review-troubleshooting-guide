# amazon-connect-troubleshooting-guide
version: 2.1.0
updated: 2026-09-05
# Description: 
  Adaptive troubleshooting and remediation for Amazon Connect. Diagnoses issues from three
  entry points: a finding from an Amazon Connect Operations Review, a symptom the customer
  reports directly, or an unscoped "something is wrong" request. Resolves every threshold and
  applicability decision against the live instance profile rather than fixed defaults, so the
  same procedure produces different verdicts on a 20-call/day dev instance and a 50k-call/day
  production instance. Read-only by default; every write passes a two-gate confirmation.
  Platform-agnostic — usable by any AI tool with AWS CLI/SDK access.
# Compatibility: 
  Requires AWS CLI/SDK read access to connect, wisdom, cloudwatch, logs, cloudtrail, s3, kms,
  lambda, lex, service-quotas, ce, cloudformation, iam (simulate-principal-policy).
  Real-time metrics APIs may need session-policy-free credentials (Category H).
# Coverage: 
  17 patterns across 8 categories — flow logging, alarm coverage, approved origins, S3/KMS
  posture, Lex alias drift, AI guardrails, TDG/ACGR resilience, S3 lifecycle, cost
  investigation, metrics-blocking IAM, Contact Lens rule hygiene, and four call-quality
  patterns. NOT covered by a dedicated pattern — routed to Category Z and reported as gaps,
  never improvised: SAML/SSO login failures, agent-state and missed-contact issues, DTMF
  failures, Lambda integration errors, queue-routing misconfiguration, missing CTRs,
  chat/task channel issues.

# Amazon Connect Troubleshooting — Adaptive Runbook Dispatcher

A dispatcher plus a pattern contract. It decides **which** procedure runs, **whether** a
condition is a problem for *this* instance, and **what numbers** count as bad — then hands off
to a static, fully-specified procedure in a reference file.

**The governing line: applicability and thresholds are dynamic; procedures and evidence rules
are static.** Vague procedures are what produce invented APIs and invented quotas.

Not gated on an ops review (a customer with choppy audio now doesn't get a 7-pillar review
first). Not improvised — no pattern means a reported gap, not a synthesised command sequence.
Not a write tool until the two-gate sequence completes.

## Run sequence

| # | Phase | Reads | Emits | Refuses to |
|---|---|---|---|---|
| 0 | Load `global-rules.md` | — | shared rules in effect | proceed without it |
| 1 | Pick entry door | the request | D-FIND / D-SYMP / D-OPEN | force one door through another |
| 2 | **Layer -1** perishable evidence *(D-SYMP/D-OPEN)* | symptom | the capture ask, in the first reply | block on collection |
| 3 | **Layer 0a/b** profile | APIs + must-asks | classification, bands, thresholds source | default an unanswered must-ask |
| 4 | **Layer 0c** pre-flight | one probe per category | coverage manifest, *before* findings | render a denied probe as a pass |
| 5 | Select patterns | contract guards vs profile | applies / suppressed / blocked | drop a suppression silently |
| 6 | Resolve thresholds | `parameters` | derived numbers + their derivation | ship a static count |
| 7 | Set severity | `severity_base` + profile | `base → adjusted (reason)` | adjust up on intuition |
| 8 | Diagnose | tier T0/T1/T2 | evidence with citations | confuse absence with AccessDenied |
| 9 | Report | all of the above | 11-section output contract | leave a section silently empty |
| 10 | Fix *(only if asked)* | two gates + IaC check | applied changes | write outside the gates |
| 11 | Deferred verification | `verify_delay` | pending re-checks | report deferred work as verified |

---

## 1. Entry Doors

| Door | Trigger | Starts at |
|---|---|---|
| **D-FIND** | ops review produced finding X (`SEC-001`, `REL-011`, …) | profile (reuse) → pattern X at Diagnose |
| **D-SYMP** | customer reports a symptom | Layer -1 → profile (build) → Symptom Lookup |
| **D-OPEN** | "something's wrong with Connect" | Layer -1 → profile (build) → Z1 triage |

D-FIND may reuse the review's profile and evidence subject to E4 freshness — don't re-collect.
D-SYMP/D-OPEN must build the profile first: a symptom can't be judged without knowing normal.

Instance unreachable (`AccessDenied`/`ResourceNotFound` on `ListInstances`/`DescribeInstance`)
→ **that is the root cause domain.** Report and stop.

---

## 2. Layer -1 — Perishable Evidence (D-SYMP / D-OPEN)

Some evidence expires in minutes and no API recovers it. Ask in your **first reply**, before
the profile and pre-flight — those take long enough to lose it.

| Evidence | Lost when |
|---|---|
| CCP logs — **capture** | agent refreshes/closes the tab before downloading |
| CCP logs — once in the customer's S3 bucket | only by a lifecycle expiry rule (durable) |
| `chrome://webrtc-internals/` dump | the call ends — must be open *before* the call |
| DevTools console / HAR | session ends |
| Real-time metrics snapshot | the moment passes — there is no history API |

Durable and can wait: CTRs (24 mo), CloudWatch (15 mo), CloudTrail (90 d), flow logs.
**Never spend a perishable window collecting durable evidence.**

**The ask:** affected agent's CCP → gear icon → **Download logs**, *before* refreshing; if
reproducible, open `chrome://webrtc-internals/` in a second tab before the next test call and
download while the call is live; 3–5 contact IDs with UTC timestamps; **and the S3 bucket +
prefix where CCP logs are collected.**

**Prefer the S3 path** — retrieve directly rather than waiting on a file transfer; it scopes to
the incident window and works when the agent already closed the tab. The bucket is
**customer-owned, not Connect-managed** (no `InstanceStorageResourceType` covers client logs),
so it is a must-ask and can never be derived. Retrieval, key-layout discovery, parsing, and the
token/PII handling rules: `call-quality-playbook.md` §5.A.1.

Rules: ask once and specifically (name the gear icon). A refresh already happened → record
`CCP logs unavailable — session cleared before capture` and name the hypotheses that
forecloses. Don't block. **Don't ask on D-FIND** — a config finding has no live session, and
asking anyway trains the customer to ignore the request when it matters.

---

## 3. Layer 0 — Instance Profile

Every guard and derived threshold reads from this. Build once per instance, carry it through.

### 0a. Inferable from APIs

```bash
aws sts get-caller-identity
aws connect list-instances --region <r>
aws connect describe-instance --instance-id <id> --region <r>
aws connect list-instance-attributes --instance-id <id> --region <r>
aws connect list-integration-associations --instance-id <id> --region <r>
aws connect list-tags-for-resource --resource-arn <arn> --region <r>
aws connect list-traffic-distribution-groups --instance-id <id> --region <r>
aws connect list-queues --instance-id <id> --queue-types STANDARD --region <r>
aws connect list-users --instance-id <id> --region <r>
aws service-quotas get-service-quota --service-code connect --quota-code <code> --region <r>
```

| Field | Source | Consumed by |
|---|---|---|
| `classification` | tags, alias, integrations | nearly every guard |
| `channels` | queue + routing-profile media concurrency | A, D, F |
| `identity_type` | `describe-instance → IdentityManagementType` | ACGR, SAML |
| `genai_in_use` | `WISDOM_ASSISTANT` / `Q_IN_CONNECT` integration | E2 |
| `campaigns_in_use` | `CONNECT_CAMPAIGNS` integration | telephony, cost |
| `replica_topology` | `ReplicationConfiguration`, TDG list | F |
| `volume_band` | CloudWatch `CallsPerInterval` 14d → `low <500/d`, `mid`, `high >10k/d` | all derived thresholds |
| `agent_count` | `list-users`, enabled only | alarm sizing, TDG |
| `instance_age_days` | `describe-instance → CreatedTime` | abandoned detection |
| `flow_logs_enabled` | `describe-instance-attribute CONTACT_FLOW_LOGS` | A1 |
| `contact_lens_enabled` | `describe-instance-attribute CONTACT_LENS` | H2, cost |
| `iac_owned` | stack tags + `describe-stack-resources` | every Change Proposal |

**Classification is a heuristic, never authoritative.** State it and its basis in every
Change Proposal.

| Classification | Criteria |
|---|---|
| `production` | integrations present, OR prod/prd tags, OR Wisdom/Q-in-Connect |
| `dev_test` | tags/alias contain dev, test, staging, sandbox, poc |
| `abandoned` | age > 365 d, 0 integrations, no prod tags, 0 enabled users |
| `dr_replica` | TDG association, OR alias contains replica/dr/bak/secondary |
| `unconfirmed` | anything else — **treat as production** |

### 0b. Must be asked — not inferable

Ask as one short intake block. **Never substitute a default.**

| Question | Gates |
|---|---|
| Call quality or call failure issues right now? | **D0 — mandatory every run** |
| RTO/RPO for voice? Documented DR requirement? | `REL-001`, `REL-009..013` — no stated RTO means absence of a TDG is an *observation* |
| Compliance regime — PCI DSS / HIPAA / GDPR / none? | `SEC-006/007`, retention, redaction, data handling |
| Is recording/transcript retention fixed? How long? | `COST-004/005` — never propose an expiry without it |
| Agent topology — office LAN / remote / VDI / mixed? | D2, D4 |
| **CCP log S3 bucket and prefix?** | **D2, D4 — primary agent-side evidence path** |
| Answer-time SLA / target queue wait? | queue-depth, `OLDEST_CONTACT_AGE` |
| Business hours / coverage windows? | hours-of-operation logic, off-hours alarm noise |

Unanswerable (unattended run, no live customer) → mark each dependent pattern
`BLOCKED — requires <question>`. **A finding that depends on an unanswered requirement is not a
finding.**

### 0c. Capability Pre-Flight → Coverage Manifest

Without it, a permission gap renders as a clean bill of health. One representative read per
category; record allowed / denied / throttled:

| Cat | Probe | Cat | Probe |
|---|---|---|---|
| A1 | `logs:DescribeLogGroups` | E2 | `wisdom:ListAssistants` ⚠ separate namespace |
| B1 | `cloudwatch:DescribeAlarms` | F | `connect:ListTrafficDistributionGroups` |
| C1 | `connect:ListApprovedOrigins` | G1 | `s3api:GetBucketEncryption` |
| C2/C3 | `connect:DescribeInstanceStorageConfig`, `kms:DescribeKey` | G2 | `ce:GetCostAndUsage` ⚠ $0.01/call |
| D2/D4 | `s3:ListBucket` on the **CCP log bucket** | H1 | `connect:GetCurrentMetricData` |
| E1 | `connect:ListBots` | H2 | `connect:ListRules` |

Emit the manifest **before any findings** so the reader can scope the negatives:

| Category | Probe | Result | Consequence |
|---|---|---|---|
| E2 | `wisdom:ListAssistants` | `AccessDenied` | **NOT ASSESSED** — guardrail state unknown |
| D2/D4 | `s3:ListBucket` on CCP log bucket | `AccessDenied` | **NOT ASSESSED** — agent-side evidence unreachable; never read as "no CCP logs exist" |

**A denied probe renders `NOT ASSESSED — missing <permission>`.** Never a pass, never a
zero-finding result, never an empty section.

---

## 4. Evidence Rules (static — these never adapt)

**E1. Ambiguous negatives.** Roughly half of all findings are "X is absent", and absence is
what a permission failure looks like. Classify every negative against the table in
`global-rules.md` §2, and disambiguate `AccessDenied` with `iam simulate-principal-policy`
(§2.1) before reporting a permissions finding.

**E2. Diagnose depth scales with confidence.** Record the tier on every finding.

| Tier | When | Action |
|---|---|---|
| **T0** | pillar check returned a direct result naming the root cause | pillar evidence *is* the Diagnose result; cite API + resource + timestamp |
| **T1** | severity ≥ High, **or** rests on an absence, **or** rests on an inference, **or** T0 evidence stale | run the pattern's full Diagnose + Verify |
| **T2** | T1 inconclusive, or two patterns both fit | run both; report competing hypotheses with the discriminating evidence |

**E3. Pivot budget.** Two minutes or two failed hypotheses per finding, then escalate to T2 or
record `root cause not established — <what was ruled out>`. Don't settle for a weak answer
because the strong one was slow.

**E4. Evidence freshness.**

| Class | TTL | On expiry |
|---|---|---|
| Structural profile | 24 h | re-collect 0a |
| Metric-derived (`volume_band`, thresholds) | 1 h | re-derive |
| Must-ask answers | session, unless revised | carry forward |
| **Evidence backing a Change Proposal** | **15 min** | **re-diagnose and re-propose** |
| Coverage manifest | per run | re-probe |

Stale-evidence findings drop to T1, never reported as confirmed.

---

## 5. Pattern Contract

Every pattern conforms to this. **A pattern missing `applies_when` or `parameters` is
incomplete and must not be run against a real instance.**

```yaml
id: OPS-002
category: B
severity_base: MEDIUM

applies_when:                       # ALL must hold, evaluated against Layer 0
  - profile.classification in [production, unconfirmed, dr_replica]
  - profile.channels contains voice

suppress_when:                      # ANY true → not a finding; record + cite the clause
  - profile.classification == abandoned
  - existing alarms already cover the metric (namespace+metric+dimension match)

blocked_when: []                    # missing must-ask → BLOCKED, not a finding

depends_on: [H1]                    # resolved first; see Fix Ordering

parameters:                         # resolved live, never hardcoded
  missed_calls_threshold:
    derive: p95(CloudWatch AWS/Connect MissedCalls, 14d) * 1.5
    floor: 3
    fallback_if_no_data: BLOCKED — insufficient traffic history to size this alarm
  concurrent_calls_pct_threshold:
    static: 80                      # metric is already normalized against the quota
  evaluation_periods:
    derive: 1 if profile.volume_band == high else 3

diagnose: [ ... static command sequence ... ]
verify:   [ ... static; must assert a concrete observable ... ]
verify_delay: "period × evaluation_periods, +1 period margin"
verify_requires_traffic: true
fix:      [ ... static; runs ONLY after two-gate ... ]
rollback: [ ... static commands, not prose ... ]
effort:   "30 min"
risk:     "LOW — read-only metrics, no contact-handling behaviour change"
```

### Threshold derivation

The test: **static ratio, keep. Static count, derive.** `ConcurrentCallsPercentage 80` travels
everywhere because it is already a ratio of the resolved quota. `MissedCalls 5` is catastrophic
at 20 calls/day and noise at 50k. Apply this to every numeric literal in every pattern.

| Parameter | Resolution |
|---|---|
| `ConcurrentCallsPercentage` | static `80` — already normalized |
| `MissedCalls` count | `p95(14d) * 1.5`, floor 3 |
| `ContactFlowErrors` | `max(1, p95(14d))` — `1` valid only when the 14d baseline is 0 |
| Concurrent-call quota | `service-quotas get-service-quota` — never assumed |
| `OLDEST_CONTACT_AGE`, queue depth | `profile.sla_target` (must-ask) × arrival rate |
| S3 lifecycle expiry | `profile.retention_requirement` (must-ask) — **never** a default |
| Recording storage growth | growth rate vs `volume_band`, not absolute GB |
| Alarm `evaluation_periods` | `volume_band` |
| Jitter / loss / latency | static `<30 ms` / `<0.5 %` / `<150 ms` — codec properties |
| Lambda flow timeout | static 8 s — hard service limit |

### Severity

`severity_base` is the **ceiling**. Down one level for `dev_test`; suppress for `abandoned`;
`unconfirmed` gets production severity. Up one level **only** with a stated blast-radius reason
from the profile (`dr_replica` with a documented RTO; `genai_in_use` with an unguarded agent) —
never on intuition. Always show `base → adjusted (reason)`. Level definitions:
`global-rules.md` §8.

### Fix Ordering

Severity alone produces an unfollowable plan. Sort each severity band topologically by
`depends_on`, then apply **dependency promotion**: a dependency in a lower band moves up into
its dependent's band.

| Pattern | depends_on | Why |
|---|---|---|
| B1 (alarms) | H1 | can't verify an alarm whose metrics you can't read |
| any flow-error diagnosis | A1 + a test call | no logs, no evidence |
| C2 (S3 KMS enforcement) | C3 | the policy references a key that must exist |
| F1 (TDG) | replica instance exists | a TDG spans instances |
| F2–F6 (ACGR) | `identity_type == SAML` | unavailable on `CONNECT_MANAGED` |
| E1 (Lex prod alias) | production alias identified | else the flow points at nothing |
| G1 (lifecycle) | `retention_requirement` answered | expiry days otherwise invented |

### Multi-instance semantics

One profile per instance — never merged. N instances with the same condition = **N findings**,
each with its own severity, thresholds, and suppression decision; that divergence is the point.
Rollup is display-only, per-instance evidence stays individually cited. One instance returning
`AccessDenied` doesn't abort the run. **Never apply a fix across instances under one gate** —
classification and blast radius differ per instance.

---

## 6. Write Path

Read-only by default. Full sequence, Change Proposal format, hard stops, and the deferred-
verification table: **`global-rules.md` §5**. In summary:

**Gate 1** (customer asks for *that specific* fix — "fix everything" doesn't count) →
**step 0 IaC ownership check** (a CLI fix on stack-managed state is reverted at next deploy) →
**Change Proposal** (commands, current state, expected state, blast radius, rollback *as
commands*, effort/risk, verify timing) → **Gate 2** (confirmation of *that concrete proposal*,
per instance, per finding) → **re-diagnose** (proposal evidence expires in 15 min; abort
`ALREADY_RESOLVED` or `DRIFT`) → **execute → verify by observing state** → **document**.

Anything with a `verify_delay` reports `APPLIED — verification pending, re-check after <delay>`.
Never `verified`.

---

## 7. Routing

| Cat | IDs | Covers | Reference |
|---|---|---|---|
| **A** | A1 (`OPS-001`/`OPS-004`) | flow logging gaps, invisible flow errors | `troubleshooting-guide.md` |
| **B** | B1 (`OPS-002`) | alarm coverage, operational blindness | `troubleshooting-guide.md` |
| **C** | C1 (`SEC-001`), C2 (`SEC-007`), C3 (`SEC-006`), C4 (IAM) | origins, S3 policy/encryption, KMS CMK, IAM denials | `troubleshooting-guide.md`, `iam-permission-errors.md` |
| **D** | **D0 (mandatory)**, D1–D4 (`PERF-CQ-001..004`) | call quality intake, agent/WebRTC, telephony/carrier, CCP logs | `call-quality-playbook.md` |
| **E** | E1 (`PERF-002`), E2 (`AI-001`/`AI-007`) | Lex test alias in production, AI guardrails | `troubleshooting-guide.md` |
| **F** | F1 (`REL-001/002/008`), F2–F6 (`REL-009..013`) | TDG/DR; ACGR sync and recovery | F1: `troubleshooting-guide.md`; F2–F6: `acgr-sync-operations.md` |
| **G** | G1 (`COST-004`), G2 (`COST-003`) | S3 lifecycle, cost spike investigation | `troubleshooting-guide.md` |
| **H** | H1 (metrics blocker), H2 (`PERF-003`) | session policy blocking metrics, Contact Lens test rule | `troubleshooting-guide.md`, `iam-permission-errors.md` |
| **Z** | Z1 | no pattern matches — general triage | this file |

**Finding-ID drift:** pillar files use `OPS-001`/`AI-001`; an earlier `SKILL-troubleshoot.md`
draft used `OPS-004`/`AI-007` for the same findings. On D-FIND, match on the pillar file that
produced the finding.

### Category Z — an honest gap marker

Run the originating pillar check (or nearest read-only equivalent) as Diagnose. Record
verbatim: `no dedicated runbook pattern exists yet for this finding type`. Report the evidence
and stop. **Do not synthesize a fix** — an invented remediation for a production contact centre
is worse than an acknowledged gap.

### Symptom Lookup (D-SYMP)

**Capture first** is the Layer -1 ask — request it in your first reply, not after the profile.

| Symptom | Cat | Capture first |
|---|---|---|
| Choppy, one-way, dropped audio | D2 | **CCP logs + webrtc-internals + contact IDs** |
| CCP won't connect / WebRTC failure | D2→D4 | **CCP logs + console + Network tab** |
| Agent hears nothing / no audio device | D2 | **CCP logs + console** |
| Agents can't log in / SAML or SSO failure | **Z1** | **HAR + SAML response + verbatim error** |
| Agent stuck in a state / not receiving contacts | **Z1** | **CCP logs + metrics snapshot + contact IDs** |
| Calls not arriving at Connect | D3 | contact IDs, caller numbers, UTC times (durable) |
| Flow errors not visible in logs | A1 | — |
| No alarms / no operational visibility | B1 | — |
| Cannot embed CCP in a web app | C1 | console from the embedding page |
| `no identity-based policy allows` | C4 | verbatim error |
| `no session policy allows` / can't read metrics | H1 | verbatim error |
| Lex bot answering with test intents | E1 | — |
| AI agent responding without guardrails | E2 | — |
| Recording storage growing unbounded | G1 | — |
| Unexpected Connect cost increase | G2 | — |
| ACGR: replica out of sync / enable replication / sync inactive | F3 / F2 / F6 | — |
| Anything else | **Z1** | CCP logs if an agent is affected now |

**Two honest gaps:** agent login/SAML failure and agent-state/not-receiving-contacts are among
the most common symptoms a contact centre reports, and this kit has **no pattern for either**.
They route to Z1 — capture the perishable evidence, run read-only discovery, report what you
have, state the gap. Do not improvise a SAML debugging sequence; assertion mapping and IdP
config are exactly where invented steps do damage.

---

## 8. Anti-Hallucination Rules

1. Report only what an explicit tool call returned **in this session**. Never recall, infer, or
   estimate from training data.
2. Cite every finding: API called, resource queried, timestamp.
3. `Data unavailable — <reason>` for anything not retrieved. Never guess.
4. Never extrapolate one resource's result to similar resources unless each was checked.
5. No "typically", "usually", "by default", "should be" inside a finding. Verified Invariants
   (`global-rules.md` §7) are the sole exception, and only with their source.
6. Distinguish absence from inaccessibility on every negative finding — E1 is not optional.
7. **Never invent an AWS API.** Verify against the installed CLI, which is always available and
   authoritative for what will actually run — don't depend on a reference file resolving:

   ```bash
   aws connect help | grep -i '<operation-fragment>'   # does it exist?
   aws connect <operation> help                         # exact parameter names
   aws --version                                        # an older CLI may genuinely lack it
   find / -path '*botocore/data/connect/*/service-2.json' 2>/dev/null | head -1   # enums/shapes
   ```

   Not in the installed CLI → report a capability gap. Never guess an operation, parameter, or
   response field.
8. Never report call quality as confirmed-clear without an explicit D0 answer. Silence is not
   "no issues".
9. Never present a derived threshold as an AWS recommendation. State how it was derived.
10. Never claim a fix worked from a zero exit code. Verify observes state.
11. Unresolved `blocked_when` → `BLOCKED`, never assumed clear.
12. Denied pre-flight probe → `NOT ASSESSED`, never a pass.
13. Never report a deferred-verification fix as verified at application time.
14. Never diagnose an agent-side symptom from durable evidence alone without stating that the
    perishable evidence was requested and whether it arrived. If lost to a refresh, name the
    hypotheses that forecloses.

---

## 9. Output Contract

Any format the calling tool wants. Content is fixed:

1. **Version + entry door + scope** — version stamp, door, instances, regions, patterns run
2. **Coverage manifest** — Layer 0c; which categories are assessable, which `NOT ASSESSED` and
   why. **Before** findings, so negatives can be scoped
3. **Instance profile** — per instance, classification *and its basis*, must-asks answered vs not
4. **Findings** — ID, category, severity (`base → adjusted`, reason), cited evidence, **tier**,
   instance
5. **Suppressed** — conditions observed but not findings here, each citing the `suppress_when`
   clause that fired. *The visible proof the skill adapted — never omit*
6. **Blocked** — patterns not evaluated + the must-ask each needs
7. **Call quality (D0)** — the explicit answer, or an open question. Never a silent "no issues"
8. **Gaps** — Category Z entries + any check whose API was inaccessible
9. **Prioritized plan** — 🔴 Immediate / 🟠 This sprint / 🟡 Next sprint / 🟢 Backlog,
   topologically ordered within bands, each with threshold rationale, effort, risk
10. **Applied changes** — empty unless a two-gate sequence completed. State that explicitly
11. **Deferred verification** — anything applied whose verification is pending, with re-check
    action and timing

Consistency check before returning: every finding in §4 appears in §9 or has a stated reason;
every suppression cites its clause; every blocked item names its question; no `NOT ASSESSED` in
§2 is contradicted by a "no findings" claim in §4; every §10 change with a `verify_delay`
appears in §11. **A mismatch is a process error — resolve it, don't ship it.**

---

## 10. Delegated to `global-rules.md`

Not repeated here. Load once at step 0; these apply to every pattern and every run.

| Topic | § |
|---|---|
| Grounding, citation format, forbidden hedges, no-extrapolation | §1 |
| Ambiguous-negative table + `AccessDenied` disambiguation matrix | §2 |
| Data handling — sensitivity classes, PII masking, PCI/HIPAA constraints | §3 |
| Throttling quotas (per account+region), retry/backoff, run cost | §4 |
| Write path — two gates, Change Proposal format, hard stops, deferred verification | §5 |
| Rollback as commands | §6 |
| Verified Invariants + "Corrected — do not reintroduce" | §7 |
| Severity level definitions | §8 |
| Output discipline | §9 |
| AWS Support escalation bundle | §10 |

## 11. Reference Files

Load **only** what the selected categories need. §7 Routing is the table.

| File | Required for | If unavailable |
|---|---|---|
| `global-rules.md` | **every run** | **Stop** — no grounding or write rules |
| `troubleshooting-guide.md` | A, B, C, E, G, H | `NOT ASSESSED — procedure unavailable` |
| `call-quality-playbook.md` | D (incl. D0 gate, CCP log retrieval §5.A.1) | D0 still asked; diagnosis is a gap |
| `acgr-sync-operations.md` | F2–F6 | those findings become Z1 gaps |
| `iam-permission-errors.md` | C4, H1 disambiguation | E1 + inline `simulate-principal-policy`; state reduced confidence |
| `waf-pillar-checks.md` | post-fix confirmation | use the pattern's own `verify` |
| `connect-pillar-{1..7}-*.md` | D-FIND T0 evidence | rebuild at T1 instead of reusing |
| `worked-example.md` | validating a run, onboarding, authoring | — |
| API surface catalog | operation existence | **not required** — rule 7 uses the installed CLI |

**Resolution:** local `references/`, then the host agent space. If a needed reference resolves
in neither, **report the affected category as a gap and continue with what does resolve.** Never
improvise a procedure to cover a missing reference.

### Note for pattern authors

Port patterns from `SKILL-troubleshoot.md` unchanged **except**: add the Pattern Contract
headers, and replace each hardcoded numeric literal with `static:` (justified) or `derive:`.
Strip run-specific artifacts — the source contains a personal Salesforce origin, a hardcoded
`$5.00` budget, and fixed 2026-06 dates that must not ship as defaults.
