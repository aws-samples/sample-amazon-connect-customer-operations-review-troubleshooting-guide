# Scoping Inputs — Pre-Assessment Checklist

This file defines the inputs an operations review or troubleshooting pass needs before running pillar assessments or runbooks. It replaces any platform-specific gating mechanism — a calling tool can resolve these inputs however fits its own interaction model (asking a human, taking them as parameters, reading them from a ticket, etc.). None of the steps below require a specific chat harness or task/investigation history lookup.

---

## Required Inputs

### 1. AWS Account(s)

- If not provided, resolve the currently authenticated account:
```bash
aws sts get-caller-identity
```
- Multiple accounts are supported — resolve or collect all relevant account IDs before proceeding.

### 2. Region(s) and Instance Discovery

Once account(s) are known, discover Connect instances. Scan regions in parallel where possible:

```
us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1,
ap-southeast-2, ap-northeast-1, ca-central-1, af-south-1,
ap-northeast-2, eu-west-2, us-gov-west-1
```

Per region:
```bash
aws connect list-instances --region <region> --max-results 10
# Empty response -> skip region
# Results -> for each instance:
aws connect describe-instance --instance-id <instance-id> --region <region>
```

Present discovered instances as raw facts — do not label or classify them as Production/Dev/Test at this stage (classification happens in Step 2 of the main workflow, based on evidence, not guesswork):

```
## Instances Found: {n} across {accounts} account(s), {regions} region(s)

| # | Account | Instance ID | Alias | Region | Status | Identity Type | Created |
|---|---------|-------------|-------|--------|--------|---------------|---------|
| 1 | 111122223333 | i-xxxxxxxx | alias-1 | us-east-1 | ACTIVE | SAML | 2022-03-10 |
```

If a caller/human needs to choose which instances to include, offer the list; otherwise proceed with all discovered instances that match the given scope.

### 3. Pillar Selection (Operations Review only)

Resolve which Well-Architected pillars to run:

1. Operational Excellence — logging, alarms, operational visibility
2. Security — approved origins, encryption, KMS, IAM
3. Reliability — DR, Traffic Distribution Groups, ACGR sync
4. Performance Efficiency — Lex bot config, Contact Lens rules, WebRTC
5. Cost Optimization — S3 lifecycle, cost spike analysis
6. Sustainability — multi-instance consolidation opportunities
7. Generative AI — AI guardrails, Q in Connect, Wisdom

If unspecified, default to running all 7 for a full review. Only load pillar reference files for the selected pillars.

### 4. Troubleshooting-Only Runs

If the request is symptom- or finding-ID-based troubleshooting rather than a full review, skip pillar selection entirely — go directly to the Runbook Category Index in `SKILL.md` and jump to the matching reference file.

---

## Scoping Summary

Before starting assessments, produce a short summary of what will run — useful for review, logging, or handoff, but not a blocking requirement:

```
## Scoping Summary

- Account(s): {account IDs}
- Instances: {instance aliases and IDs}
- Pillars selected: {pillar list or "All 7"} (n/a for troubleshooting-only runs)
```
