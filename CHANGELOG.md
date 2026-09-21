# Changelog

All notable changes to this skill are documented here. Versions are tagged in git
(`v1.0.0`, `v1.1.0`, …) so any release can be checked out or reverted directly.

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
