# Evals

Automated tests for the `amazon-connect-ops-review-troubleshooting-guide` skill.
These files are **development-only** — exclude them (and `.skilleval.yaml`) from the
upload `.zip`.

## Files

| File | Layer | Question it answers |
|---|---|---|
| `../.skilleval.yaml` | Audit | Is the skill file itself well-formed and free of unsafe external links? (static lint, no model run) |
| `eval_queries.json` | Trigger | Does the skill activate on Connect ops-review / troubleshooting prompts and stay dormant on unrelated ones? |
| `evals.json` | Functional | When the skill runs, does the output honor its own contract — read-only by default, two-gate before writes, grounded/cited findings, mandatory call-quality intake? |

## Trigger evals (`eval_queries.json`)

Each entry is `{query, should_trigger}`. A harness presents the query to the model with
this skill available and checks whether the skill activated against `should_trigger`.
Positive cases come straight from `SKILL.md` "When to Use"; negatives (a Bedrock review,
a weather question, a Chime question) prove the `description` frontmatter is specific
enough not to over-fire.

## Functional evals (`evals.json`)

Each entry has a `query` and a list of `assertions`. Assertion `method` values:

- `contains` / `contains_any` — substring match (deterministic)
- `not_contains_any` — must not contain any listed substring (deterministic)
- `regex` / `not_regex` — pattern match (deterministic)
- `llm` — a grader model judges a fuzzy criterion (probabilistic; add as needed)

Assertions transcribe rules already written in prose in `SKILL.md` /
`references/global-rules.md` (read-only default, Two-Gate Confirmation, source citations,
the mandatory D0 call-quality ask) into machine-checkable form, so a future edit can't
silently break them.

## Running

These files follow the AWS DevOps Agent skill-eval format. Run them with that harness, or
with any runner that (1) loads `SKILL.md`, (2) sends each query to a model, and (3)
evaluates the assertions above. The file format is the portable, reusable part.
