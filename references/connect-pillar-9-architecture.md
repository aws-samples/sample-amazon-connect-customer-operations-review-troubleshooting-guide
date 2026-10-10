# Amazon Connect Operations Review — Pillar 9: Architectural Patterns

## Description

Assesses the structure of the contact centre rather than its configuration
flags: flow composition and complexity, error-path coverage, external
dependency topology, reuse and modularity, data storage architecture, routing
topology, and entry-point reachability.

This pillar is possible because `connect:DescribeContactFlow` returns the flow
definition as JSON in its `Content` field. That makes block-level analysis a
read-only operation, so most pattern detection here needs no human input and no
AWS intervention.

## When to Use

- Runs for any instance with contact flows
- User asks about architecture, design patterns, technical debt, flow sprawl,
  maintainability, or "is this set up sensibly"
- Before a migration, a redesign, or handing an instance to a new team

## Execution Strategy

```
Budget: 120 seconds
APIs: ~35 calls (dominated by sampled DescribeContactFlow)
Depends on: Phase 0 output (flow list, queue list, routing profile list)

Parallelization plan:
  Sequential:  9.1 → 9.2 → 9.3 → 9.4   (all consume the same sampled flow JSON)
  Parallel:    9.5 + 9.6 + 9.7 + 9.8
  Estimated wall time: ~85 seconds on fast path
```

**Fetch the flow JSON exactly once.** Checks 9.1 through 9.4 and 9.5 all read
the same `Content` payloads. Re-describing a flow per check multiplies the call
count by five for no additional information.

## Pre-Flight (5 seconds)

```
Test 1: connect:DescribeContactFlow on the first flow from Phase 0
  - SUCCESS and Content present → run 9.1–9.5 in full
  - SUCCESS but Content absent → structural analysis unavailable; run
    metadata-only variants and say so
  - AccessDeniedException → skip 9.1–9.5, note in output, run 9.6–9.9

Test 2: connect:ListInstanceStorageConfigs with --resource-type CALL_RECORDINGS
  - SUCCESS → run 9.6
  - AccessDeniedException → skip 9.6
  - NOTE: --resource-type is REQUIRED on this call. Omitting it returns a
    ParamValidation error, which is a malformed request, not a denial.
```

## Sampling Rule

Describing every flow on a large instance will exhaust the budget. Describe UP
TO 25 flows, prioritised:

1. `Type=CONTACT_FLOW` with `State=ACTIVE` — the customer-facing IVR paths
2. Flows referenced by a claimed phone number (from Check 9.8)
3. Flows whose name matches `copy|test|old|tmp|bak|v2|new` — likely debt
4. Largest flows by `Content` length, if a prior pass recorded it
5. Remaining `CONTACT_FLOW` types, most recently modified first

⚠️ **Then stratify: add at least two flows of every other `Type` present**
(`CAMPAIGN`, `CUSTOMER_QUEUE`, `QUEUE_TRANSFER`, `AGENT_HOLD`, `AGENT_WHISPER`,
`CUSTOMER_HOLD`, `CUSTOMER_WHISPER`, `OUTBOUND_WHISPER`, `AGENT_TRANSFER`), or
all of them if fewer than two exist. Priorities 1–5 above select almost
exclusively `CONTACT_FLOW`, and the non-`CONTACT_FLOW` types behave very
differently — on a measured instance every one of 26 `CONTACT_FLOW` flows had
an error branch while 23 of 23 `CAMPAIGN` flows had none. A sample drawn only
from priorities 1–5 therefore cannot see that difference at all and will report
a clean bill of health for the whole instance. **Record the sample composition
broken down by `Type`,** not just the total.

Record the sample size and the population size in the output. Every percentage
in this pillar is a percentage **of the sample**, and must be labelled as such.
Do not extrapolate a sampled rate to the full population as though measured —
the grounding rules forbid it.

