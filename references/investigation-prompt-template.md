# Investigation Prompt Template

Use this template when creating a new Amazon Connect Ops Review investigation. Keeping the description short reduces input token cost on every step of the run — all procedure is enforced by the skill files, not the description.

The scope fields below are placeholders — leave them blank or omit them entirely if you prefer to provide scope interactively during Phase 0. The agent will ask for account, instance, and pillar selection regardless.

---

## Template

```
Run the amazon-connect-ops-review-troubleshooting-guide skill end-to-end.
Load and follow SKILL.md exactly — do not skip any phase or gate.
Do NOT begin any assessment until SKILL.md Phase 0 scoping gate is complete and confirmed by the customer.

Scope (optional — agent will confirm interactively during Phase 0):
- Account: {AWS_ACCOUNT_ID or "confirm interactively"}
- Instance: {INSTANCE_ALIAS_OR_ID or "confirm interactively"}
- Pillars: {PILLAR_SELECTION or "confirm interactively"}
- Report: HTML artifact
```

---

## Fill-in Guide

| Placeholder | What to put here | Example |
|---|---|---|
| `{AWS_ACCOUNT_ID}` | 12-digit AWS account ID — one or more, comma-separated | `111122223333` or `111122223333, 444455556666` |
| `{INSTANCE_ALIAS_OR_ID}` | Connect instance alias or full instance ID — one or more | `my-connect-prod` or leave blank for agent to discover all |
| `{PILLAR_SELECTION}` | Pillar name(s), numbers, or "All 7" | `Security, Reliability` or `All 7` |

All three fields are optional in the description. Phase 0 will confirm them interactively regardless — pre-filling just skips the initial question for that field.

---

## Why Keep the Description Short?

The investigation description is re-read as input on **every single step** of the run. A verbose description (800+ tokens) multiplied across 30 steps = 24,000+ wasted input tokens per run — spent re-reading procedure that the skill files already enforce.

The slim template (~80 tokens) carries only what the agent needs before loading the skill:
1. Which skill to load
2. The hard gate reminder (don't skip Phase 0)
3. Optional scope pre-fill

Everything else — phases, gates, pillar checks, report format — is enforced by `SKILL.md` and its reference files once loaded.

---

## Examples

### Fully Interactive (no pre-fill — agent asks everything)

```
Run the amazon-connect-ops-review-troubleshooting-guide skill end-to-end.
Load and follow SKILL.md exactly — do not skip any phase or gate.
Do NOT begin any assessment until SKILL.md Phase 0 scoping gate is complete and confirmed by the customer.

Report: HTML artifact
```

### Pre-filled — Single Account, All Pillars

```
Run the amazon-connect-ops-review-troubleshooting-guide skill end-to-end.
Load and follow SKILL.md exactly — do not skip any phase or gate.
Do NOT begin any assessment until SKILL.md Phase 0 scoping gate is complete and confirmed by the customer.

Scope:
- Account: 111122223333
- Instance: confirm interactively
- Pillars: All 7
- Report: HTML artifact
```

### Pre-filled — Multiple Accounts, Single Pillar

```
Run the amazon-connect-ops-review-troubleshooting-guide skill end-to-end.
Load and follow SKILL.md exactly — do not skip any phase or gate.
Do NOT begin any assessment until SKILL.md Phase 0 scoping gate is complete and confirmed by the customer.

Scope:
- Accounts: 111122223333, 444455556666
- Instance: confirm interactively
- Pillars: Security
- Report: HTML artifact
```
