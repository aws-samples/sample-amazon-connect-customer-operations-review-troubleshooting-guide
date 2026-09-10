# Amazon Connect Operations Review & Troubleshooting Guide

A structured, read-only-by-default skill for running Well-Architected operations reviews
and troubleshooting Amazon Connect instances — usable by any AI tool with AWS CLI/SDK
access, not just this agent.

## What This Skill Is For

Two related jobs, one skill:

1. **Operations Review** — a full or partial Well-Architected assessment of one or more
   Connect instances across 7 pillars (Operational Excellence, Security, Reliability,
   Performance, Cost, Sustainability, Generative AI).
2. **Troubleshooting & Remediation** — diagnosing a specific finding (e.g. `SEC-001`,
   `REL-011`) or an open-ended symptom (choppy calls, missing CTRs, ACGR out of sync),
   and proposing — but never silently applying — a fix.

Every review and every troubleshooting pass ends with the same guarantee: findings are
evidence-backed, cross-referenced to a runbook, and nothing gets written to your Connect
instance without you explicitly asking for it and then confirming the exact change.

## What's Expected of You (the Audience)

Before you invoke this skill, know that:

- **You bring the scope, or you answer when asked.** Have your target account(s),
  region(s), instance(s), and pillar(s) in mind. If you don't provide them, the skill
  will resolve what it can automatically (current account, common regions, instance
  discovery) and ask you to pick from what it finds — it won't silently assume.
- **You will be asked about call quality, every time.** This is a mandatory question on
  every pass, regardless of what you originally asked about. Answer honestly — a "no
  issues" only counts if you actually said so.
- **You decide if anything gets fixed.** All output is diagnosis and proposals. A fix is
  only applied if you (a) explicitly ask for that specific fix, and (b) explicitly
  confirm the concrete before/after/rollback plan you're shown. No exceptions, even for
  low-risk changes.
- **You should expect citations, not guesses.** Every finding is backed by a specific
  API call, resource, and timestamp. If data can't be retrieved, you'll see
  `Data unavailable — [reason]` instead of a guess. If something looks off, ask for the
  source.
- **You may need to help classify the instance.** Production vs. dev/test
  classification is inferred from tags and integrations, not authoritative — flag it
  early if the skill gets your environment wrong, especially before any write is
  proposed.

## How a Review Actually Runs

1. **Scope it** — accounts, regions, instances, and pillars are confirmed or discovered.
2. **Discover & classify** — instances are enumerated and tagged as Production,
   Dev/Test, Abandoned, AI-Focused, Campaign, or DR Replica (heuristic, not final).
3. **Assess** — the selected pillar(s) run their checks; every finding produced,
   regardless of severity, is mapped to a runbook category and diagnosed/verified —
   never left as a bare finding with no follow-up.
4. **Report** — executive summary, discovery table, findings, a troubleshooting guide
   entry per finding, a call-quality section, and a prioritized remediation plan
   (Immediate / This Sprint / Next Sprint / Backlog).

Nothing is applied at the end of this — the report is a proposal set, not a change log.

## Runbook Categories

| Category | Covers |
|---|---|
| A — Contact Flow & Logging | Logging gaps, invisible flow errors |
| B — Monitoring & Alarms | Missing CloudWatch alarms, operational blindness |
| C — Security & Access | Approved origins, encryption, KMS, IAM errors |
| D — Telephony & Call Quality | Mandatory intake + agent-side, carrier-side, CCP log issues |
| E — Integrations | Lex test-alias-in-prod, AI guardrail gaps |
| F — Reliability & DR | Traffic Distribution Groups, ACGR sync and failure recovery |
| G — Cost | Storage lifecycle, cost spike investigation |
| H — Metrics & Session Policy | Session-policy metric blockers, Contact Lens test rules |
| Z — Catch-All | Anything not yet mapped — diagnosed under Z1, never dropped |

## Ground Rules You Can Rely On

- **Read-only by default.** Every AWS call used for diagnosis is non-mutating.
- **Two-Gate Confirmation for any write.** General intent, then a concrete change
  proposal, then explicit re-confirmation — only then does anything execute.
- **No extrapolation.** A finding on one resource is never assumed true for a similar
  one unless it was checked individually.
- **No default-value assumptions** — e.g., contact flow logging must be verified at both
  instance and flow level; Lambda timeout in a contact flow is a fixed 8 seconds; DTMF
  is only captured in "Get customer input" blocks; CTRs may take up to 24 hours without
  Kinesis streaming.

## Example Requests

Run a full operations review on our Connect instance in us-east-1.
Just check our security posture — do we have any open findings?
Fix SEC-001 — walk me through the change and rollback before doing anything.
Agents are reporting choppy audio on calls today. Investigate call quality.
Check whether ACGR is still syncing between our primary and DR replica instances.


## Prerequisites

- AWS CLI/SDK access with `connect`, `cloudwatch`, `logs`, `lambda`, `wisdom`,
  `cloudtrail`, and `iam` (read) permissions
- Contact flow logs enabled at the instance level if flow-level diagnosis is needed
  (the skill will tell you if it isn't)
- For CCP/call-quality diagnosis: be ready to share browser dev tools output or network
  diagnostics if asked — CCP logs are session-scoped and clear on refresh

## Adding This Skill to Your Agent Space

To make this skill available to your AWS DevOps Agent:

1. Package the skill directory (`SKILL.md` plus everything under `references/`) as a
   `.zip` — keep the folder structure intact, don't flatten it.
2. Open your AWS DevOps Agent space in the console.
3. Go to the **Skills** section of the space.
4. Select **Add skill → Upload skill**, and upload the `.zip` package.
5. Confirm the skill appears in the space's skill list and shows as **active**.

That's it — no separate install step. The agent loads `SKILL.md` and pulls in files
under `references/` on demand as its workflow calls for them, so nothing needs to be
pre-registered beyond the upload itself.

**Sanity check after upload:** ask the agent to run a small, low-stakes request (e.g.
"check our security posture" on a single instance). If the response follows this
skill's structure — findings with citations, a troubleshooting cross-reference per
finding, and the mandatory call-quality question — the skill loaded correctly. If it
doesn't, re-upload and confirm the skill shows as active before retrying.

**Updating later:** re-zip and re-upload using the same **Add skill → Upload skill**
flow — this replaces the previous version rather than creating a duplicate.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