⚠️ **Retry failed describes.** `DescribeContactFlow` issued concurrently can
return transient throttling errors. A measured run lost 6 of 59 flows that way
and the loss was silent — it simply shrank the denominator. Retry with backoff
and **report the describe success count alongside the sample size**; if any
flow could not be described after retries, say which, rather than quietly
reducing the sample.

## Checks

### Check 9.1 — Flow Structural Composition (25 seconds max)

**API calls**:
```
connect:ListContactFlows        (MaxResults up to 1000; paginate)
connect:DescribeContactFlow     (per sampled flow)
  EXTRACT: ContactFlow.Content          → JSON string, parse it
             .Actions[]                 → the blocks
               .Identifier
               .Type                    → block type
               .Parameters              → block configuration
               .Transitions             → NextAction, Errors, Conditions
             .StartAction
           ContactFlow.Type             → CONTACT_FLOW | CAMPAIGN | AGENT_HOLD | ...
           ContactFlow.Status           → PUBLISHED | SAVED
           ContactFlow.State            → ACTIVE | ARCHIVED
```

**Checks**:
- [ ] Block count per flow — `len(Actions)`
- [ ] Flows at or near the 200-block limit
- [ ] Block-type distribution across the sample
- [ ] Flows of 1–2 blocks (stubs that may be dead weight)
- [ ] Flow type mix — a high `CAMPAIGN` share indicates an outbound-led estate

**Findings**:
- Any flow ≥180 blocks = ARCH-001 🟠 High — approaching the 200-block ceiling,
  which blocks further edits
- Any flow ≥200 blocks = ARCH-002 🔴 Critical
- Single-block flows that are not a standard hold/whisper type = ARCH-003 🟢 Low

The limit is **200 blocks per flow**, not a byte size. Do not assert a flow
size limit in KB; none is documented.

### Check 9.2 — Error-Path Coverage (15 seconds max)

**Data source**: the sampled flow JSON from 9.1.

#### The metric that means something

The intuitive metric — "how many flows have no `Errors` transition anywhere" —
**measures flow type, not flow quality,** and must not be reported on its own.
On a measured instance it came out at 29 of 59 flows, which sounds alarming,
but the breakdown was:

| Type | No error branch | Reading |
|---|---|---|
| `CONTACT_FLOW` | 0 / 26 | every customer-facing flow handled errors |
| `CAMPAIGN` | 23 / 23 | structurally normal — nothing in them can fail |
| whisper / hold types | 1 / 1 each | structurally normal — they play a prompt |

A whisper flow that plays one prompt has no failure-capable block, so it has
nothing to handle and its missing `Errors` array is not a defect. The headline
"29 of 59" was composed almost entirely of such flows.

**Therefore:**
- **Anchor the check on failure-capable blocks, not on flows.** A block that
  can fail at runtime and has no `Errors` branch is a real defect regardless of
  which flow it sits in. That is ARCH-005 and it is the primary finding here.
- **Never report a single instance-wide "N of M flows lack error handling"
  figure.** Break it down by `Type` or do not report it.
- ARCH-004 applies only to flows that **contain at least one failure-capable
  block**. A flow with no such block is out of scope for it — do not count it.

**Derivation**:
```
FAILURE_CAPABLE = { InvokeLambdaFunction, GetParticipantInput,
                    ConnectParticipantWithLexBot, GetCustomerProfile,
                    InvokeExternalResource, TransferContactToQueue,
                    CreateWisdomSession, UpdateContactData }

for each sampled flow F:
    capable      = [A for A in F.Actions if A.Type in FAILURE_CAPABLE]
    unguarded    = [A for A in capable
                    if not A.Transitions.Errors]          → ARCH-005
    in_scope(F)  = len(capable) > 0
    no_path(F)   = in_scope(F) and no A in capable has a real handler
```

