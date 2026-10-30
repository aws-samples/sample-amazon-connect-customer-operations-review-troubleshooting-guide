# Changelog

All notable changes to this skill are documented here. Versions are tagged in git
(`v1.0.0`, `v1.1.0`, …) so any release can be checked out or reverted directly.

## [1.5.0] - 2026-10-26
### Added
- **Cost Optimization module** (menu option 4) — `references/cost-optimization.md`. Spend
  baseline from Cost Explorer (by service, usage type and `aws:connect:instanceId` tag),
  forecast and Cost Anomaly Detection findings; lever evaluation for phone numbers,
  telephony mix, pricing-plan-gated feature ROI, idle instances, recording storage and spend
  hygiene; quantify-and-rank with stated formulas; `CSO-001`–`CSO-019` finding catalog.
  Ported from the `connect-cost-optimization` skill with every MCP tool replaced by direct
  read-only AWS CLI/SDK calls.
- **Peak Readiness module** (menu option 5) — `references/peak-readiness.md`. Event
  intake, capacity/quota headroom (CloudWatch concurrency + GetMetricDataV2 baseline +
  Service Quotas), IVR Lambda / Lex / resiliency / network checks, monitoring and
  staffing/routing preparedness, attestation vocabulary, READY / READY WITH ACTIONS /
  NOT READY verdict, machine-readable JSON verdict, `PEAK-xxx` finding catalog. Ported from
  the `connect-scale-readiness` skill with every MCP tool replaced by direct read-only calls.
- Evals: 4 functional evals and 4 positive / 1 negative trigger queries for the two modules.
## [1.4.0] - 2026-10-06
### Added
- **Region Readiness mode.** A self-service, pre-build check of which Amazon Connect home
  Region can deliver a customer's features, phone numbers, outbound/campaign destinations,
  agent locations, and Global Resiliency pairing. It needs no AWS account access.
  - `references/region-readiness.md` — mode procedure (R0 snapshot check → R1 intake →
    R2 evaluate → R3 interpret → R4 optional read-only live check → R5 report), an
    existing-instance hook for Operations Reviews, manual rules for agents that can't run
    code, and the `REG-001`–`REG-013` finding catalog.
  - `scripts/region_readiness.py` — deterministic evaluator (stdlib Python). It produces a
    per-Region verdict, findings with source URLs, a ranked scorecard, a single-Region or
    multi-instance recommendation, and a separate list of design blockers that no Region fixes.
  - `references/region-data/connect-region-data.json` — dated snapshot built from the
    Supported Regions page, the Telecoms Coverage Guide PDF (last updated 1 Oct 2026), the
    phone-number requirements page, the default outbound allow-list page, the Global
    Resiliency replica/requirements pages, the low-latency design page, the Region-selection
    and single-vs-multi-instance architecture guidance, and the supported-languages page.
  - `references/region-readiness-matrix.md` — generated, human-readable copy of the snapshot.
  - `scripts/build_region_data.py` — maintainer refresh tool. Integrity checks: every
    green/yellow/red mark in the PDF (866/12/988) must be parsed exactly once, and every
    quoted AWS sentence must still appear on its page. Anything else goes to `parse_warnings`.
- Runbook Category **R — Region Readiness** and symptom-lookup rows ("can't claim a number",
  "campaign calls fail to a country", "can't create a replica", "which Region?").
- Operations Review now cross-checks each discovered instance's Region against its
  retrieved configuration (numbers, Contact Lens, campaigns, Cases, agent assist, TDGs).
- Grounding rule 6 (`global-rules.md`): Region facts come only from the cited snapshot or a
  live fetch made this session, never from memory.
- Evals: 4 functional evals (campaign destinations, Global Resiliency pairs, South Africa
  recommendation, no-memory UNKNOWN), 4 positive and 1 negative trigger query, and a
  `region-requirements-za.json` fixture. The Telecoms guide domain was added to `.skilleval.yaml`
  `safe_domains`.
- **Module selection gate** in `SKILL.md`: on invocation the skill presents a 1/2/3 menu
  (Review | Troubleshoot | Region Readiness) and runs only the chosen module, confirming
  even when the opening message implies one. The Review→Region-Readiness cross-check is
  preserved as the one documented cross-module exception.
- **Example prompts** — three per module in `SKILL.md` as user starting points.
- **Live-first Region Readiness.** The mode now fetches the decisive live AWS page per
  question by default and falls back to the bundled snapshot only when a fetch isn't
  possible, citing which source it used. The Amazon Connect pricing page was added as a
  reference source. `region_readiness.py` stamps its output as snapshot-based (offline
  fallback) so a direct script run is never mistaken for live data.
