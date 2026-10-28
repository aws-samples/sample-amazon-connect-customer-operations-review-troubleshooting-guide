# Cost Optimization Mode — Where Can We Cut the Amazon Connect Bill?

## Purpose

Pillar 5 of the Review module flags cost issues as part of a full Well-Architected audit. This mode goes deeper: its whole job is to **size, rank, and sequence savings**. It decomposes the Connect bill, evaluates every lever in the catalog below, and returns a ranked list of opportunities — each with an estimated monthly dollar impact, the evidence behind it, an effort level, and a risk note.

Finding IDs use the `CSO-xxx` prefix (catalog at the end of this file). They are distinct from the Review module's `COST-xxx` pillar findings; where both describe the same issue, cite both.

> **Naming:** AWS documentation and pricing now call the product **Amazon Connect Customer**, with plans such as the Connect Customer plan and Customer Basic. This file uses "Amazon Connect" / "Connect" as shorthand; API and usage-type names are unchanged. "Wisdom" is the retired name of Amazon Q in Connect.

This mode is **read-only and advisory**. It never releases a phone number, disables a feature, or changes a configuration. Any change follows the Two-Gate Confirmation Sequence in `references/global-rules.md` — and phone-number releases are effectively irreversible (see CSO-001).

---

## When to Use

- "Reduce / cut / optimize our Amazon Connect cost."
- "Why is my Connect bill increasing?" / "Investigate a Connect spend anomaly."
- "Find unused phone numbers." / "Is Contact Lens worth the cost?"
- "Optimize our telephony mix (toll-free vs. DID, outbound destinations)."

For a full Well-Architected audit, use the Review module (option 1) instead. For a one-off cost spike on an instance already under review, Runbook Category G2 (`COST-003`) is the shorter path.

---

## Step C0 — Prerequisites and run cost

Read-only IAM actions this mode uses: `ce:GetCostAndUsage`, `ce:GetCostForecast`, `ce:GetAnomalies`, `connect:ListInstances`, `connect:DescribeInstance`, `connect:DescribeInstanceAttribute`, `connect:ListInstanceStorageConfigs`, `connect:ListPhoneNumbersV2`, `connect:DescribePhoneNumber`, `connect:ListFlowAssociations`, `connect:GetMetricDataV2`, `connect:SearchContacts`, `connect:DescribeContact`, `connect:ListRules`, `connect:ListIntegrationAssociations`, `cloudtrail:LookupEvents`, `cloudwatch:GetMetricData`.

**Read-only is not free:** each Cost Explorer request costs about $0.01. Collect the baseline once and reuse it; do not re-query per lever.

Cost Explorer data is **account-wide** (management/payer account for consolidated billing), not per instance. If `ce:*` returns `AccessDeniedException`, every spend-based lever is `NOT ASSESSED — ce:GetCostAndUsage denied`; inventory-based levers (CSO-001–003, CSO-015) still run, sized with pricing-page rates and labelled as estimates.

---

## Step C1 — Scope

| Input | How to resolve |
|---|---|
| Account | Provided, or `aws sts get-caller-identity` |
| Instance(s) | Provided, or discover per `references/connect-ops-review-orchestrator.md` and let the customer pick; analyze one at a time |
| Region(s) | Instance inventory and metrics are per Region; Cost Explorer spend is account-wide — label spend that cannot be tied to a scoped instance as such |
| Cost window | Default: last 3 complete calendar months for the breakdown, last 30 days for usage-type detail |
| Pricing plan | **Ask:** Connect Customer plan or Customer Basic? (gates CSO-010–014) |
| Material-dollar floor | **Ask:** the smallest monthly amount the customer cares about (filters anomalies and tiny levers) |

**Coverage rule:** if any call returns a `NextToken` you didn't follow, a throttling error, or an empty result where data was expected, report the covered scope and mark dependent levers `Data unavailable — [reason]`. Never size a saving, or claim "no waste", from partial or empty data.

---

## Step C2 — Spend baseline