⚠️ **An `Errors` array can be non-empty and still handle nothing.** Entries
with `ErrorType` of `NoMatchingCondition` or `NoMatchingError` are the default
"else" branch of a condition check, not failure handling. Counting any
non-empty `Errors` array as handled inflates coverage: on the measured instance
29 flows had no `Errors` array at all, but **35** had no handler whose
`ErrorType` was anything other than those two defaults. When deciding whether a
block is guarded, require at least one entry whose `ErrorType` is **not** in
`{NoMatchingCondition, NoMatchingError}`, and say which rule you applied.

**Checks**:
- [ ] Failure-capable blocks with no real `Errors` branch, by flow and type
- [ ] Flows containing a failure-capable block but no real handler on any of
      them, counted **per flow `Type`**
- [ ] Error branches that terminate in `DisconnectParticipant` with no prior
      `MessageParticipant` — a silent hang-up

**Findings**:
- A failure-capable block with no real `Errors` branch = ARCH-005 🟠 High; name
  the flow and the block type. **This is the headline finding of this check.**
- A flow that has failure-capable blocks and no real handler on any of them =
  ARCH-004 🟠 High. Report it per flow `Type` and per the sample, never as a
  bare instance-wide count.
- An error branch that disconnects without a message = ARCH-006 🟡 Medium
- If every failure-capable block in the sample is guarded, **say so plainly and
  state the sample composition by `Type`.** A clean result on a
  `CONTACT_FLOW`-only sample is not a clean result for the instance.

### Check 9.3 — External Dependency Topology (20 seconds max)

**Data source**: the sampled flow JSON, plus:
```
connect:ListLambdaFunctions     (MaxResults max 25 — exceeding it hard-fails)
connect:ListBots                (MaxResults max 25)
connect:ListIntegrationAssociations
```

**Derivation**:
```
referenced_arns  = every arn:aws:... found in the sampled flow Content
associated_arns  = ListLambdaFunctions result

orphan_association = associated_arns − referenced_arns
                     (declared but no sampled flow invokes it)
unassociated_ref   = referenced_arns − associated_arns
                     (a flow invokes it but it is not associated → will fail)
cross_account      = any referenced ARN whose account ≠ the instance's account
cross_region       = any referenced ARN whose region ≠ the instance's region
```

**Checks**:
- [ ] Lambda ARNs referenced in flows vs associated with the instance
- [ ] Cross-account resource references
- [ ] Cross-region resource references
- [ ] Lex bot references vs associated bots
- [ ] Integration association types present

**Findings**:
- A flow references a Lambda that is **not associated** with the instance =
  ARCH-007 🔴 Critical. Connect will reject the invocation at runtime; the flow
  is broken on that path.
- A referenced resource is in a **different account** = ARCH-008 🟠 High. State
  both account IDs. Cross-account invocation requires a resource policy on the
  target; it is not inherently wrong, but it is an undeclared dependency and
  frequently a leftover from a sample or a copied flow.
- A referenced resource is in a **different region** = ARCH-009 🟠 High —
  adds cross-region latency to every contact on that path, and breaks a
  single-region DR assumption.
- An associated Lambda invoked by no sampled flow = ARCH-010 🟢 Low. Note the
  sampling caveat: an unsampled flow may use it, so report it as a candidate,
  not a confirmed orphan.

**Error handling**:
- `ListLambdaFunctions` with `MaxResults` above 25 returns
  `InvalidRequestException — Result Size cannot be larger than 25`. Re-issue
  with 25. This is not a permissions problem.

### Check 9.4 — Reuse and Modularity (10 seconds max)

**API calls**:
```
connect:ListContactFlowModules  (MaxResults up to 1000)
  + module-reference blocks in the sampled flow JSON
```

**Checks**:
- [ ] Flow modules defined on the instance
- [ ] Module-reference blocks across the sample
- [ ] Repeated block sequences across flows — candidates for extraction
- [ ] Repeated literal values (queue ARNs, prompts, phone numbers) appearing in
      many flows

**Findings**:
- Zero flow modules on an instance with more than 20 flows = ARCH-011 🟡 Medium.
  Every change must then be applied flow by flow, which is where copy
  proliferation (Check 9.5) comes from.
