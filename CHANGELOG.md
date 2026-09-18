# Changelog

All notable changes to this skill are documented here. Versions are tagged in git
(`v1.0.0`, `v1.1.0`, …) so any release can be checked out or reverted directly.

## [1.1.0] - 2026-09-18
### Added
- Eval suite for automated quality signal:
  - `.skilleval.yaml` — audit config (ignore rules + documentation-domain allowlist).
  - `evals/eval_queries.json` — trigger evals (8 positive, 5 negative) proving the skill
    activates on Connect ops-review / troubleshooting prompts and stays dormant on
    unrelated ones (including an Amazon Bedrock review, to prove service specificity).
  - `evals/evals.json` — functional evals asserting the skill's own contract: read-only
    by default, Two-Gate Confirmation before any write, grounded/cited findings, and the
    mandatory D0 call-quality intake.
  - `evals/README.md` — how the three eval layers work and how to run them.
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