Size and decompose the bill first, so every lever can be expressed as a fraction of a real number.

```bash
# Monthly spend by service (Connect vs. telecom), last 3 complete months (end date exclusive)
aws ce get-cost-and-usage --time-period Start=<YYYY-MM-01>,End=<YYYY-MM-01> \
  --granularity MONTHLY --metrics UnblendedCost UsageQuantity \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Connect","Contact Center Telecommunications (service sold by AMCS, LLC)"]}}' \
  --group-by Type=DIMENSION,Key=SERVICE

# Same window grouped by usage type (drives the bucket decomposition below)
aws ce get-cost-and-usage --time-period Start=<start>,End=<end> --granularity MONTHLY \
  --metrics UnblendedCost UsageQuantity \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Connect","Contact Center Telecommunications (service sold by AMCS, LLC)"]}}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE

# Per-instance attribution (needs the cost-allocation tag activated — see CSO-019)
aws ce get-cost-and-usage --time-period Start=<start>,End=<end> --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=TAG,Key=aws:connect:instanceId \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Connect","Contact Center Telecommunications (service sold by AMCS, LLC)"]}}'

# Forecast (needs roughly 14+ days of history)
aws ce get-cost-forecast --time-period Start=<tomorrow>,End=<first day of month after next> \
  --granularity MONTHLY --metric UNBLENDED_COST \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Connect","Contact Center Telecommunications (service sold by AMCS, LLC)"]}}'

# AWS Cost Anomaly Detection findings (authoritative anomaly source; empty if no monitor exists)
aws ce get-anomalies --date-interval StartDate=<90 days ago>,EndDate=<today>
```

Exclude **Amazon Connect Voice ID** usage types (end of support) from totals. Decompose the usage types into these buckets, recording each as an absolute monthly figure and a % of total. Match on the usage-type string returned — **list any usage type you cannot place under "Uncategorized", verbatim; never guess its bucket**:

| Bucket | Usage-type hints (verify against the returned strings) |
|---|---|
| Voice / telephony | inbound / outbound telecom minutes, `voice` service minutes, DID vs. toll-free inbound minutes |
| Phone numbers | DID per-day fees vs. toll-free per-day fees |
| Contact Lens / conversational analytics | `ContactLens`, analytics |
| Chat / tasks / email | `chat`, `task`, `email` |
| Outbound campaigns | `campaign`, `outbound` (campaign) |
| Other features | Q in Connect, Customer Profiles, Cases, forecasting / scheduling, evaluations, screen recording |
| Uncategorized | everything else — list verbatim |

> Cost Explorer is **usage-type / tag** granularity, not line-item. Do not claim CUR/Athena precision.

**Outside the service filter:** SMS billed by AWS End User Messaging, and adjacent costs the contact center drives (Lambda, S3 recordings, Kinesis, Lex, CloudWatch Logs). Say so; never report the Connect total as the full contact-center cost.

---

## Step C3 — Evaluate the levers

Evaluate every lever in the catalog against this account's data. **Pricing basics** (always confirm current rates on the [pricing page](https://aws.amazon.com/connect/pricing/)): phone numbers are billed **per day** (e.g. a US DID ≈ $0.030/day) — never multiply a "monthly number rate". There is **no instance, seat, or baseline fee**. Derive actual per-day rates from the phone-number usage types (cost ÷ quantity); never insert a made-up `$X`.

### C3.1 Phone-number inventory (CSO-001–003)

```bash
aws connect list-phone-numbers-v2 --target-arn <instance-arn> --region <region>
aws connect describe-phone-number --phone-number-id <id> --region <region>   # Status, Type, Description
aws connect list-flow-associations --instance-id <instance-id> --resource-type VOICE_PHONE_NUMBER --region <region>
```

