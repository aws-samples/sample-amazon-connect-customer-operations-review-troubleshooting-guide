---
name: "amazon-connect-ops-review-troubleshooting-guide"
description: "Amazon Connect Well-Architected Toolkit — a multi-module toolkit for Amazon Connect covering: (1) a full Well-Architected operations review across 7 pillars (Operational Excellence, Security, Reliability, Performance, Cost, Sustainability, GenAI); (2) troubleshooting with self-service remediation for 14 finding patterns including call quality investigation and ACGR sync verification; and (3) a Region Readiness module that tells customers — before they build — which AWS Region can deliver the Connect features, phone numbers, outbound campaign destinations, and Global Resiliency pairing they need. Platform-agnostic — usable by any AI tool with AWS CLI/SDK access, not just this agent. Loads reference files on demand to minimize hallucination risk."
metadata:
  version: "1.5.0"
  author: "aws-samples"
  aws-services: "Amazon Connect"
  technical-domains: "Contact Center, Telephony, GenAI"
---

# Amazon Connect Well-Architected Toolkit

> Formerly titled "Amazon Connect Operations Review & Troubleshooting Guide." The display name changed in 1.4.0; the skill identifier (`amazon-connect-ops-review-troubleshooting-guide`) and repository name are unchanged.

## START HERE — Module selection gate (mandatory, before anything else)

When this skill is invoked, your FIRST action is to present the module menu below and WAIT for the user's choice. Do this on every fresh invocation, even if the user's opening message already named or implied a mode — confirm the number before running anything. Do not discover instances, fetch pages, read other reference files, or produce findings until the user has chosen.

Present exactly this menu:

```
Which module would you like to run?

  1. Review           — Well-Architected operations review across all 7 pillars
                        (Operational Excellence, Security, Reliability, Performance,
                        Cost, Sustainability, GenAI). Needs read-only AWS access.

  2. Troubleshoot     — Diagnose a finding ID or a symptom, verify it, and propose a
                        fix (read-only by default). Needs read-only AWS access.

  3. Region Readiness — Which AWS Region supports the features, phone numbers, outbound
                        campaign destinations, and DR pairing you need — before you build.
                        No AWS account access required.

  4. Cost Optimization — Decompose the Connect bill and rank savings opportunities
                        (phone numbers, telephony mix, feature ROI, idle instances,
                        storage, anomalies) with estimated monthly $ impact.
                        Needs read-only AWS access incl. Cost Explorer.

  5. Peak Readiness   — Go / no-go gate before a peak event (Black Friday, campaign,
                        launch): quota headroom, IVR Lambda, resiliency, monitoring,
                        staffing/routing. Needs read-only AWS access.

Reply with 1, 2, 3, 4, or 5.
```

Selection rules:
- Run ONLY the module the user selects. Ignore the others entirely — do not load their reference files, run their checks, or mix in their findings.
- Map the reply: **1 → Review**, **2 → Troubleshoot**, **3 → Region Readiness**, **4 → Cost Optimization**, **5 → Peak Readiness**. Accept the number or the module name.
- If the reply is ambiguous or invalid, re-present the menu and ask again. Do not guess.
- If the user's opening message already contains a clear request for one module, still show the menu but you MAY note the implied choice (e.g. "Looks like you want option 2 — confirm with 2 to proceed."). Proceed only after they confirm.
- The one documented cross-module exception stays intact: a **Review (option 1)** still runs the Region Readiness cross-check on each discovered instance as part of its own flow. That is Review doing its job — it is not a reason to skip this gate or to run option 3 separately.
- Once a module is chosen and running, stay in it. If the user later wants a different module, return to this menu.

After the user chooses, jump to that module's starting point:
- **1 — Review** → Investigation Workflow, Step 1 (below)
- **2 — Troubleshoot** → Runbook Category Index (below)
- **3 — Region Readiness** → `references/region-readiness.md`
- **4 — Cost Optimization** → `references/cost-optimization.md`
- **5 — Peak Readiness** → `references/peak-readiness.md`

