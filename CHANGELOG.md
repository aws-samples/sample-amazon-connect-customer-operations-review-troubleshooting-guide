# Changelog

All notable changes to this skill are documented here. Versions are tagged in git
(`v1.0.0`, `v1.1.0`, …) so any release can be checked out or reverted directly.

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