- **Mandatory deep-dive** for operations reviews: every in-scope check runs its
  `List*`→`Describe*`/`Get*` tier (sampling within a check allowed; skipping the Get tier
  is not), nothing is reported from a List-level status alone, and the Step 4 report is
  gated on the Report Generation Gate — uncompleted checks are marked `[Not checked]`,
  never silently downgraded.
### Changed
- `SKILL.md` retitled **Amazon Connect Well-Architected Toolkit** (display name and
  description); the skill identifier and repository name are unchanged for this release.
- `SKILL.md`: new Modes table (Review | Troubleshoot | Region Readiness), When-to-Use triggers,
  Region gotchas, reference list. The frontmatter description now covers Region Readiness.
- Call Quality Intake (D0) doesn't apply to a standalone Region Readiness run for a contact
  center that isn't live yet. It applies as soon as the run touches an existing instance.
- README packaging: the runtime package now includes `scripts/`.
### Notes
- Source discrepancies are surfaced as `REG-011` rather than resolved silently. Example: the
  phone-number requirements page excludes Africa (Cape Town) and GovCloud by default, but
  the Telecoms guide lists "All commercial regions" for most countries.
- Not evaluated per Region: language/locale support, and the Email channel (absent from
  the Supported Regions page). Both are reported as "Not evaluated" / `UNKNOWN`.

## [1.3.0] - 2026-09-21
### Fixed
Accuracy corrections from a verification test against the live Connect API, the AWS CLI
service model (botocore), and AWS documentation. Every change below was verified against a
cited authority before editing.
- **Instance attribute enums.** `CONTACT_FLOW_LOGS` → `CONTACTFLOW_LOGS` (the real
  `DescribeInstanceAttribute` enum has no underscore between CONTACT and FLOW), across
  `SKILL.md`, the orchestrator, pillar 1, `waf-pillar-checks.md`, and `troubleshooting-guide.md`.
  `CONTACT_LENS_VOICE`/`CONTACT_LENS_CHAT` → the only valid enum `CONTACT_LENS`. The attribute
  value is `true`/`false`, not `ENABLED`/`DISABLED`.
- **Removed all Voice ID content.** AWS ended support for Amazon Connect Voice ID on
  2026-05-20, and `VOICEID` was never a valid `DescribeInstanceAttribute` type. Removed the
  attribute, the `VOICE_ID` integration checks, and the SUS-007 / pillar-7 Voice ID findings.
- **CloudWatch metric names.** Phantom `AWS/Connect` metrics corrected: `ContactsInQueue` →
  `QueueSize`, `OldestContactAge` → `LongestQueueWaitTime`, `FromInstancePacketLossRate` →
  `ToInstancePacketLossRate` (only the "To" metric exists) with its correct dimensions
  (Participant, Type of Connection, Instance ID, Stream Type). Clarified that agent/handle-time
  figures (ContactsHandled, ContactsAbandoned, AgentInteractionDuration, AfterContactWorkTime,
  HandleTime) are historical/real-time metrics via `GetMetricDataV2`/`GetCurrentMetricData`, not
  CloudWatch metrics, and cannot be alarmed on directly.
- **API names (verified against the botocore connect model).** `ListNotificationRules` →
  `ListRules`; `CreateContactEvaluation` → `StartContactEvaluation`; removed `DescribeLexBot`
  (no such op); moved `ListRealtimeContactAnalysisSegments` (V1) to the `connect-contact-lens`
  namespace (V2 stays in `connect:`). Documented the required `--resource-type` on
  `list-instance-storage-configs` / `describe-instance-storage-config`.
- **ACGR DR runbook.** Corrected `update-traffic-distribution` shape: three independent params
  each with a `Distributions` list (not a nested `TelephonyDistribution`), and `--sign-in-config`
  uses a boolean `Enabled`, not a percentage. Fixed the `get-traffic-distribution` query to
  `TelephonyConfig.Distributions`. Added the required `--replica-alias` to `replicate-instance`.
  Replaced the invalid `INSTANCE_QUOTA` code with a name-based quota lookup.
- **Portability.** GNU-only `date -u -d '… ago'` now falls back to BSD/macOS `date -u -v`;
  `watch -n` replaced with a portable poll loop.