- A number **absent from `list-flow-associations`** has no inbound flow → candidate for CSO-002. If the association call is denied or paginates incompletely, CSO-002 is `Data unavailable` — never report numbers as unrouted from an incomplete scan.
- **Per-number call volume is not directly available.** `search-contacts` has no dialled-number filter. Use it to bound the question: total inbound voice contacts for 30 days (if < 10, every number is low-volume), and `describe-contact` on a small sample of INBOUND contacts to see which `SystemEndpoint` numbers *do* get traffic. Per-number volume otherwise comes from the customer's contact-record (CTR) data. Without it, the < 10 calls/month test is `Data unavailable`.
- Numbers claimed to a **traffic distribution group** are not in the instance list — ask. **Exclude** shared-trunking / BYOC numbers (no Connect number charge) and DR / TDG failover numbers before counting a saving.

### C3.2 Telephony mix (CSO-004–009)

Use the usage-type breakdown from C2 plus historical metrics:

```bash
aws connect get-metric-data-v2 --resource-arn <instance-arn> \
  --start-time <30d ago> --end-time <now> \
  --interval '{"IntervalPeriod":"WEEK"}' \
  --filters '[{"FilterKey":"CHANNEL","FilterValues":["VOICE"]}]' \
  --groupings '["QUEUE"]' \
  --metrics '[{"Name":"AVG_HANDLE_TIME"},{"Name":"AVG_QUEUE_ANSWER_TIME"},{"Name":"CONTACTS_HANDLED"},{"Name":"CONTACTS_QUEUED"}]' \
  --region <region>
```

Each GetMetricDataV2 request must cover < 35 days at WEEK/DAY/TOTAL intervals. Voice is billed for time in the flow, in queue and with the agent — so long queue and handle times multiply cost.

### C3.3 Pricing plan gate (CSO-010) — run before any feature lever

On the current **Connect Customer plan**, AI / analytics features (conversational analytics, Q in Connect, forecasting and scheduling, evaluations, screen recording) are **included in the channel rate** — disabling them saves nothing. Per-feature charges apply only to **Customer Basic**. No API returns the plan: take the customer's answer from C1, or infer it carefully (separately billed analytics / forecasting usage types suggest per-feature billing). **If the plan is undetermined, CSO-011–014 are all `Data unavailable — pricing plan not confirmed`.**

### C3.4 Feature ROI (CSO-011–014)

```bash
aws connect describe-instance-attribute --instance-id <id> --attribute-type CONTACT_LENS --region <region>
aws connect list-rules --instance-id <id> --publish-status PUBLISHED --event-source-name OnPostCallAnalysisAvailable --region <region>
aws connect list-rules --instance-id <id> --publish-status PUBLISHED --event-source-name OnRealTimeCallAnalysisAvailable --region <region>
aws connect list-integration-associations --instance-id <id> --region <region>   # WISDOM_ASSISTANT, CASES_DOMAIN, CONNECT_CAMPAIGNS
```

- There is **no real-time vs. post-call analytics price difference** — never recommend "downgrade to post-call" to save money. Analytics is enabled per contact in the flows' **Set recording and analytics behavior** block — read the relevant flow JSON (`describe-contact-flow`) to see where.
- Whether dashboards / rules actually consume analytics output, campaign completion rates, and Q in Connect usage are **customer-supplied**; without them the lever is `Data unavailable`.

### C3.5 Instances and storage (CSO-015–016)

```bash
aws connect get-metric-data-v2 --resource-arn <instance-arn> --start-time <30d ago> --end-time <now> \
  --interval '{"IntervalPeriod":"TOTAL"}' --filters '[{"FilterKey":"CHANNEL","FilterValues":["VOICE","CHAT","TASK","EMAIL"]}]' \
  --metrics '[{"Name":"CONTACTS_HANDLED"}]' --region <region>
aws connect list-instance-storage-configs --instance-id <id> --resource-type CALL_RECORDINGS --region <region>
aws s3api get-bucket-lifecycle-configuration --bucket <recording-bucket>
```

If `s3:GetBucketLifecycleConfiguration` is denied, CSO-016 is `NOT ASSESSED`; never read a denial as "no lifecycle policy".

### C3.6 Spend hygiene (CSO-017–019)