- A block sequence repeated in 3 or more flows = ARCH-012 🟢 Low

### Check 9.5 — Flow Lifecycle and Naming Hygiene (10 seconds max)

**Data source**: `ListContactFlows` metadata — no `Describe` needed, so this
check runs over the **full population**, not the sample. Say so in the output.

**Checks**:
- [ ] `Status: SAVED` flows — edited but never published
- [ ] `State: ARCHIVED` flows still referenced by a live flow or phone number
- [ ] Names containing `Copy of`, and the nesting depth of that phrase
- [ ] Names with a generated random suffix (trailing `-[a-z0-9]{10}`)
- [ ] Names still carrying the default `Sample ` prefix on a production instance
- [ ] Names matching `test|tmp|bak|delete|old|do not use`

**Findings**:
- A `SAVED` (unpublished) flow referenced by a phone number = ARCH-013 🔴
  Critical — callers hit the last published version, not the edited one
- `Copy of Copy of ...` nesting at depth ≥2 = ARCH-014 🟡 Medium. Report the
  maximum depth observed; deep nesting is a reliable marker of flow sprawl and
  of changes made by duplication rather than by modularisation.
- Default `Sample ` names on a production instance = ARCH-015 🟢 Low
- `ARCHIVED` flow still referenced = ARCH-016 🟠 High

### Check 9.6 — Data Storage Architecture (15 seconds max)

**API calls**:
```
connect:ListInstanceStorageConfigs
  --resource-type <TYPE>        ← REQUIRED, one call per type
```

Enumerate each type explicitly:
`CALL_RECORDINGS`, `CHAT_TRANSCRIPTS`, `SCHEDULED_REPORTS`, `MEDIA_STREAMS`,
`CONTACT_TRACE_RECORDS`, `AGENT_EVENTS`,
`REAL_TIME_CONTACT_ANALYSIS_SEGMENTS`, `ATTACHMENTS`, `CONTACT_EVALUATIONS`,
`SCREEN_RECORDINGS`.

**Checks**:
- [ ] Which resource types have a storage config and which do not
- [ ] `StorageType` per type — S3 vs KINESIS_STREAM vs KINESIS_FIREHOSE
- [ ] Whether analytics-bearing streams (`CONTACT_TRACE_RECORDS`,
      `AGENT_EVENTS`) are configured at all

**Findings**:
- `CONTACT_TRACE_RECORDS` not configured on a production instance = ARCH-017 🟠
  High. Without it there is no durable contact record export, so historical
  analysis and most BI depends entirely on the Connect console's retention.
- `AGENT_EVENTS` not configured = ARCH-018 🟡 Medium — no agent state history
- A storage type configured with no encryption key where one is supported =
  ARCH-019 🟡 Medium (cross-reference Pillar 2; do not duplicate the finding,
  reference it)

Report configured and unconfigured types as a table. An unconfigured type is
not automatically a defect — many are optional — so state the consequence
rather than asserting a gap.

### Check 9.7 — Routing Topology (15 seconds max)

**API calls**:
```
connect:ListRoutingProfiles
connect:ListRoutingProfileQueues    (per profile)
  EXTRACT: QueueName, Priority, Delay, Channel
connect:ListQueues                  (for orphan detection)
```

**Checks**:
- [ ] Queue fan-out per routing profile
- [ ] Priority and delay ladders — are they distinct or all identical?
- [ ] Queues attached to no routing profile (unreachable by routing)
- [ ] Routing profiles attached to no user (from Pillar 8 Check 8.2 data)
- [ ] A single queue serving every profile — a single point of congestion

**Findings**:
- A queue referenced by no routing profile = ARCH-020 🟡 Medium — contacts can
  only reach it by an explicit flow transfer
- All queues at identical `Priority` and `Delay` across every profile =
  ARCH-021 🟢 Low — the priority mechanism is configured but inert
- A routing profile with no assigned users = ARCH-022 🟡 Medium

### Check 9.8 — Entry-Point Topology and Reachability (15 seconds max)