### Example prompts (share with users as starting points)

**1 — Review**
- "Run a full Well-Architected operations review on my Connect instance `my-instance` in us-east-1 (read-only)."
- "Review just the Security and Reliability pillars for all Connect instances in eu-west-2."
- "Discover the Connect instances in my account and do a health check on the production one."

**2 — Troubleshoot**
- "Agents report choppy, one-way audio on ~20% of calls since this morning — help me diagnose."
- "How do I fix finding SEC-001 (HTTP approved origin) on my instance?"
- "Check whether my ACGR primary and replica are in sync and what to look for in CloudTrail."

**3 — Region Readiness**
- "Can I run outbound campaigns to Canada from an instance in Australia?"
- "I need Norway phone numbers used as custom caller ID — which Region should I build in?"
- "We need Contact Lens, outbound campaigns to the UK, and cross-Region DR — which single Region fits?"

**4 — Cost Optimization**
- "Why is our Amazon Connect bill up 30% this quarter, and where can we cut?"
- "Find unused phone numbers on `my-instance` and size the savings."
- "Is Contact Lens worth its cost on our plan?"

**5 — Peak Readiness**
- "Are we ready for Black Friday at 2x our normal peak on `my-instance` in us-east-1?"
- "Do we need any quota increases before our product launch on 15 December?"
- "Give me a go/no-go for a marketing campaign that will triple chat volume."

---

## Modes

| Mode | Use it for | Needs AWS access? | Start at |
|---|---|---|---|
| **Review** | Well-Architected operations review across 7 pillars | Yes (read-only) | Investigation Workflow, Step 1 |
| **Troubleshoot** | A finding ID or a symptom → diagnose, verify, propose fix | Yes (read-only by default) | Runbook Category Index |
| **Region Readiness** | Which Region supports the features, numbers, campaign destinations, and DR pairing a customer needs — before they build | **No** (fetches live AWS pages when web access is available, bundled snapshot otherwise) | `references/region-readiness.md` |
| **Cost Optimization** | Ranked, dollar-sized savings opportunities and spend-anomaly driver analysis (`CSO-xxx`) | Yes (read-only, incl. Cost Explorer — ~$0.01 per request) | `references/cost-optimization.md` |
| **Peak Readiness** | Go / no-go verdict before a peak event, with a lead-time-ordered action plan (`PEAK-xxx`) | Yes (read-only) | `references/peak-readiness.md` |

The module is chosen via the selection gate above. A single engagement runs one module at a time; the only cross-module behavior is that a Review (option 1) includes the Region Readiness cross-check on each discovered instance.

## When to Use

Pick the module via the selection gate above; the Example prompts show typical triggers for each. In short: **Review** for an operations/health/Well-Architected assessment (one pillar, several, or all 7, with instance discovery); **Troubleshoot** for a symptom, a finding ID to fix, a fix/rollback/verification, call-quality issues, or ACGR sync checks; **Region Readiness** for which Region supports a feature / number / campaign destination / DR pairing, or any Region-shaped failure, before building; **Cost Optimization** to cut or explain the Connect bill (Pillar 5 of a Review flags cost issues; this module sizes and ranks them); **Peak Readiness** for a pre-event capacity go / no-go.

**Note on scope:** By default, all of the above is read-only diagnosis and reporting. See `references/global-rules.md` ("Read-Only by Default" and "Two-Gate Confirmation Sequence for Any Write") — no fix is applied unless the customer explicitly asks for that specific fix AND then confirms the agent's concrete change proposal.

**Note on call quality:** Every operations review or troubleshooting pass MUST explicitly ask the customer whether they're experiencing call quality issues — see `references/call_quality_playbook.md` ("Call Quality Intake Checklist", D0). Do not infer this from pillar findings or silence. A standalone Region Readiness run for a contact center that isn't live yet has no calls to ask about, so D0 doesn't apply there; nor does it apply to a standalone Cost Optimization or Peak Readiness run, whose scope is spend or capacity (Peak Readiness still records agent-site network reachability as PEAK-021). It does apply as soon as the run touches an existing instance.

