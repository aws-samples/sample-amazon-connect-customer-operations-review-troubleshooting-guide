# Region Readiness Mode — Which AWS Region Can Run My Contact Center?

## Purpose

Amazon Connect features and telephony are Region-dependent. A feature, a phone number type, an outbound campaign destination, or a Global Resiliency pairing that works in one Region can be unavailable in another — and customers usually discover this during testing, after the build. This mode answers, **before anything is built**:

1. Which Amazon Connect home Region(s) can deliver *every* feature and telephony requirement the customer has?
2. For each candidate Region: what is supported, what is conditional (and on what), and what is blocked — each with a citation.
3. If no single Region fits: which multi-instance split covers everything, and which requirements cannot be met in any Region.

It needs **no AWS account access**. The agent collects requirements and explains the result, grounded in a cited AWS source — never from memory.

Finding IDs use the `REG-xxx` prefix (catalog at the end of this file).

---

## How this module works (read this first)

This module can get its answer from two places. **You never have to choose — the agent picks automatically, and tells you which it used.**

| | Live pages (default) | Bundled snapshot (fallback) |
|---|---|---|
| **What it is** | The agent fetches the actual AWS documentation page that decides your question, at the moment you ask. | A dated, offline copy of those same AWS pages (`references/region-data/connect-region-data.json`), scored by `scripts/region_readiness.py`. |
| **When it's used** | By default, on every question, whenever the agent has web access. | Automatically, only when a live fetch fails, times out, is blocked, or there's no web access. |
| **How current** | As current as AWS's live page right now. | As current as the day the snapshot was last built (shown as the "snapshot date" on every result). |
| **How you get it** | Just ask your question. No setup, no script. | Falls back on its own; or you can run the script yourself (see below). |

**The agent always states its source in one line** — e.g. "Source: live AWS Regions page, fetched <date>" or "Source: bundled snapshot (<date>) — live fetch unavailable." If you don't see a live-fetch line, the answer came from the snapshot.

### When should *you* run the script yourself?

For everyday questions you should **not** need to — just ask the agent and you get live data. Run `scripts/region_readiness.py` directly only when you specifically want the **offline snapshot** result, for example:

- You have **no internet access** (air-gapped / restricted network) and want a deterministic answer from the bundled copy.
- You want to **score many Regions and requirements at once** from a single `requirements.json` and get the full report/scorecard in one pass (the script is faster than asking question-by-question).
- You want a **repeatable, reviewable artifact** that won't change between runs (useful for a design doc or a ticket), independent of live-page edits.
- You're **testing or validating** the module and want the frozen baseline.

Important: the script reads the **snapshot only — it does not fetch live pages**, and it stamps every report with the snapshot date and age. If the snapshot is older than 90 days it flags it; refresh it with `scripts/build_region_data.py` (maintainer tool) or just ask the agent for a live-fetched answer instead.

### What a result does and does not promise

A ✅ / `SUPPORTED` means **the cited AWS document lists that item for that Region** — nothing more. It is **not** a guarantee that you can actually claim a number right now, that KYC documents will be approved, that porting slots are open, or that a Beta/Preview offering is production-ready. This module is for **self-preparation**; for any commitment, confirm via an AWS support case or your account team.

---

## When to Use

- "Which Region should I use for Amazon Connect?" / "Can I do X in Region Y?"
- Pre-sales, solution design, or kick-off — before any instance exists
- A customer lists countries for phone numbers, agents or outbound dialling, and needs to know where they can be served from
- Planning Global Resiliency (ACGR), outbound campaigns, Contact Lens, or AI agent features
- **Embedded in other modes:** during an Operations Review (see "Assess an existing instance" below), and in Troubleshooting when the symptom is "feature missing in the console", "can't claim a number", "campaign calls fail to a country", or "can't create a replica".

This mode is read-only and advisory. It never claims numbers, creates instances, or files support cases. A standalone run for a contact center that isn't live yet is exempt from the Call Quality Intake Gate (D0). Once the run assesses an existing instance, D0 applies as in every other pass.

---

## Step R0 — Get current data: live-first, snapshot as fallback

**Default behavior — the customer gets up-to-date data with zero effort on their part. They ask a question; you fetch what's needed. No script, no setup, no flags.**

The decision for any one Region question depends on only one or two AWS source pages (see the mapping below), not the whole catalog. So on every Region Readiness question:

1. **Fetch the decisive live page(s) first.** If you have web access, re-fetch the specific live AWS source(s) that decide *this* question (use the mapping in "Which page decides what" below) and answer from the live page. This is the DEFAULT path, not an optional extra — do it automatically without being asked, and without making the customer run anything.
2. **Fall back to the bundled snapshot automatically** if a fetch fails, times out, is blocked, or you have no web access. Read `references/region-data/connect-region-data.json` (or `references/region-readiness-matrix.md` if you can't execute code). The snapshot guarantees the customer always gets *an* answer, even offline.
3. **State the source in one line** so the customer always knows how fresh the answer is — e.g. "Source: live AWS Regions page, fetched 2026-10-06" or "Source: bundled snapshot (2026-10-06) — live fetch unavailable, re-check before committing." Keep it to a single line; do not turn it into a process the customer has to think about.
4. **Only when live and snapshot disagree** (AWS changed the page since the snapshot was built), prefer the live page, say so, and note the snapshot is now stale.

Never make the customer refresh the snapshot or run a script to get current data — that is maintainer work (see "Keeping the fallback fresh" below), not something an end user should ever touch.

### Which page decides what (fetch only what the question needs)

| Question is about | Fetch this live source | Snapshot key |
|---|---|---|
| Feature availability in a Region (Contact Lens, Q in Connect, campaigns feature, etc.) | https://docs.aws.amazon.com/connect/latest/adminguide/regions.html | `regions` |
| Outbound **campaign** destinations from a home Region | https://docs.aws.amazon.com/connect/latest/adminguide/regions.html (Outbound campaigns section) | `regions` |
| Phone number claimable Region / type / telephony capability | https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf + https://docs.aws.amazon.com/connect/latest/adminguide/phone-number-requirements.html | `telecoms_pdf`, `number_requirements` |
| Default outbound (non-campaign) country allow-list | https://docs.aws.amazon.com/connect/latest/adminguide/country-code-allow-list.html | `default_outbound` |
| Global Resiliency pairings / prerequisites | https://docs.aws.amazon.com/connect/latest/adminguide/create-replica-connect-instance.html + https://docs.aws.amazon.com/connect/latest/adminguide/connect-global-resiliency-requirements.html | `gr_replica`, `gr_requirements` |

Fetch only the row(s) the question touches — a single-page fetch is cheap; rebuilding the whole snapshot is not, and is never required to answer one question.

### Keeping the fallback fresh (maintainer, not customer)

The snapshot is only the offline fallback, so it must not rot — but keeping it fresh is a background chore the customer never performs:

- **Automate it.** Run `python3 scripts/build_region_data.py` on a schedule (monthly cron or CI job) and commit the regenerated `connect-region-data.json` + `region-readiness-matrix.md`. Review `parse_warnings` in the output before shipping a refresh.
- The snapshot carries a `generated` date; if it is **older than 90 days** and a live fetch was NOT possible for a given answer, tell the customer the answer came from a stale fallback and should be re-checked. If the live fetch succeeded, snapshot age doesn't matter for that answer.

> **One honesty note to pass to the customer when it matters:** live-fetch-first gives current data for everyday "is X available in Region Y" questions. It does NOT resolve cases where two AWS pages contradict each other (REG-011) or guarantee number stock — only an AWS case or a read-only check against their own instance (Step R4) does that. Surface this only for go-live / budget-committing decisions, not routine questions.

## Step R1 — Requirements intake

Ask for what you don't have. **Do not assume a requirement the customer has not stated** — omit it, and list it under "Not evaluated" in the report. Map answers to the input JSON (`python3 scripts/region_readiness.py --template` prints a blank file):

| Ask the customer | Input field | Notes |
|---|---|---|
| Must data stay in specific Regions or a jurisdiction? | `allowed_regions` | List of Region codes. Empty = any. Data residency is the customer's legal call. Record their constraint; don't interpret law. |
| Which Connect features will you use? | `features` | Keys from `--list-features` or aliases (`contact lens`, `q in connect`, `wfm`, `whatsapp`, `screen recording`…). Sub-features such as `conversational_analytics.real_time_call_analytics` are checked individually. |
| Which countries need phone numbers, of which type, and for what? | `phone_numbers[]` | `{country, type, needs}`. `type`: `DID`, `TOLL_FREE`, `UIFN`, `DID_MOBILE`, `SHARED`. `needs`: `inbound`, `national_outbound`, `international_outbound`, `porting`, `multi_carrier`, `custom_caller_id`, `campaigns`. |
| Which countries will agents call outbound (non-campaign)? | `outbound_destinations` | Checked against the per-Region default allow-list. |
| Which countries will outbound campaigns dial? | `campaign_destinations` | The most commonly missed constraint: campaign destinations are fixed per home Region. |
| Where are agents physically located? | `agent_countries` | Drives agent-location rules (Philippines, Vietnam), isolation guidance (India, South Korea, South Africa), and latency anchoring. |
| Do you need cross-Region DR (Global Resiliency)? | `global_resiliency` | Checks the fixed Region pairs and prerequisites. |
| Do you need FIPS endpoints? | `fips` | |
| Is AWS GovCloud (US) an option? | `include_govcloud` | Without it, GovCloud is listed but not recommended. |

Countries accept ISO-2 codes (`GB`) or names (`United Kingdom`, `UK`).

## Step R2 — Run the evaluation

```bash
python3 scripts/region_readiness.py --input requirements.json              # Markdown report
python3 scripts/region_readiness.py --input requirements.json --format json
python3 scripts/region_readiness.py --input requirements.json --top 5      # detail 5 Regions
python3 scripts/region_readiness.py --country "Japan"                      # one-country telephony lookup
python3 scripts/region_readiness.py --list-features                        # feature keys + Regions
```

Standard library only, no credentials needed. Note the script evaluates the **bundled snapshot** (the offline fallback), so when a live fetch succeeded in Step R0 for a decisive item, prefer the live value over the script's output for that item and say so. The script is still the fastest way to score many Regions/requirements at once and to produce the full report body.

**If you cannot execute code**, read `references/region-readiness-matrix.md` (human-readable copy of the same snapshot) and apply the rules in "Manual evaluation rules" below. State in the report that the evaluation was manual.

## Step R3 — Interpret the result

| Verdict | Meaning | What to tell the customer |
|---|---|---|
| ✅ `SUPPORTED` | The cited source lists it for that Region | Nothing to action beyond normal build |
| ⚠️ `CONDITIONAL` | Possible, with a prerequisite or caveat (documents, allow-list case, partner onboarding, Beta status, latency test, ACGR prerequisites) | List the exact prerequisite and its lead time |
| ❌ `NOT_SUPPORTED` | A cited source says it is unavailable in that Region | A blocker for that Region: pick another Region or a multi-instance split |
| ❔ `UNKNOWN` | No source covers it (e.g. Email channel is absent from the Regions page) | Confirm with AWS. Never fill the gap from memory. |

- **Region blockers vs design blockers.** A *design blocker* (marked "no Region choice fixes these") is unavailable in every Region — e.g. porting not offered for that country's number type, a Philippines/Vietnam number used by agents outside that country, Voice ID (end of support). Changing Region won't fix it; the requirement itself must change.
- **`REG-011` (sources disagree).** The bundled sources sometimes conflict: e.g. the phone-number requirements page excludes Africa (Cape Town) and GovCloud by default, while the Telecoms guide lists "All commercial regions". Present both quotes and tell the customer to confirm with AWS (Solutions Architect / Support) before committing. Do not pick a winner silently.
- **Latency (`REG-009`) is a heuristic.** The continent match only flags risk. The AWS guidance (500 ms network RTT recommended, 900 ms end-to-end upper bound) must be confirmed with the Connect Endpoint Test Utility from real agent locations.
- **Multi-Region plans.** When no single Region fits, the script proposes a primary Region plus additional instances that cover the remaining requirements. Each additional instance is a separate Connect instance with its own users, flows, reporting and quotas. Point out that cost, and the AWS guidance to prefer a single instance (or single ACGR pair) without compelling requirements (`curated.single_instance_default`).

## Step R4 — Optional live verification (only with account access and an instance)

These checks are read-only and run only if the customer offers credentials:

```bash
# Number stock actually available to this instance (country = ISO-2, type = DID | TOLL_FREE | UIFN | SHARED | THIRD_PARTY_DID | THIRD_PARTY_TF | SHORT_CODE)
aws connect search-available-phone-numbers --instance-id <instance-id> \
  --phone-number-country-code GB --phone-number-type DID --max-items 5 --region <region>

# Region of an existing instance and the numbers already claimed to it
aws connect describe-instance --instance-id <instance-id> --region <region>
aws connect list-phone-numbers-v2 --instance-id <instance-id> --region <region>
```

`search-available-phone-numbers` needs `--instance-id` or `--target-arn` (instance or traffic distribution group). An empty result means no stock was returned *right now*. That doesn't prove the country/type is unsupported — the documented route is an "Account and billing" support case to request numbers. Never call `claim-phone-number`; claiming is a billable write and falls under the Two-Gate Confirmation Sequence in `references/global-rules.md`.

## Step R5 — Report

Use the script's Markdown output as the body, or reproduce these sections:

1. **Recommendation** — the Region (or multi-instance plan), plus viable alternatives
2. **Design blockers** — requirements no Region satisfies
3. **Region scorecard** — every home Region ranked: Region blockers, design blockers, conditions
4. **Requirement × Region matrix** — top candidates
5. **Findings per candidate Region** — `REG-xxx`, requirement, detail, source URL
6. **Prerequisites & lead times** — KYC documents, porting windows, allow-list cases, partner onboarding, ACGR onboarding (Enterprise Support / SAML)
7. **Not evaluated** — anything the customer didn't specify, plus language/locale support (see `references/region-data` → `unlisted_features.languages`)
8. **Data provenance** — snapshot date, Telecoms guide "Last updated" date, and the statement that this is a point-in-time copy to re-check before committing

---

## Assess an existing instance (Operations Review / Troubleshooting hook)

When the orchestrator has already discovered an instance (Phase 0), build the requirements from **retrieved** configuration and evaluate with `allowed_regions = [<instance region>]`:

| Retrieved data (Phase 0 / pillar calls) | Requirement |
|---|---|
| `list-phone-numbers` / `list-phone-numbers-v2` → `PhoneNumberCountryCode`, `PhoneNumberType` | `phone_numbers[]` (`needs: ["inbound"]`) |
| `describe-instance-attribute --attribute-type CONTACT_LENS` = `true` | `features: conversational_analytics` |
| `describe-instance-attribute --attribute-type HIGH_VOLUME_OUTBOUND` = `true` | `features: outbound_campaigns` |
| `list-integration-associations` → `CASES_DOMAIN` | `features: cases` |
| `list-integration-associations` → `WISDOM_ASSISTANT` | `features: agent_assist` |
| `list-traffic-distribution-groups` returns a group | `global_resiliency: true` |

Report any non-`SUPPORTED` result as a `REG-xxx` finding under Pillar 3 (Reliability) for `REG-008`, and Pillar 1 (Operational Excellence) otherwise. Route it to Runbook Category **R** (Region Readiness): Diagnose = re-run the script for the instance Region and cite the source. Verify = Step R4 live check where applicable. Fix = proposal only (e.g. raise an allow-list case, move the workload to an instance in a supported Region).

Do not infer customer intent (campaign destinations, agent locations) from an existing instance — ask, or mark it "Not evaluated".

---

## Manual evaluation rules (no code execution)

Apply these in order using `references/region-readiness-matrix.md`:

1. **Feature** — ✅ if the Region column shows ✅ in §2 (or the sub-feature table), else ❌ `REG-001`. Voice ID is ❌ everywhere (end of support 2026-05-20).
2. **Global Resiliency** — only the pairs in §1 (`us-east-1`↔`us-west-2`, `eu-central-1`↔`eu-west-2`, `ap-northeast-1`→`ap-northeast-3`). Any other source Region ❌ `REG-008`. Always list the prerequisites (Enterprise Support or Unified Operations, SAML 2.0 instance, numbers ported).
3. **Phone number** — find the country/type row in §5. Claimable-in = "All commercial" (every home Region except GovCloud), "All regions", or the listed codes. Otherwise ❌ `REG-002`. A ❌ in a column the customer needs → design blocker `REG-003`. 🟡 → ⚠️ `REG-003`. Status other than GA → ⚠️ `REG-004`. Then check §6: a Region-restricted row or an agent-location rule overrides, and the default rule (excludes Cape Town and GovCloud) conflicting with §5 → ⚠️ `REG-011`.
4. **Outbound (non-campaign)** — destination in §4 for that Region → ✅, else ⚠️ `REG-006` (allow-list support case; default-deny).
5. **Campaign destination** — must appear for that Region in §3 in both columns → ✅. In only one column → ⚠️ `REG-011`. In neither → ❌ `REG-007`.
6. **Agents** in India, South Korea or South Africa → ⚠️ `REG-010` (AWS: "Isolation is required for agents in India, South Korea, and South Africa.").
7. **Latency** — if neither agents nor numbers are on the Region's continent → ⚠️ `REG-009`, and require an Endpoint Test Utility measurement.

---

## Finding catalog

| ID | Title | Typical severity | Typical resolution |
|---|---|---|---|
| REG-001 | Feature not available in Region | HIGH if the feature is in scope | Choose a Region that lists it, or descope |
| REG-002 | Number country/type not claimable in Region | HIGH | Home Region that can claim it, or a second instance |
| REG-003 | Telephony capability gap (outbound / porting / multi-carrier / caller ID) | HIGH (design) / MEDIUM (yellow tick) | Change number type or design; confirm use case with AWS |
| REG-004 | Number offering not GA | MEDIUM | Request early access; do not plan production traffic on Beta/Test |
| REG-005 | KYC documents / agent-location rule | MEDIUM (lead time) / HIGH (agent-location breach) | Start document collection early; restrict agent IPs where required |
| REG-006 | Outbound destination not in default allow-list | MEDIUM | "Country Allowlisting for Outbound Calls" support case before go-live |
| REG-007 | Campaign destination not dialable from Region | HIGH | Home Region that serves that destination, or a second instance |
| REG-008 | Global Resiliency unavailable / pairing / prerequisites | HIGH if DR is required | Use a supported pair; meet support-plan and SAML prerequisites |
| REG-009 | Latency anchoring risk | MEDIUM | Measure with the Endpoint Test Utility; move instance near agents or numbers |
| REG-010 | Agent isolation guidance (IN / KR / ZA) | MEDIUM | Dedicated instance for those agents |
| REG-011 | AWS sources disagree | MEDIUM | Confirm with AWS before committing |
| REG-012 | Excluded by residency / allowed-Region constraint | INFO | — |
| REG-013 | Not evaluated (no Region data) | INFO | Confirm with AWS |

---

## Region gotchas (each sourced in the snapshot)

- Outbound campaign destinations are fixed per home Region. Example from the Regions page: "you can't make campaign calls from Europe (London) to US phone numbers".
- Global Resiliency replicas exist only for three pairings. Osaka (`ap-northeast-3`) is replica-only, not a home Region.
- Outbound calling is default-deny. Each Region has a short default country list (e.g. Europe (Frankfurt)/(London): United Kingdom, Italy, France, Ireland, United States — **not** Germany). Other countries need an allow-list case. UK `+447` and Japan `+8170/+8180/+8190` mobile prefixes may need a quota request.
- Some countries' numbers can be claimed only in specific Regions: South Africa numbers in Africa (Cape Town); Japan geographic `+81 3`/`+81 6` in Asia Pacific (Tokyo); Norway in Europe (Frankfurt)/(London) (all per both the Telecoms guide and the phone-number requirements page); Philippines DID/toll-free in Asia Pacific (Singapore) (Telecoms guide).
- Philippines and Vietnam numbers require the agents to be physically located in that country.
- Generative AI conversational-analytics features vary by Region. Africa (Cape Town) and GovCloud lack several of them; Asia Pacific (Seoul) lacks generative AI performance evaluations; Asia Pacific (Singapore) lacks generative AI contact categorization.
- Agent assist (Amazon Q in Connect), agentic voice, Agentic CX Designer, External Tool and live media streaming are not listed for Africa (Cape Town) or GovCloud.
- Porting lead times are long: AWS advises opening porting requests "as far in advance of your pending go-live date as possible". South Korea ordering/porting takes longer than most countries.

---

## Sources (bundled snapshot)

| Key | Source |
|---|---|
| `regions` | https://docs.aws.amazon.com/connect/latest/adminguide/regions.html |
| `telecoms_pdf` | https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf |
| `number_requirements` | https://docs.aws.amazon.com/connect/latest/adminguide/phone-number-requirements.html |
| `default_outbound` | https://docs.aws.amazon.com/connect/latest/adminguide/country-code-allow-list.html |
| `gr_replica` / `gr_requirements` | https://docs.aws.amazon.com/connect/latest/adminguide/create-replica-connect-instance.html · https://docs.aws.amazon.com/connect/latest/adminguide/connect-global-resiliency-requirements.html |
| `low_latency` | https://docs.aws.amazon.com/connect/latest/adminguide/low-latency-design.html |
| `region_selection` | https://docs.aws.amazon.com/connect/latest/adminguide/operational-excellence.html ("Region selection", in the Architectural guidance section) |
| `single_vs_multi_instance` | https://docs.aws.amazon.com/connect/latest/adminguide/single-instance-multiple-instances.html |
| `supported_languages` | https://docs.aws.amazon.com/connect/latest/adminguide/supported-languages.html |
| `endpoint_test_utility` | https://docs.aws.amazon.com/connect/latest/adminguide/check-connectivity-tool.html |
| `pricing` | https://aws.amazon.com/connect/pricing/ |