**API calls**:
```
connect:ListPhoneNumbersV2          (MaxResults up to 1000)
  filter to numbers whose TargetArn is this instance or a TDG linked to it
connect:DescribePhoneNumber         (per number, sampled)
  + TransferToFlow / contact-flow ARNs found in the sampled flow JSON
```

**Derivation**:
```
entry_flows     = flows targeted by a claimed phone number
transfer_targets = flows referenced by a contact-flow ARN inside another flow
reachable        = entry_flows ∪ transfer_targets ∪ queue default flows
candidates_unreachable = all_flows − reachable
```

**Checks**:
- [ ] Numbers claimed but targeting nothing
- [ ] Numbers in a `FAILED` or `IN_PROGRESS` status
- [ ] Flows in `candidates_unreachable`

**Findings**:
- A claimed number with no flow target = ARCH-023 🟠 High — the number rings
  into nothing
- A number in `FAILED` status = ARCH-024 🟠 High
- Flows in `candidates_unreachable` = ARCH-025 🟢 Low. **Label this a candidate
  list, not a finding of dead code.** A flow can also be entered as a queue
  default, an agent whisper, an outbound whisper, or a campaign target, and the
  sample may not cover every referencing flow. Report the count and the method
  limitation together.

### Check 9.9 — Integration Topology (10 seconds max)

**API calls**:
```
connect:ListIntegrationAssociations
  EXTRACT: IntegrationType, IntegrationArn
```

**Checks**:
- [ ] Integration types present — `APPLICATION`, `WISDOM_ASSISTANT`,
      `WISDOM_KNOWLEDGE_BASE`, `Q_MESSAGE_TEMPLATES`, `CASES_DOMAIN`,
      `EVENT`, `FILE_SCANNER`, `SES_IDENTITY`, `ANALYTICS_CONNECTOR`, and others
- [ ] Associations whose target resource no longer resolves
- [ ] Q in Connect / Wisdom associations without a corresponding flow block
      (cross-reference Pillar 7; reference it rather than duplicating)

**Findings**:
- An association whose target cannot be resolved = ARCH-026 🟠 High
- An integration associated but referenced by no sampled flow = ARCH-027 🟢 Low,
  subject to the same sampling caveat as ARCH-010

## Must-Ask Inputs

| Input | Why it cannot be inferred | Blocks |
|---|---|---|
| Whether a flow's routing logic matches intent | The API returns structure, not intent | any correctness claim |
| Whether a restrictive pattern is deliberate | e.g. `ROUTE_CURRENT_CHANNEL_ONLY`, a single shared queue | ARCH-021, CAP-004 |
| Target or future-state architecture | A design decision, not an observable | any "should be" recommendation |
| Which flows are genuinely retired | Reachability analysis yields candidates only | ARCH-025 |

## Not Assessable From the API

State these plainly if asked; do not approximate them.

- **Flow correctness.** Structure is readable, intent is not. A flow can be
  perfectly formed and route every contact to the wrong queue.
- **Prompt and message content quality.** Audio prompts are referenced by ARN;
  their contents are not returned.
- **Service-team roadmap fit, preview-feature eligibility, limit exceptions.**
  These need an AWS account team or service team.
- **Whether a cross-account dependency is sanctioned.** The reference is
  observable; the agreement behind it is not.

## Findings Summary