- **Service quotas.** Corrected hardcoded defaults (flows per instance 500 → 100; routing
  profiles 4000 → 500; users 500 confirmed) and changed Check 3.6 to retrieve *applied* quotas
  live via `service-quotas list-service-quotas` instead of assuming defaults.
- **Documented facts.** Lambda flow-block timeout is configurable up to 8s (sync) / 60s (async),
  not a fixed non-configurable 8s; removed the anti-hallucination rule that forbade the correct
  answer. Removed the unsupported 32 KB flow-definition limit (real limit: <200 blocks / <1 MB).
  Corrected the TCP 443 "TURN/media fallback" claim (media/TURN is UDP 3478; TCP 443 is
  signalling/control). Removed the unsupported "contact records may take up to 24 hours"
  delivery claim (delivery is at-least-once; 24-**month** retention is correct) and noted "CTR"
  is the former term for "contact record".
- **File hygiene.** Fixed the broken `call-quality-playbook.md` reference (actual file is
  `call_quality_playbook.md`); removed dangling references to non-shipped `worked-example.md`
  and `SKILL-troubleshoot.md`.
- **Frontmatter.** Added `author` to the metadata block.

## [1.2.0] - 2026-09-19
### Changed
- **De-duplicated discovery/classification.** `connect-ops-review-orchestrator.md` is now
  the single canonical source for the classification criteria and region-scanning strategy;
  `SKILL.md` Step 2 and `scoping-gate.md` point to it instead of restating the criteria
  table and region list (removes drift risk). The safety principle "unconfirmed =
  production-risk" is retained inline in `SKILL.md`.
- **Softened wall-clock time budgets into priority ordering.** `global-rules.md` no longer
  instructs the agent to self-time against a clock ("At 70 seconds…"); it now works checks
  in MUST RUN / HIGH VALUE / DROP FIRST priority order and cuts short only on a real signal
  (host time limit, user interrupt, repeated throttling). The per-check second figures in
  the orchestrator and pillar files are explicitly reframed as relative-effort hints, not
  deadlines. Behavior is more reliable — an agent can follow a priority list but cannot
  measure elapsed seconds.
- **Aligned the eval files with the standard AWS DevOps Agent skill-eval format:**
  `evals/evals.json` now uses the
  `{id, prompt, expected_output, files, assertions}` schema with the harness assertion DSL
  (`contains '...'`, `matches regex /.../`); added the `evals/files/connect-context.json`
  fixture; removed an earlier non-standard custom runner and eval README.
### Added
- Expanded README packaging section: explicit dev-only exclusions (`evals/`,
  `.skilleval.yaml`, `CHANGELOG.md`, git files) with a ready-to-run `zip` command, and a
  note on the platform-agnostic runtime package (`SKILL.md` + `references/`).
### Fixed
- Removed a stale reference to a deleted `evals/README.md` from the README packaging note.

## [1.1.0] - 2026-09-18
### Added
- Eval suite for automated quality signal, following the standard AWS DevOps Agent
  skill-eval file format:
  - `.skilleval.yaml` — audit config (ignore rules + documentation-domain allowlist).
  - `evals/eval_queries.json` — trigger evals as `{query, should_trigger}` (8 positive,
    5 negative) proving the skill activates on Connect ops-review / troubleshooting
    prompts and stays dormant on unrelated ones (including a review request for a
    different AWS service, to prove service specificity).
  - `evals/evals.json` — functional evals as `{id, prompt, expected_output, files,
    assertions}`, with assertions in the harness DSL (`contains '...'`,
    `contains 'X' or contains 'Y'`, `matches regex /.../`).
  - `evals/files/connect-context.json` — context fixture used by the smoke-test eval.
- `metadata` (version, aws-services, technical-domains) in `SKILL.md` frontmatter.
- This CHANGELOG.

### Notes
- No change to review or remediation behavior — this release is additive (testing +
  release hygiene) only.
- `.skilleval.yaml` and `evals/` are development-only; exclude them from the upload `.zip`.

## [1.0.0] - initial release
### Added
- Amazon Connect operations review across 7 Well-Architected pillars.
- Troubleshooting/remediation runbooks (categories A–H, Z) for 14 finding patterns,
  including call quality investigation and ACGR sync verification.
- Read-only-by-default posture with Two-Gate Confirmation Sequence for any write.
- Anti-hallucination grounding rules with mandatory source citation.
- Platform-agnostic design usable by any AI tool with AWS CLI/SDK access.
