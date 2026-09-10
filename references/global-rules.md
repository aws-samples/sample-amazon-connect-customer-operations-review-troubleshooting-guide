# Global Rules — Shared Across All Operations Review Pillars

## Read-Only by Default

**This skill operates in read-only mode by default.** Assessment, discovery, and troubleshooting diagnosis use only List/Describe/Get-type API calls (e.g., `describe-instance`, `list-approved-origins`, `get-current-metric-data`). No mutating call (Create/Update/Put/Delete/Associate/Disassociate/Enable/Disable, etc.) is issued unless the customer has explicitly asked for that specific fix to be applied, AND the two-gate confirmation sequence below has completed.

- Producing findings, a remediation plan, or CLI commands for a fix is NOT the same as applying it. Presenting the `aws connect update-instance-attribute ...` command for a finding is fine; running it is not, until asked.
- If a customer asks for a full operations review or troubleshooting pass without also asking to "fix it" / "apply it" / "go ahead", treat the entire engagement as read-only — diagnose and report only.

## Two-Gate Confirmation Sequence for Any Write

A customer saying "yes, fix it" or "go ahead" is **Gate 1 only** — general intent to remediate. It is NOT sufficient on its own to issue a mutating call. A second, more specific confirmation (**Gate 2**) is required after the agent has proposed the concrete change. Do not collapse these into a single step.

### Gate 1 — General Intent

The customer asks for a specific finding/symptom to be fixed (e.g., "fix SEC-001", "enable contact flow logging", "go ahead and apply that").

→ Proceed to build the Change Proposal below. Do NOT issue any mutating call yet.

### Change Proposal (Agent Output — Required Before Gate 2)

Before asking for final confirmation, the agent MUST present a change proposal covering all of the following, specific to the actual resource and current retrieved state — not generic boilerplate:

1. **What is about to change** — the exact resource(s) affected (instance ID/alias, flow ID, queue ARN, etc.)
2. **How it will change** — the exact CLI command(s)/API call(s) and parameters that will be run
3. **Before state** — the current value/configuration, from data already retrieved this session (cite source per the Grounding Rules below)
4. **After state** — what the value/configuration will be once the change is applied
5. **Rollback** — the exact command(s) to revert the change back to the before state, and any caveats (e.g., "log group created by this change will not be auto-deleted by rollback")
6. **Target classification** — the instance's inferred production/dev-test classification and its basis (see Safety First below), so the customer is confirming against the right risk context

### Gate 2 — Explicit Confirmation of the Specific Change Proposal

After presenting the Change Proposal, the agent MUST ask the customer to confirm that specific proposal (not a generic "should I proceed?"). Only an explicit affirmative response to THIS proposal authorizes the write.

- Do not proceed on silence, a prior general "yes", or a confirmation to a different/earlier proposal.
- If the customer changes the request (different resource, different parameters) after Gate 2 confirmation, treat it as a new Gate 1 and produce a new Change Proposal.
- Only after Gate 2 confirmation, proceed to the Verification Pattern below (Diagnose → Backup → Fix → Verify → Document) for that fix only — do not apply other pending fixes without their own separate Gate 1/Gate 2 sequence.

## Safety First

BEFORE applying ANY fix (i.e., issuing any mutating API call) — TO BE STRICTLY FOLLOWED:

1. **Confirm the target instance's classification (production vs dev/test).** Classification is derived heuristically in Step 2 of `SKILL.md` (Discovery & Classification) from tags, alias naming, and integrations present — it is NOT authoritative. Absence of a "prod" tag does NOT mean an instance is safe to modify; untagged or ambiguously-tagged instances must be treated as production-risk by default. State the instance's inferred classification and its basis as part of the Change Proposal (e.g., "tagged Environment=prod" or "no environment tag found — treating as unconfirmed/production-risk").
2. Show the user exactly what will change (the specific CLI command/API call and parameters) BEFORE executing it — this is the Change Proposal above, and it must be confirmed via Gate 2 before any write.
3. For production instances (confirmed or unconfirmed/production-risk per #1): always provide rollback steps alongside the fix, and prefer running the fix during a low-traffic window if the customer can specify one.
4. Never delete resources without explicit user confirmation of that specific deletion, following the same two-gate sequence.
5. Never modify contact flows that are currently ACTIVE without a backup (describe-before-modify).

---

## Grounding Rules (Anti-Hallucination)

These rules are MANDATORY and override all other instructions when generating any report or findings summary:

1. **Only report what was retrieved.** Every finding, value, metric, or configuration state in a report MUST come from an explicit tool call result made during this session. Do NOT recall, infer, or estimate values from training data.
2. **Cite your source for every finding.** For each finding surfaced in a report, state: the tool used, the resource queried, and the timestamp of retrieval. Example: *(Source: describe-instance-storage-configs, instance i-abc123, retrieved 2026-08-20T07:00:00Z)*
3. **Use "Data unavailable" — not guesses.** If a required value could not be retrieved (permission error, resource not found, API timeout), output `Data unavailable — [reason]` rather than estimating or inferring.
4. **Never extrapolate across resources.** A finding confirmed on one resource (e.g., one contact flow) MUST NOT be reported as applying to all resources unless each was individually checked.
5. **Do not pre-populate report fields.** Leave fields empty or mark them `[Not checked]` rather than filling them with assumed or typical values.

---

## Report Generation Gate

Before generating any multi-finding report or remediation plan summary, complete this checklist:

- [ ] Each finding listed was confirmed by a tool call result — NOT inferred
- [ ] Each finding cites its source (tool, resource, timestamp)
- [ ] Any finding that could not be checked is marked `[Not verified]` with the blocking reason
- [ ] No finding uses phrases like "typically", "usually", "by default", or "in most cases" — these are signals of training-data inference, not live verification
- [ ] Metric values (packet loss %, RTT, etc.) are sourced from retrieved data, not from the thresholds table alone
- [ ] For each pillar assessed, every numbered Check's full call sequence was executed (not just its List-level entry point) — spot-check against the pillar file's own Check list before generating the report


If any item is unchecked, do NOT generate the report. Return to data collection.

---

## Verification Pattern

Applies only after both Gate 1 and Gate 2 of the Two-Gate Confirmation Sequence above have completed for a specific fix. Every fix follows: Diagnose → Backup → Fix → Verify → Document

1. **DIAGNOSE:** Confirm the issue exists (re-run the check)
2. **BACKUP:** Save current state (describe before modify) — this is the "Before state" from the Change Proposal, captured fresh immediately before the write
3. **FIX:** Apply the remediation — the one mutating call(s) confirmed in the Change Proposal, nothing broader
4. **VERIFY:** Re-run the original check to confirm resolution matches the "After state" promised in the Change Proposal
5. **DOCUMENT:** Record what was changed, when, by whom, and restate the rollback command for future reference

---

## Standard Timeout Handling

```
At 70 seconds: Stop issuing new API calls.
At 80 seconds: Produce findings from data collected so far.
Uncompleted checks: Mark as "NOT_ASSESSED: timeout" in output.
```

**Priority order if timeout approaching:**
- MUST RUN: Critical path checks first (safety, security, reliability)
- HIGH VALUE: Checks with high signal-to-cost ratio
- DROP IF NEEDED: Low-signal analysis-only checks

See individual pillar files for specific check priorities.

---

## Standard Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, ResourceNotFoundException, session policy errors

If a pre-flight test fails for a check:
  - SKIP ENTIRE CHECK
  - Note in output: "[Check name] — SKIPPED: [reason]"
  - Continue with remaining checks
```

**Per-check error handling:** See individual pillar files for service-specific retry logic (wisdom:*, lambda:*, ce:*, etc.).

---

## Standard Findings Output Format

```markdown
## Pillar [X]: [Pillar Name] — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- APIs timed out: {n}
- Assessment completeness: {%}

### Findings

#### 🔴 CRITICAL
- [FINDING-ID] Title
  - Impact: What happens if not fixed
  - Source: Tool, resource, timestamp
  - Fix: Reference to Pattern or link to remediation (not yet applied — awaiting Gate 1 + Change Proposal + Gate 2)

#### 🟠 HIGH
- [FINDING-ID] Title
  - Impact: Description
  - Fix: Action (not yet applied — awaiting Gate 1 + Change Proposal + Gate 2)

#### 🟡 MEDIUM
- [FINDING-ID] Title
- [FINDING-ID] Title

#### 🟢 LOW
- [FINDING-ID] Title

### Recommendations (Prioritized)
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]
```

**Rules:**
- Every finding MUST cite its source (API call, resource queried, timestamp)
- Every finding MUST explain the impact
- CRITICAL findings MUST have a clear fix path
- Findings MUST be specific (not generic "review X")
- Numbers MUST come from retrieved data, not assumptions
- Findings and remediation plans are diagnostic output only — no fix is applied as part of producing this report; applying any fix requires the full Two-Gate Confirmation Sequence