**Note on runbook cross-referencing:** An operations review does NOT end at producing pillar findings. Every finding surfaced by Step 3's pillar assessments — not just ones the customer explicitly names — MUST be routed through its matching Runbook Category for Diagnose/Verify treatment before the Step 4 report is produced. See Step 3 below.

---

## Investigation Workflow

### Step 1 — Scoping Inputs

Before running any assessment, resolve these inputs. If a caller (human or orchestrating tool) hasn't provided them, ask for them or resolve automatically where noted — either is fine, this is not a mandatory blocking gate:

| Input | How to resolve |
|---|---|
| AWS account(s) | Provided explicitly, or resolve current account via `aws sts get-caller-identity` |
| Region(s) | Provided explicitly, or scan common regions (see Step 2) |
| Instance(s) | Provided explicitly, or discover via Step 2 and present the list for selection |
| Pillar(s) to assess | One, several, or "all 7" — default to all 7 if unspecified for a full review |

**Safety check before any remediation (applies throughout — see `references/global-rules.md` for full detail):**
1. Confirm the target instance's classification (production vs dev/test) — this is agent-inferred from tags/integrations in Step 2 below, NOT authoritative; state it and its basis as part of the Change Proposal
2. Any write follows the Two-Gate Confirmation Sequence: Gate 1 (general intent) → agent presents a Change Proposal (what/how/before/after/rollback) → Gate 2 (explicit confirmation of that specific proposal) → only then execute
3. For production instances: always provide rollback steps
4. Never delete resources without explicit confirmation of that specific deletion
5. Never modify ACTIVE contact flows without a backup (describe-before-modify)

See `references/scoping-gate.md` for the full scoping inputs checklist, and `references/global-rules.md` for the full Two-Gate Confirmation Sequence and Change Proposal requirements.

### Step 2 — Discovery & Classification

```bash
# Resolve current account/identity if not provided
aws sts get-caller-identity

# Per region, list and describe instances
aws connect list-instances --region <region>
aws connect describe-instance --instance-id <instance-id> --region <region>
aws connect describe-instance-attribute --instance-id <instance-id> --attribute-type CONTACTFLOW_LOGS --region <region>
aws connect list-integration-associations --instance-id <instance-id> --region <region>
aws connect list-tags-for-resource --resource-arn <instance-arn> --region <region>
```

Classify each discovered instance using the classification criteria in `references/connect-ops-review-orchestrator.md` — that file is the **canonical source** for discovery, classification, and pillar routing; do not restate its criteria table here (keeping a single copy avoids drift).

**Classification is a heuristic signal based only on tags, alias, and integrations found — not an authoritative production/dev-test determination.** An instance with no tags or an ambiguous alias MUST be treated as unconfirmed/production-risk, not automatically "safe".

Collect shared data once (flows, queues, users, routing profiles, phone numbers) — see `references/connect-ops-review-orchestrator.md` for the full discovery and shared-data-collection procedure and pillar-routing rules.

Full instance details, including disconnect reason, come from:
```bash
aws connect describe-contact --instance-id <instance-id> --contact-id <contact-id> --region <region>
aws connect get-current-metric-data --instance-id <instance-id> \
  --filters '{"Queues":["<queue-arn>"]}' \
  --current-metrics '[{"Name":"AGENTS_AVAILABLE","Unit":"COUNT"},{"Name":"AGENTS_ON_CALL","Unit":"COUNT"},{"Name":"CONTACTS_IN_QUEUE","Unit":"COUNT"}]' \
  --region <region>
aws logs filter-log-events --log-group-name /aws/connect/<instance-id> --filter-pattern "ERROR" --region <region>
```

If the instance itself is unreachable (`AccessDeniedException` on `ListInstances`/`DescribeInstance`), that IS the root cause domain — stop and report it rather than chasing downstream symptoms.