| Finding | Trigger | Severity |
|---------|---------|----------|
| ARCH-001 | Flow ≥180 blocks (approaching the 200 limit) | 🟠 High |
| ARCH-002 | Flow ≥200 blocks | 🔴 Critical |
| ARCH-003 | Single-block non-standard flow | 🟢 Low |
| ARCH-004 | Flow with failure-capable blocks and no real error path on any of them | 🟠 High |
| ARCH-005 | Failure-capable block with no real `Errors` branch | 🟠 High |
| ARCH-006 | Error branch disconnects with no message | 🟡 Medium |
| ARCH-007 | Flow references a Lambda not associated with the instance | 🔴 Critical |
| ARCH-008 | Cross-account resource reference in a flow | 🟠 High |
| ARCH-009 | Cross-region resource reference in a flow | 🟠 High |
| ARCH-010 | Associated Lambda invoked by no sampled flow | 🟢 Low |
| ARCH-011 | Zero flow modules on an instance with >20 flows | 🟡 Medium |
| ARCH-012 | Block sequence repeated in ≥3 flows | 🟢 Low |
| ARCH-013 | Unpublished (`SAVED`) flow referenced by a phone number | 🔴 Critical |
| ARCH-014 | `Copy of` nesting at depth ≥2 | 🟡 Medium |
| ARCH-015 | Default `Sample ` flow names on production | 🟢 Low |
| ARCH-016 | `ARCHIVED` flow still referenced | 🟠 High |
| ARCH-017 | `CONTACT_TRACE_RECORDS` storage not configured | 🟠 High |
| ARCH-018 | `AGENT_EVENTS` storage not configured | 🟡 Medium |
| ARCH-019 | Storage type without an encryption key where supported | 🟡 Medium |
| ARCH-020 | Queue referenced by no routing profile | 🟡 Medium |
| ARCH-021 | Identical priority/delay across all profiles | 🟢 Low |
| ARCH-022 | Routing profile with no assigned users | 🟡 Medium |
| ARCH-023 | Claimed number with no flow target | 🟠 High |
| ARCH-024 | Phone number in `FAILED` status | 🟠 High |
| ARCH-025 | Flows with no detected entry path (candidates) | 🟢 Low |
| ARCH-026 | Integration association target unresolvable | 🟠 High |
| ARCH-027 | Integration associated but unreferenced in the sample | 🟢 Low |
| ARCH-028 | `DescribeContactFlow` returns no `Content` — structural analysis unavailable | 🟡 Medium |

**ARCH-001 through ARCH-012 and ARCH-025 depend on sampled flow JSON.** State
the sample size alongside every one of them, and never present a sampled share
as a measured population rate.

## Architecture Summary Table

| Dimension | Status |
|-----------|--------|
| Flow structural analysis available | {✅ / ❌ Content absent} |
| Flows sampled / total | {n} / {N} |
| Error-path coverage (sample) | {✅ all / ⚠️ n flows bare / ➖} |
| External dependencies resolve | {✅ / ❌ n broken} |
| Cross-account or cross-region references | {✅ none / ⚠️ n found} |
| Flow modularity | {✅ modules in use / ❌ none} |
| Lifecycle hygiene | {✅ / ⚠️ copy sprawl / ❌ unpublished in production} |
| Contact-record export configured | {✅ / ❌} |
| Routing topology | {✅ / ⚠️} |
| All claimed numbers reach a flow | {✅ / ❌ n orphaned} |

## Timeout Priority

```
MUST RUN:    9.1 (structure) → 9.2 (error paths)
HIGH VALUE:  9.3 (dependencies) — finds runtime-breaking references
HIGH VALUE:  9.5 (lifecycle) — metadata only, full population, very cheap
PARALLEL:    9.6, 9.7, 9.8, 9.9
DROP FIRST:  9.4 (modularity), then 9.9 (integrations)
```

Reduce the sample size before dropping a check: 10 flows analysed across 9.1–9.5
is worth more than 25 flows analysed for structure alone. Record the reduced
sample size in the output.

## Retry Policy (Pillar 9 Specific)

```
RETRY (once, 2s wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, session policy errors

Check 9.1: DescribeContactFlow failure on a sampled flow → drop that flow from
           the sample, reduce the denominator, continue
Check 9.1: Content present but not valid JSON → report ARCH-028 for that flow,
           do not guess its structure
Check 9.3: ListLambdaFunctions MaxResults error → re-issue with 25
Check 9.6: ParamValidation on ListInstanceStorageConfigs → you omitted
           --resource-type; re-issue per type
Check 9.8: DescribePhoneNumber failure → reduce the number sample, continue
```
