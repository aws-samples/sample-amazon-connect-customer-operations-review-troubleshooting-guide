# Amazon Connect Well-Architected Toolkit

> Formerly "Amazon Connect Operations Review & Troubleshooting Guide." The display name changed in 1.4.0; the skill identifier (`amazon-connect-ops-review-troubleshooting-guide`) and repository name are unchanged.

A structured, read-only-by-default skill for running Well-Architected operations reviews
and troubleshooting Amazon Connect instances — usable by any AI tool with AWS CLI/SDK
access, not just a specific agentic tool.

## What This Skill Is For

Three related jobs, one skill:

1. **Operations Review** — a full or partial Well-Architected assessment of one or more
   Connect instances across 7 pillars (Operational Excellence, Security, Reliability,
   Performance, Cost, Sustainability, Generative AI).
2. **Troubleshooting & Remediation** — diagnosing a specific finding (e.g. `SEC-001`,
   `REL-011`) or an open-ended symptom (choppy calls, missing CTRs, ACGR out of sync),
   and proposing — but never silently applying — a fix.
3. **Region Readiness** — *before* anything is built, tells you which AWS Region can deliver
   the Connect features, phone numbers (by country and type), outbound and campaign
   destinations, agent locations, and Global Resiliency pairing you need. It needs no AWS
   account access: a deterministic script (`scripts/region_readiness.py`) evaluates your
   requirements against a dated snapshot of the official AWS sources and returns a
   per-Region verdict with `REG-xxx` findings, citations, and a recommendation.

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
| R — Region Readiness | Feature / telephony / campaign / DR fit of a Region (`REG-001`–`REG-013`) |
| Z — Catch-All | Anything not yet mapped — diagnosed under Z1, never dropped |

## Ground Rules You Can Rely On

- **Read-only by default.** Every AWS call used for diagnosis is non-mutating.
- **Two-Gate Confirmation for any write.** General intent, then a concrete change
  proposal, then explicit re-confirmation — only then does anything execute.
- **No extrapolation.** A finding on one resource is never assumed true for a similar
  one unless it was checked individually.
- **No default-value assumptions** — e.g., contact flow logging must be verified at both
  instance and flow level; a contact flow's Lambda block timeout is configurable up to 8s
  (synchronous) / 60s (asynchronous); DTMF is only captured in "Get customer input" blocks;
  contact records are delivered at least once and retained for 24 months (use Kinesis
  streaming for near-real-time delivery).

## Example Requests

Run a full operations review on our Connect instance in us-east-1.
Just check our security posture — do we have any open findings?
Fix SEC-001 — walk me through the change and rollback before doing anything.
Agents are reporting choppy audio on calls today. Investigate call quality.
Check whether ACGR is still syncing between our primary and DR replica instances.
Which Region should we use? We need UK and South African numbers, Contact Lens, and outbound campaigns to the UK.
Can our eu-west-2 instance run outbound campaigns to US numbers?


## Region Readiness — run it yourself

No AWS credentials needed. Python 3.8+ (standard library only):

```bash
python3 scripts/region_readiness.py --template > requirements.json   # fill it in
python3 scripts/region_readiness.py --input requirements.json         # Markdown report
python3 scripts/region_readiness.py --list-features                   # feature keys
python3 scripts/region_readiness.py --country "Japan"                 # one-country telephony lookup
```

What it checks, per Amazon Connect home Region:

- **Features**, including sub-features: Contact Lens analytics by type, messaging channels, agent assist, forecasting, Cases, Customer Profiles, agentic voice, and more
- **Phone numbers**: where each country/type can be claimed, national/international outbound, porting, multi-carrier, custom caller ID, GA/Beta status, KYC documents, and agent-location rules
- **Outbound calling**: the default allow-list per Region and the outbound campaign destinations per Region
- **Global Resiliency**: the supported Region pairings and prerequisites
- **Agent isolation and latency anchoring**, from AWS architecture guidance

The data is a **point-in-time snapshot** (`references/region-data/connect-region-data.json`; its
date is printed on every report). Maintainers refresh it with
`python3 scripts/build_region_data.py` (needs network and `pip install pdfplumber`). The build
verifies that every tick in the Telecoms Coverage Guide was parsed, and that every quoted
AWS sentence still appears on its page. Review `parse_warnings` in the JSON before shipping a
refresh.

Sources: [Supported Regions](https://docs.aws.amazon.com/connect/latest/adminguide/regions.html) ·
[Telecoms Coverage Guide (PDF)](https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf) ·
[Phone number requirements by country](https://docs.aws.amazon.com/connect/latest/adminguide/phone-number-requirements.html) ·
[Default outbound countries](https://docs.aws.amazon.com/connect/latest/adminguide/country-code-allow-list.html) ·
[Global Resiliency replicas](https://docs.aws.amazon.com/connect/latest/adminguide/create-replica-connect-instance.html) ·
[Low-latency design](https://docs.aws.amazon.com/connect/latest/adminguide/low-latency-design.html) ·
[Region selection](https://docs.aws.amazon.com/connect/latest/adminguide/operational-excellence.html) ·
[Single vs multiple instances](https://docs.aws.amazon.com/connect/latest/adminguide/single-instance-multiple-instances.html) ·
[Supported languages](https://docs.aws.amazon.com/connect/latest/adminguide/supported-languages.html)

## Prerequisites

- AWS CLI/SDK access with `connect`, `cloudwatch`, `logs`, `lambda`, `wisdom`,
  `cloudtrail`, and `iam` (read) permissions (not needed for Region Readiness)
- Contact flow logs enabled at the instance level if flow-level diagnosis is needed
  (the skill will tell you if it isn't)
- For CCP/call-quality diagnosis: be ready to share browser dev tools output or network
  diagnostics if asked — CCP logs are session-scoped and clear on refresh

## Adding This Skill to Your Agent Space

To make this skill available to your AWS DevOps Agent:

1. Package the skill directory as a `.zip` — keep the folder structure intact, don't
   flatten it. Include `SKILL.md` (must sit at the archive root) plus everything under
   `references/`. **Exclude development-only files** — they aren't needed at runtime and
   only bloat the upload:

   ```bash
   zip -r amazon-connect-ops-review-troubleshooting-guide.zip . \
     -x '.git/*' '.gitignore' '.gitallowed' \
        'CHANGELOG.md' '.skilleval.yaml' 'evals/*' 'CONTRIBUTING.md' 'CODE_OF_CONDUCT.md' \
        '*/__pycache__/*' '*.DS_Store'
   ```

   The runtime package is `SKILL.md` + `references/` + `scripts/`. If your agent can't
   execute Python, Region Readiness falls back to `references/region-readiness-matrix.md`. `.skilleval.yaml` and `evals/`
   are test assets (skill-eval definitions); `CHANGELOG.md` and the git files are
   repo hygiene. This skill is platform-agnostic — any AI tool with AWS CLI/SDK access can
   load `SKILL.md` and pull in `references/` on demand; the steps below cover the AWS
   DevOps Agent specifically.
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