- **Anomalies:** use `ce get-anomalies` findings first. If no Cost Anomaly Detection monitor exists, compute month-over-month change from C2 (> 20% without known growth → investigate) and compare daily spend only **like-for-like weekday** (a weekday-heavy center otherwise shows false spikes). For each material anomaly, do a driver analysis:

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time <spike - 7d> --end-time <spike> --region <region>
aws cloudwatch get-metric-data --metric-data-queries '[{"Id":"cc","MetricStat":{"Metric":{"Namespace":"AWS/Connect","MetricName":"ConcurrentCalls","Dimensions":[{"Name":"InstanceId","Value":"<id>"},{"Name":"MetricGroup","Value":"VoiceCalls"}]},"Period":3600,"Stat":"Maximum"}}]' \
  --start-time <window start> --end-time <window end> --region <region>
```

AWS/Connect CloudWatch metrics are retained only ~2 weeks. An outbound spike to unusual or high-cost destinations is a possible **toll-fraud / IRSF** signal → CRITICAL; destination detail comes from the customer.

---

## Step C4 — Quantify and rank

For every opportunity, state the **formula and its assumption** (e.g. "12 toll-free numbers × <per-day rate from the toll-free usage type> × 30 days"). Where a rate is unknown, give a range or a % of the relevant bucket and label it an estimate — never invent a rate.

Rank by **impact × effort** (largest, cheapest first). Severity is relative to total monthly Connect spend (guidance — adjust to the customer):

| Severity | Definition |
|---|---|
| 🔴 CRITICAL | Runaway or anomalous spend inflating the bill now (e.g. suspected toll fraud) |
| 🟠 HIGH | ≥ ~10% of monthly spend, high confidence, low effort |
| 🟡 MEDIUM | ~2–10%, needs a config or process change |
| 🟢 LOW | < ~2%, housekeeping |
| INFO | Observation, no action required |

Add a **risk / irreversibility** note to every row. Number releases (CSO-001–003) and feature removals need customer sign-off regardless of dollar size.

---

## Step C5 — Report

Satisfy the Report Generation Gate in `references/global-rules.md` first. Then produce:

1. **Executive Summary** — total identified monthly savings (low–high range), current monthly spend and forecast trajectory, top 3 opportunities by dollar impact
2. **Scoping Summary** — account, instance(s), cost window, pricing plan (and its basis), material-dollar floor
3. **Spend Breakdown** — `| Bucket | Monthly $ | % of total | Trend |`, plus the verbatim Uncategorized list
4. **Ranked Opportunities** — `| # | CSO-ID | Opportunity | Evidence (API, resource, timestamp) | Est. monthly impact (formula) | Effort | Severity | Risk |`
5. **Anomalies & Forecast** — `| Signal | Detail | Impact |`, and the anomaly source used (Cost Anomaly Detection or month-over-month fallback)
6. **Not assessed** — every lever marked `Data unavailable` / `NOT ASSESSED`, with the reason and what would unblock it
7. **Phased Action Plan** — Immediate (quick wins) / This Sprint (config changes) / Next Sprint / Backlog (telephony-mix or architecture changes)

Every action is a proposal only — none is applied by producing the report. Recommend AWS Cost Anomaly Detection and AWS Budgets for ongoing alerting.

---

## Finding catalog