### Step 3 — Pillar Assessments + Cross-Reference EVERY Finding to a Runbook

**Deep-dive is mandatory. A List/summary-only pass is an INCOMPLETE pillar, not a done one.** For every in-scope check:
- Run the full call sequence: `List*` → the per-item `Describe*`/`Get*` tier (honor the pillar's own sampling caps, e.g. "up to 20 flows" — sampling within a check is fine; skipping the Describe/Get tier is not).
- Never report a List-level status as a finding without its Describe/Get confirmation (e.g. a guardrail "ACTIVE" in a list may have no published version — verify).
- A check is "done" only when its Describe/Get calls ran OR are recorded as `[Not checked — reason]`. No silent downgrade to List-only.
- The per-pillar second-budgets are effort hints, NOT licence to skip the Describe/Get tier. If a run is cut short, mark checks `[Not checked — reason]`; do not pass them off as clean.

Before executing any API calls, determine the requested pillar scope:

- If the customer names specific pillar(s), execute ONLY the API calls filed under those pillar(s)' sections in `references/api-surface.md`, using each named pillar's `connect-pillar-N-*.md` for the authoritative Check sequence. Do NOT execute calls filed exclusively under out-of-scope pillars.
- If the customer requests ALL pillars or a general/full review, execute the full catalog across all 7 pillar sections.
- An API filed under multiple pillars (e.g. ListLambdaFunctions) is executed once per in-scope pillar that references it — each applies its own Describe/Get follow-up and interpretive lens.

`references/api-surface.md` gives catalog context per pillar; the pillar file's own numbered Checks are authoritative on any conflict.


For a full or partial **operations review**, load and execute only the selected pillar files:

| Pillar | Reference File |
|---|---|
| 1 — Operational Excellence | `references/connect-pillar-1-ops-excellence.md` |
| 2 — Security | `references/connect-pillar-2-security.md` |
| 3 — Reliability | `references/connect-pillar-3-reliability.md` |
| 4 — Performance Efficiency | `references/connect-pillar-4-performance.md` |
| 5 — Cost Optimization | `references/connect-pillar-5-cost.md` |
| 6 — Sustainability | `references/connect-pillar-6-sustainability.md` |
| 7 — Generative AI | `references/connect-pillar-7-genai.md` |

**Cross-check pillar coverage against `references/waf-pillar-checks.md`** before treating a pillar pass as complete — it holds the full Well-Architected checklist per pillar. If a pillar file's checks don't cover an item listed there for the pillars in scope, note the gap explicitly in that pillar's findings rather than silently skipping it.

**Mandatory follow-on step — do not treat as optional or as a separate path from the review:** once pillar assessments produce findings, loop through **every single finding, regardless of severity**, and:
1. Map it to its Runbook Category (A–H, R) using the Runbook Category Index below or the finding's pillar-file "Fix" reference
2. Load the matching reference file and run that finding's Diagnose step (re-confirm/deepen the finding with the specific runbook procedure — not just the pillar check that first surfaced it)
3. Run the Verify step to confirm the diagnosis is reproducible
4. Do NOT run the Fix step — this cross-reference pass is diagnostic only
5. If a finding truly has no matching category (rare — most map to A–H or R), route it to Category Z and note that explicitly rather than dropping it silently

**This applies to a customer-named symptom or finding ID exactly the same way** — the only difference is a customer request starts directly at this step for one finding, while a full review arrives here for all findings produced by Step 3's pillar assessments.

**Regardless of what triggered this run, also execute the Call Quality Intake Gate (D0) in `references/call_quality_playbook.md`** — this is a mandatory explicit ask on every pass, not something to infer from pillar results.

**If a Diagnose/Verify step or a pillar check calls for an AWS API not already listed in the Tool Quick Reference below, consult `references/api-surface.md`** — the complete API catalog — before concluding the API isn't available; do not assume a capability doesn't exist just because it's absent from the shortlist.

Read `references/global-rules.md` before concluding on any finding — it defines the anti-hallucination grounding rules, the read-only-by-default rule, the Two-Gate Confirmation Sequence and Change Proposal format, safety checklist, verification pattern, and timeout/retry policy shared across every pillar and runbook.

### Step 4 — Report

**Gate:** before writing the report, satisfy the Report Generation Gate in `references/global-rules.md` — every in-scope check's Describe/Get tier ran, or is marked `[Not checked — reason]`. Do not generate the report with any check silently left at List-only.

Produce a report with these sections. This is a content template only — deliver it in whatever output format fits the calling tool (chat message, file, ticket comment, etc.); nothing here requires a specific artifact or storage system.

1. **Executive Summary** — instances assessed, total findings by severity, top 3 priorities
2. **Scoping Summary** — account(s), instances, pillars run
3. **Discovery Table** — instances, region, status, identity type, created date
4. **Findings** — per-instance, per-pillar findings with severity, impact, source citation
5. **Troubleshooting Guide** — for EVERY finding from Step 4 above: its runbook category, the Diagnose result, the Verify result, and the Fix reference marked "not applied." A finding present in section 4 but absent from this section is a process error — go back to Step 3.
6. **Call Quality Section** — result of the mandatory D0 ask: either the customer's explicit answer (and D0.1–D0.5 detail if YES), or, if this run had no way to ask a live customer, an explicit open question flagging that call quality status was not confirmed — never a silent "No issues" absent an actual answer
7. **Prioritized Remediation Plan** — Immediate / This Sprint / Next Sprint / Backlog

All fixes listed in the report are proposals only — none are applied by generating this report. Applying any of them requires the full Two-Gate Confirmation Sequence in `references/global-rules.md`.

---

## Runbook Category Index

Runbooks are organized by failure domain. Use the appropriate category based on the symptom or finding ID.

| Category | IDs | Covers | Reference File |
|---|---|---|---|
| A — Contact Flow & Logging | A1 (OPS-001) | Contact flow logging gaps, invisible flow errors | `references/troubleshooting-guide.md` |
| B — Monitoring & Alarms | B1 (OPS-002) | Missing CloudWatch alarms, operational blindness | `references/troubleshooting-guide.md` |
| C — Security & Access | C1 (SEC-001), C2 (SEC-007), C3 (SEC-006), C4 (IAM) | HTTP approved origins, S3 encryption, KMS key upgrade, IAM permission errors | `references/troubleshooting-guide.md`, `references/iam-permission-errors.md` |
| D — Telephony & Call Quality | D0 (mandatory intake), D1–D4 (PERF-CQ-001–004) | Call quality intake (always run), agent-side/WebRTC, telephony-side/carrier, CCP log analysis | `references/call_quality_playbook.md` |
| E — Integrations | E1 (PERF-002), E2 (AI-001) | Lex bot test alias in production, AI guardrail verification | `references/troubleshooting-guide.md` |
| F — Reliability & DR | F1 (REL-001), F2–F6 (REL-009–013) | Traffic Distribution Group / DR, ACGR sync configuration and failure recovery | `references/acgr-sync-operations.md` |
| G — Cost | G1 (COST-004), G2 (COST-003) | S3 lifecycle policy, cost spike investigation | `references/troubleshooting-guide.md` |
| H — Metrics & Session Policy | H1 (Metrics Blocker), H2 (PERF-003) | Session policy / elevated role blocking real-time metrics, Contact Lens test rule in production | `references/troubleshooting-guide.md`, `references/iam-permission-errors.md` |
| R — Region Readiness | R1 (REG-001–013) | Feature, telephony, campaign-destination, Global Resiliency, and latency fit of a Region | `references/region-readiness.md` |
| Z — Catch-All | Z1 | Symptom or finding not mapped to any category above — do NOT silently drop it, diagnose it under Z1 and note the gap | This file |

**Note:** Findings from pillars 1–7 that don't yet have a dedicated pattern in `troubleshooting-guide.md`, `call_quality_playbook.md`, `acgr-sync-operations.md`, or `iam-permission-errors.md` (e.g., a Sustainability or Cost finding without an existing numbered pattern) still route to Category Z: re-run the pillar's own Diagnose-equivalent check as the runbook Diagnose step, and note "no dedicated runbook pattern exists yet for this finding type" rather than omitting it from the Troubleshooting Guide report section.

### Symptom-Based Lookup

| Symptom | Category |
|---|---|
| Contact flow errors not visible in logs | A1 |
| No CloudWatch alarms, no operational visibility | B1 |
| Cannot embed CCP in web app | C1 |
| IAM "no identity-based policy allows" / "no session policy allows" errors | C4 |
| Recording storage costs growing unbounded | G1 |
| Lex bot responding with test intents in production | E1 |
| AI agent responding without safety guardrails | E2 |
| Cannot access real-time metrics | H1 |
| Unexpected high Connect costs this month | G2 |
| Choppy / one-way audio | D2 |
| Calls not arriving at Connect | D3 |
| CCP not connecting / WebRTC failures | D2/D4 |
| ACGR: changes not synced to replica | F3 (REL-011) |
| ACGR: need to enable replication | F2 (REL-009) |
| ACGR: sync service not active | F6 (REL-013) |
| Feature missing from the console / API in this Region | R1 |
| Can't claim a phone number for a country | R1 |
| Outbound campaign calls fail to a country | R1 |
| Outbound calls to a country blocked | R1 (REG-006) |
| Can't create an ACGR replica in the chosen Region | R1 (REG-008) |
| "Which Region should we use?" | R1 |
| Rank savings / find unused numbers / is a feature worth it | Cost Optimization module (`references/cost-optimization.md`) |
| "Are we ready for the peak / can we handle 2x?" | Peak Readiness module (`references/peak-readiness.md`) |

---

## Tool Quick Reference

| Tool / API | When to use |
|---|---|
| `connect:describe-instance` | Instance config, status, features, ReplicationConfiguration |
| `connect:list-instance-attributes` / `describe-instance-attribute` | Enabled features (contact flow logs, Contact Lens, etc.) |
| `connect:describe-contact` | Specific contact details, disconnect reason |
| `connect:describe-contact-flow` | Contact flow definition and metadata |
| `connect:describe-queue` | Queue config, outbound caller ID, hours |
| `connect:describe-routing-profile` | Agent routing config, queue priorities |
| `connect:describe-hours-of-operation` | Business hours configuration |
| `connect:describe-phone-number` | Phone number status, target flow |
| `connect:get-current-metric-data` | Real-time queue and agent metrics (requires elevated permissions in some setups) |
| `connect:get-metric-data-v2` | Historical metrics and analytics |
| `connect:list-lambda-functions` | Lambda integrations |
| `connect:list-lex-bots` | Lex bot integrations |
| `connect:list-approved-origins` | CCP embedding origins (SEC-001) |
| `connect:list-traffic-distribution-groups` / `get-traffic-distribution` | DR / multi-region setup |
| `wisdom:list-assistants` / `list-knowledge-bases` / `list-ai-agents` / `list-ai-guardrails` | AI/GenAI assessment — separate IAM namespace from `connect:*` |
| `cloudwatch:describe-alarms` / `get-metric-data` | Alarm coverage, metric trends |
| `logs:filter-log-events` / `describe-log-groups` | Contact flow log errors |
| `cloudtrail:lookup-events` | ACGR sync detection, audit trail, API-level change history — read-only, available under standard agent controls, no separate elevated grant needed |
| `iam:simulate-principal-policy` | Diagnosing session-policy vs identity-policy permission errors |

This table is a curated shortlist of the most commonly needed calls, not the complete set. **If a check needs an AWS API not listed here, consult `references/api-surface.md` for the complete API catalog before assuming the capability doesn't exist.**

All of the above are read-only calls. Mutating calls (`update-*`, `create-*`, `delete-*`, `associate-*`, `disassociate-*`, `put-*`) appear only inside a runbook's "Fix" step and only run after the full Two-Gate Confirmation Sequence (`references/global-rules.md`).

---

## Gotchas: Amazon Connect

- Contact flow logging must be explicitly ENABLED at both the instance level AND on each contact flow. Instance-level enablement alone is not enough.
- Contact flow complexity is bounded by a block limit, not a fixed byte size: a flow must have fewer than 200 blocks and a total size under 1 MB to import/export (the flow designer's block counter warns as you approach 200). There is no documented 32 KB flow-definition limit.
- Lambda functions invoked from a contact flow have a configurable timeout up to a maximum of 8 seconds in Synchronous execution mode and up to 60 seconds in Asynchronous mode. If the Lambda's own timeout is shorter, that applies first.
- DTMF input is only captured during "Get customer input" blocks. "Play prompt" blocks do NOT capture DTMF.
- Agents must be in "Available" status to receive contacts. Custom "Routable" statuses do NOT route contacts unless explicitly configured.
- CCP (Contact Control Panel) requires WebRTC — outbound UDP port 3478 (SEND/RECEIVE) for media/TURN, plus TCP 443 for signalling/HTTPS, with `*.connect.aws`/`*.transport.connect.aws` domains allow-listed. Media flows over UDP 3478; there is no documented TCP 443 media/TURN fallback. Corporate firewalls, VPN split-tunneling, and SSL inspection commonly break CCP connectivity.
- Phone numbers are region-specific — a number claimed in one region cannot be used by an instance in another region.
- Region availability differs per feature, per phone-number country/type, and per outbound campaign destination. Never answer "is X available in Region Y" from memory — the Region Readiness mode (`references/region-readiness.md`) fetches the decisive live AWS page by default (falling back to the bundled snapshot when web access is unavailable) and cites the source and date it used.
- Outbound campaign destinations are fixed by the instance's home Region (e.g. no campaign calls from Europe (London) to US numbers), and Global Resiliency replicas exist only for three Region pairings (`us-east-1`↔`us-west-2`, `eu-central-1`↔`eu-west-2`, `ap-northeast-1`→`ap-northeast-3`).
- Contact records (formerly "contact trace records"/CTRs) are delivered at least once and may be delivered again when new information arrives (e.g. after update-contact-attributes); there is no documented fixed 24-hour delivery window. Each record is available for 24 months from contact initiation. Use Kinesis streaming for near-real-time delivery.
- `wisdom:*` (Q in Connect, AI Agents, AI Guardrails, AI Prompts) is a completely separate IAM namespace from `connect:*`. The `connect:*` wildcard grants zero `wisdom:` access.
- ACGR (Amazon Connect Global Resiliency) requires SAML identity management — it cannot be enabled on `CONNECT_MANAGED` instances.
- ACGR sync events in CloudTrail are identified by `userIdentity.invokedBy` or `sourceIPAddress` equal to `synchronization.connect.amazonaws.com` — NOT by event name, since the sync service can perform any mutation. Do not filter by the SLR's `sessionIssuer.userName`, which contains an account-specific suffix.
- `ResourceConflictException` (HTTP 409) on ACGR sync events is benign — concurrent update noise, not a failure signal.
- CCP logs are session-scoped — refreshing or closing the browser clears them. Capture immediately after an issue occurs.

## Anti-Hallucination Rules

- Only report what was retrieved via an explicit tool/API call made during this session — never recall, infer, or estimate from training data.
- Cite the source for every finding: the API call, the resource queried, and the timestamp.
- Use `Data unavailable — [reason]` for anything that couldn't be retrieved — never guess.
- Never extrapolate a finding confirmed on one resource to all similar resources unless each was individually checked.
- Never use phrases like "typically", "usually", "by default" in a finding — these signal training-data inference, not live verification.
- Lambda timeout from a contact flow is configurable up to 8 seconds (Synchronous) or 60 seconds (Asynchronous) — do not claim a single fixed 8-second limit or that it cannot be changed.
- Contact flow logs require enablement at BOTH instance and flow level — never claim instance-level alone is sufficient.
- DTMF is only captured in "Get customer input" blocks — never claim other blocks capture DTMF.
- Contact records are delivered at least once (and may be re-delivered) and retained for 24 months — do not claim a fixed 24-hour delivery window; recommend Kinesis streaming for near-real-time needs.
- Never report call quality status as confirmed without an explicit customer answer to the D0 ask — an absence of a reported symptom is not the same as a confirmed "no issues."
- Never produce a Findings section (Step 4.4) without a corresponding Troubleshooting Guide entry (Step 4.5) for every finding — an ops review is not complete until every finding has been cross-referenced to a runbook and diagnosed/verified.
- Spend no more than a couple of minutes on any single hypothesis before pivoting if inconclusive.

---

## Reference Files

- `references/global-rules.md` — Grounding rules, read-only-by-default rule, Two-Gate Confirmation Sequence + Change Proposal format, safety checklist, verification pattern, timeout/retry policy (shared across all pillars and runbooks)
- `references/scoping-gate.md` — Scoping inputs checklist (accounts, instances, pillars)
- `references/connect-ops-review-orchestrator.md` — Discovery, classification, and shared data collection
- `references/connect-pillar-1-ops-excellence.md` — Pillar 1 checks (Operational Excellence)
- `references/connect-pillar-2-security.md` — Pillar 2 checks (Security)
- `references/connect-pillar-3-reliability.md` — Pillar 3 checks (Reliability) + Check 3.7 ACGR
- `references/connect-pillar-4-performance.md` — Pillar 4 checks (Performance Efficiency)
- `references/connect-pillar-5-cost.md` — Pillar 5 checks (Cost Optimization)
- `references/connect-pillar-6-sustainability.md` — Pillar 6 checks (Sustainability)
- `references/connect-pillar-7-genai.md` — Pillar 7 checks (Generative AI)
- `references/troubleshooting-guide.md` — Runbook categories A, B, C, E, G, H: index, symptom lookup, remediation plan template, detailed procedures
- `references/call_quality_playbook.md` — Category D: mandatory call quality intake gate (D0) + PERF-CQ-001–004 procedures
- `references/acgr-sync-operations.md` — Category F: ACGR sync architecture, detection, remediation (REL-009–013), failover test campaign
- `references/iam-permission-errors.md` — Category C4/H1: IAM error disambiguation
- `references/waf-pillar-checks.md` — Well-Architected Framework pillar checklist. Consulted in Step 3 to verify pillar-check coverage before a pillar pass is treated as complete.
- `references/api-surface.md` — Complete API catalog. Consulted in Step 3 and the Tool Quick Reference as the fallback when a needed AWS API isn't in the curated shortlist.
- `references/region-readiness.md` — Region Readiness mode: requirements intake, evaluation, interpretation, report template, existing-instance hook, manual rules, REG-001–013 catalog
- `references/region-readiness-matrix.md` — Generated, human-readable Region matrix (features, campaign destinations, default outbound countries, per-country telephony). Use when code execution isn't available.
- `references/cost-optimization.md` — Cost Optimization mode: spend baseline, lever evaluation, quantify-and-rank, report template, CSO-001–019 catalog
- `references/peak-readiness.md` — Peak Readiness mode: event intake, capacity/quota, dependency, preparedness checks, verdict rules, report template (incl. machine-readable JSON), PEAK-xxx catalog
- `references/region-data/connect-region-data.json` — Dated **fallback** snapshot of the AWS sources, used when a live fetch isn't possible. Region Readiness fetches live pages first by default (Step R0).
- `scripts/region_readiness.py` — Deterministic Region Readiness evaluator over the fallback snapshot (stdlib Python, no AWS access). `scripts/build_region_data.py` is a maintainer tool that refreshes the snapshot — automate it on a schedule (monthly cron/CI) so the fallback never goes stale; customers never run it.