| ID | Lever | Detection signal | Savings mechanism | Effort |
|---|---|---|---|---|
| CSO-001 | Idle toll-free numbers | Toll-free numbers from `list-phone-numbers-v2` + toll-free per-day usage type + **customer-supplied** per-number volume (< 10 calls/month, guidance) | Release → removes the toll-free daily charge (`count × daily rate × days`) | Low |
| CSO-002 | DID numbers with no routing | Number absent from `list-flow-associations` (complete scan only) | Release → removes the DID daily charge | Low |
| CSO-003 | Unreleased test / vanity numbers | `describe-phone-number` `PhoneNumberDescription` / status + zero traffic (customer-supplied) | Release | Low |
| CSO-004 | Toll-free where a DID suffices | Toll-free vs. DID inbound minutes in the usage-type breakdown; internal/regional traffic is **customer-supplied** | Net saving = (TF daily − DID daily) × days + TF per-minute premium × minutes; callers need the new number | Medium |
| CSO-005 | Outbound destination mix | High outbound telecom spend | Review destination mix (country, mobile vs. landline), caller ID and dialling patterns — carriers are not customer-selectable except via shared trunking | Medium |
| CSO-006 | Hold / handle time inflating per-minute cost | `AVG_HANDLE_TIME`, `AVG_QUEUE_ANSWER_TIME` high (GetMetricDataV2) | Reduce billed minutes via routing, staffing, self-service | High |
| CSO-007 | Queue time billed while callers wait | High `AVG_QUEUE_ANSWER_TIME` × `CONTACTS_QUEUED` | Offer queued callback | Medium |
| CSO-008 | Low self-service containment | Customer-supplied IVR / bot containment data | Improve IVR / bot containment | High |
| CSO-009 | External transfers | Customer-supplied transfer data (external transfers keep two billed legs up) | Prefer internal transfers | Medium |
| CSO-010 | Pricing plan undetermined | No customer answer and no conclusive usage types | Confirm the plan — gates CSO-011–014 | Low |
| CSO-011 | Conversational analytics enabled but unused (Customer Basic) | `CONTACT_LENS` attribute + analytics spend + flows' recording/analytics block + no consuming rules (`list-rules`) / dashboards (customer-supplied) | Disable analytics on flows that don't need it | Low |
| CSO-012 | Low-completion outbound campaigns | Campaign spend + customer-supplied completion rates | Pause or re-target | Medium |
| CSO-013 | Low-usage Amazon Q in Connect | `WISDOM_ASSISTANT` integration + spend + customer-supplied usage | Disable or scope | Low |
| CSO-014 | Unused per-agent / per-unit items (Customer Basic, or items priced separately such as Cases or external voice connectors) | Matching usage types + customer confirmation | Remove unused seats / connectors | Low–Medium |
| CSO-015 | Idle instance | `CONTACTS_HANDLED` = 0 over 30 days, all channels (complete data only). No instance fee — the cost is its numbers' per-day charges, any per-day/per-agent items, and storage | Release numbers, consolidate or decommission (customer decision) | Medium |
| CSO-016 | Recording storage not tiered | Recording bucket from `list-instance-storage-configs` + lifecycle config | Lifecycle to Intelligent-Tiering / Standard-IA; expire at end of retention (retention period is a **must-ask** — never propose an expiry without it). Glacier tiers only for recordings that won't need routine playback (restore required) | Low |
| CSO-017 | Spend anomaly | `ce get-anomalies`, or > 20% month-over-month without known growth | Driver analysis (CloudTrail changes, volume, usage types); possible toll fraud → CRITICAL | Varies |
| CSO-018 | Forecast overrun | `ce get-cost-forecast` above the customer's budget | Apply the levers above pre-emptively; set AWS Budgets | Varies |
| CSO-019 | No per-instance / per-number attribution | Tag-grouped query returns only the empty tag value — `aws:connect:instanceId` / `aws:connect:systemEndpoint` not activated | Activate in Billing → Cost allocation tags (applies going forward; a management-account user can request a backfill of up to 12 months) | Low |

> **Phone-number release warning (CSO-001–003):** a released number enters a **cooldown of up to 180 days** before anyone can claim it again, and claim + release is capped at **200% of the phone-number quota per rolling 180 days** (after that, claims are blocked until a support case). Treat release as irreversible for planning, recommend it only for numbers the customer confirms are unused, and never perform it outside the Two-Gate sequence.

---

## Sources

- [Amazon Connect pricing](https://aws.amazon.com/connect/pricing/)
- [Managing phone numbers](https://docs.aws.amazon.com/connect/latest/adminguide/contact-center-phone-number.html)
- [Contact Lens](https://docs.aws.amazon.com/connect/latest/adminguide/contact-lens.html)
- [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
- [AWS Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html)
