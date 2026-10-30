# Peak Readiness Mode — Can Our Contact Center Absorb the Event?

## Purpose

A **point-in-time go / no-go gate** for an upcoming peak — a seasonal spike, marketing campaign, product launch, Black Friday — or a sustained volume increase. It projects recent peaks against the event target, checks capacity / quota headroom, IVR dependency headroom, resiliency, monitoring and staffing / routing readiness, records customer attestations for what no API can see, and returns **READY / READY WITH ACTIONS / NOT READY** with a lead-time-ordered action plan.

This is not a broad audit (use the Review module for that). Finding IDs use the `PEAK-xxx` prefix (catalog at the end of this file).

> **Naming:** AWS documentation now calls the product **Amazon Connect Customer**. This file uses "Amazon Connect" / "Connect" as shorthand; API, metric and quota names are unchanged.

This mode is **read-only**. It never requests a quota increase, changes a configuration, or load-tests — it recommends the customer do so.

---

## When to Use

- "Are we ready for Black Friday call volume?" / "Can Connect handle 2x our normal peak?"
- "Pre-event / go-no-go readiness check for our campaign or launch."
- "Do we need to request service-quota increases before the event?"

---

## Status vocabulary (every checklist item)

| Status | Meaning |
|---|---|
| ✅ Ready | Verified from API data retrieved this session. |
| 🔷 Attested | No API can observe it (or the data was incomplete) and the customer confirmed it — record who, when, evidence. Ranks with ✅. |
| ❔ Unverified | No data and no attestation yet. Ranks with ⚠️. |
| ⚠️ Needs Action | A gap that can be closed before the event; carries a lead time. |
| ❌ Blocker | A gap that **cannot** be closed within the available lead time. |
| ➖ N/A | Not relevant to this event (e.g. no chat channel). |

Items marked **(customer)** in the catalog have no API source: ask explicitly, never mark them ✅ from API data, and never invent an attestation.

---

## Step P0 — Prerequisites

Read-only IAM actions this mode uses: `connect:ListInstances`, `connect:DescribeInstance`, `connect:DescribeInstanceAttribute`, `connect:ListInstanceStorageConfigs`, `connect:GetMetricDataV2`, `connect:GetCurrentMetricData`, `connect:ListQueues`, `connect:DescribeQueue`, `connect:ListRoutingProfiles`, `connect:DescribeRoutingProfile`, `connect:ListUsers`, `connect:DescribeUser`, `connect:ListHoursOfOperations`, `connect:DescribeHoursOfOperation`, `connect:ListHoursOfOperationOverrides`, `connect:ListContactFlows`, `connect:DescribeContactFlow`, `connect:ListLambdaFunctions`, `connect:ListBots`, `connect:ListPhoneNumbersV2`, `connect:ListSecurityProfiles`, `connect:ListTrafficDistributionGroups`, `servicequotas:ListServiceQuotas`, `servicequotas:ListAWSDefaultServiceQuotas`, `cloudwatch:GetMetricData`, `cloudwatch:DescribeAlarms`, `lambda:GetFunctionConfiguration`, `lambda:GetFunctionConcurrency`, `lambda:ListProvisionedConcurrencyConfigs`, `lambda:GetAccountSettings`, `cloudtrail:LookupEvents`. Cost Explorer is not used.

`GetCurrentMetricData` / `GetMetricDataV2` are **session-policy sensitive** — an `AccessDenied` there is Runbook Category H1, not "no data".

**No account access? Answer rule and policy questions directly.** Many questions about this mode need no AWS API: the verdicts (READY / READY WITH ACTIONS / NOT READY, Step P5), when a gap is a Blocker versus Needs Action (the lead-time rule), the status vocabulary, the projection and threshold math (e.g. scaling a ConcurrentCallsPercentage peak by the event multiplier, or entering alarm thresholds as 0-1 decimals), and what a `PEAK-xxx` finding ID means. When the user asks such a question, or says no account access is available, answer from this file as the Peak Readiness module — do not ask the user to confirm the module, do not switch to Region Readiness or another module, and do not stop to resolve the access question. Only the live checks in Steps P2-P4 need the actions above; if they are unavailable, say so and give the rule-based answer.

---

## Step P1 — Event parameters

Ask for and record; if a value is not given, state the assumption:

| Input | Notes |
|---|---|
| Target instance / Region | Provided, or discover per `references/connect-ops-review-orchestrator.md` and let the customer pick |
| Expected peak | Absolute (e.g. "600 concurrent calls") **or** a multiplier vs. current peak ("2x") |
| Channels | Voice, chat (incl. SMS / WhatsApp), tasks, email, outbound campaigns |
| Event date / window | Drives **lead time** — quota increases can take up to ~3 weeks (very large increases longer) |
| Scope | Whole contact center (default) or one dimension (e.g. "just quota headroom") |
| Change freeze | Whether a pre-event freeze window applies (PEAK-030) |
| Serving queues / flows / numbers | Which queues, flows and phone numbers carry the event traffic |

**Coverage rule:** a paginated call not fully followed, a throttle, an empty result where data was expected, or a denied call makes the dependent item ❔ Unverified (`Data unavailable — [reason]`), never ✅. Never infer headroom from partial data.

---

## Step P2 — Capacity and quota headroom

**Data windows — do not assume long history:**
- AWS/Connect **CloudWatch metrics are retained only ~2 weeks** → concurrency peaks for at most the last 14 days.
- **GetMetricDataV2** covers up to **3 months**; each request must span < 35 days (DAY / WEEK / TOTAL). Default baseline: last 30 days, DAY interval. Last year's seasonal peak is beyond reach — ask the customer.

```bash
# Concurrency peak (last 14 days, hourly Maximum)
aws cloudwatch get-metric-data --start-time <14d ago> --end-time <now> --region <region> \
  --metric-data-queries '[
   {"Id":"pct","MetricStat":{"Metric":{"Namespace":"AWS/Connect","MetricName":"ConcurrentCallsPercentage","Dimensions":[{"Name":"InstanceId","Value":"<id>"},{"Name":"MetricGroup","Value":"VoiceCalls"}]},"Period":3600,"Stat":"Maximum"}},
   {"Id":"cc","MetricStat":{"Metric":{"Namespace":"AWS/Connect","MetricName":"ConcurrentCalls","Dimensions":[{"Name":"InstanceId","Value":"<id>"},{"Name":"MetricGroup","Value":"VoiceCalls"}]},"Period":3600,"Stat":"Maximum"}},
   {"Id":"breach","MetricStat":{"Metric":{"Namespace":"AWS/Connect","MetricName":"CallsBreachingConcurrencyQuota","Dimensions":[{"Name":"InstanceId","Value":"<id>"},{"Name":"MetricGroup","Value":"VoiceCalls"}]},"Period":3600,"Stat":"Sum"}},
   {"Id":"thr","MetricStat":{"Metric":{"Namespace":"AWS/Connect","MetricName":"ThrottledCalls","Dimensions":[{"Name":"InstanceId","Value":"<id>"},{"Name":"MetricGroup","Value":"VoiceCalls"}]},"Period":3600,"Stat":"Sum"}}]'

# Contact-volume baseline (last 30 days, per queue x channel per day)
aws connect get-metric-data-v2 --resource-arn <instance-arn> --start-time <30d ago> --end-time <now> \
  --interval '{"IntervalPeriod":"DAY"}' --groupings '["QUEUE","CHANNEL"]' \
  --filters '[{"FilterKey":"QUEUE","FilterValues":["<queue-id>", "..."]}]' \
  --metrics '[{"Name":"CONTACTS_HANDLED"},{"Name":"CONTACTS_QUEUED"},{"Name":"CONTACTS_ABANDONED"},{"Name":"AVG_HANDLE_TIME"},{"Name":"SUM_HANDLE_TIME"}]' \
  --region <region>

# Applied and default quotas (Connect service code = connect)
aws service-quotas list-service-quotas --service-code connect --region <region>
aws service-quotas list-aws-default-service-quotas --service-code connect --region <region>

# Current counts for count quotas
aws connect list-phone-numbers-v2 --target-arn <instance-arn> --region <region>
aws connect list-users / list-queues / list-routing-profiles / list-security-profiles / list-contact-flows / list-hours-of-operations --instance-id <id> --region <region>
```

`GetMetricDataV2` `FilterKey` QUEUE accepts up to 100 queue IDs per request; batch if needed.

**State the actual windows used** in the report.

**Projected peak** = observed recent peak × multiplier (or the absolute target). Caveats:
- If `CallsBreachingConcurrencyQuota` or `ThrottledCalls` > 0 in the baseline, the observed peak was **clipped** by the quota and understates demand — mark the projection "understated".
- Concurrency grows **faster than volume** once queues lengthen (queued calls hold a line).
- `CallsPerInterval` is a per-second rate — context only, not projectable against the concurrency quota.

**Quota-headroom bands** (one set for every capacity check): **Warning ≥ 0.70, Critical ≥ 0.80** of the limit (70 / 80 on a percent scale). 0.80 matches AWS's suggestion to alert at 80% of a quota; 0.70 is an early-warning heuristic.

- **Concurrent calls** — `ConcurrentCallsPercentage` is a **0–1 decimal** (0.8 = 80%). Projected fraction = peak fraction × multiplier (or target ÷ applied quota). Compare with 0.7 / 0.8, never 70 / 80. Calls over the quota are **rejected with a fast-busy tone**; outbound calls count, queued callbacks and external transfers do not. No datapoints → ❔, never "0%".
- **Chat / tasks / email / campaigns** — each has its own concurrency quota (Service Quotas). Live chat / task slots: `get-current-metric-data` with `SLOTS_ACTIVE` / `SLOTS_AVAILABLE` grouped by CHANNEL. A derived hourly average = `SUM_HANDLE_TIME` ÷ 3600 s from GetMetricDataV2 at HOUR interval (≤ 3 days per request) — a **floor** for the peak, not the peak. Instantaneous chat / task peak, email concurrency and campaign concurrency are **(customer)**.
- **Count quotas** — phone numbers, users, queues, routing / security profiles, flows, hours: projected count (current + what the event adds) ÷ applied limit. If a quota is not returned by Service Quotas, use the [documented default](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-service-limits.html) and say "documented default assumed".
- **API rate limits** are shared by every instance in the account and Region — no API measures current call rates → **(customer)**.
- **Integration / analytics quotas** — *Lambda functions per instance* (default 50; count from `list-lambda-functions`), *Lex bots per instance* (70, not adjustable), *Lex V2 bot aliases per instance* (100; from `list-bots --lex-version V2`), and — only if event flows enable analytics — *concurrent real-time calls with analytics* (300), *concurrent post-call analytics jobs* (200; ≈ avg call minutes × 0.4 × calls/hour ÷ 60, AWS's planning formula), *concurrent chat analytics jobs* (200).
- **Lex** — runtime concurrency is an **Amazon Lex V2** quota (not Connect): documented defaults 125 concurrent voice (RecognizeUtterance), 400 (StartConversation), 50 text — **(customer)** attests applied values. A production flow pointing at **TestBotAlias** (2 concurrent conversations; alias ARN ending `TSTALIASID` in `list-bots` output or the flow JSON) is a ❌ Blocker for any surge. Any **Lex V1** bot (`list-bots --lex-version V1`) is Blocker-level — Lex V1 support ended September 15, 2025.

---

## Step P3 — Dependency headroom

```bash
aws connect list-lambda-functions --instance-id <id> --region <region>
aws lambda get-function-configuration --function-name <arn>          # Timeout
aws lambda get-function-concurrency --function-name <arn>            # ReservedConcurrentExecutions
aws lambda list-provisioned-concurrency-configs --function-name <arn>
aws lambda get-account-settings --region <region>                    # ConcurrentExecutions, UnreservedConcurrentExecutions
aws cloudwatch get-metric-data ...  # AWS/Lambda Invocations, Errors, Throttles (Sum), Duration (p95, p99), ConcurrentExecutions (Maximum) per FunctionName, last 14 days
aws connect list-traffic-distribution-groups --instance-id <id> --region <region>
```

- **IVR Lambda concurrency** — Little's law: required ≈ projected invocations/s × avg duration (s); cross-check with observed max `ConcurrentExecutions` × multiplier. Compare with reserved concurrency (**also a cap**) or the account's unreserved concurrency. Missing reserved / provisioned concurrency is **not** a Blocker when unreserved headroom covers the projection. Any `Throttles` > 0 today is a failure risk.
- **Duration** — p95 should stay under **50% of each block's timeout** (guidance). Take the timeout from the flow JSON (`InvocationTimeLimitSeconds`); if absent, use the **synchronous maximum 8 s** (async up to 60 s). Connect retries a throttled / failed synchronous call up to 3 times within the timeout, so throttling first shows as caller latency. A function with no datapoints is ❔, not healthy.
- **Downstream integrations** (APIs, databases, CRM) behind the Lambdas → **(customer)**.
- **Resiliency** — a TDG with `Status` ACTIVE means Global Resiliency is configured. It needs a replica in a supported pair (`us-east-1`↔`us-west-2`, `eu-central-1`↔`eu-west-2`, `ap-northeast-1`→`ap-northeast-3`; see `references/region-readiness.md`), SAML identity, and AWS account-team engagement — it **cannot be stood up just before an event**.
- **Network from agent sites** → **(customer)**, never ✅: TCP 443 to the documented Connect domains, **UDP 3478 outbound** to the TURN endpoint, and (stateless firewalls only) inbound ephemeral UDP 49152–65535 (Windows) / 32768–61000 (Linux) for return traffic. Only if the customer allowlists by IP range does the `AmazonIpSpaceChanged` subscription matter. Details: `references/call_quality_playbook.md`.

---

## Step P4 — Operational preparedness

```bash
aws cloudwatch describe-alarms --region <region>          # no namespace filter: AWS/Connect, AWS/Lambda and metric-math alarms all count
aws connect describe-routing-profile / list-routing-profile-queues --instance-id <id> --routing-profile-id <rp> --region <region>
aws connect describe-queue --instance-id <id> --queue-id <q> --region <region>          # Status, HoursOfOperationId, MaxContacts
aws connect describe-hours-of-operation --instance-id <id> --hours-of-operation-id <h> --region <region>
aws connect list-hours-of-operation-overrides --instance-id <id> --hours-of-operation-id <h> --region <region>
aws connect describe-instance-attribute --instance-id <id> --attribute-type CONTACTFLOW_LOGS --region <region>
aws connect list-instance-storage-configs --instance-id <id> --resource-type CONTACT_TRACE_RECORDS --region <region>
aws connect describe-contact-flow --instance-id <id> --contact-flow-id <serving-flow> --region <region>
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=connect.amazonaws.com \
  --start-time <freeze start> --end-time <now> --region <region>
```

- **Monitoring** — alarms on `ConcurrentCallsPercentage` (threshold entered as **0.7 / 0.8** — an alarm at 80 never fires), `CallsBreachingConcurrencyQuota` > 0, `ThrottledCalls` > 0, `ContactFlowFatalErrors` > 0, `MisconfiguredPhoneNumbers` > 0, `MissedCalls`, `QueueSize` / `LongestQueueWaitTime` beyond SLA **per critical queue**, `ContactFlowErrors` per critical flow, and Lambda errors / throttles. If `describe-alarms` paginates incompletely, do not report an alarm as missing.
- **Staffing** — offered load ≈ projected contacts per interval × `AVG_HANDLE_TIME` ÷ interval length ≈ agents busy at peak (add shrinkage and an occupancy target for headcount). Compare with agents on the serving routing profiles (`list-users` + `describe-user`) and the users quota. Actual schedules → **(customer)**.
- **Routing for the surge** — overflow is **flow logic**, not a queue setting: look in the serving flows for Check queue status / Check staffing, the Transfer to queue error / at-capacity branch, and queued callback or estimated-wait messaging. The only queue-level control is `MaxContacts` — confirm headroom over the projected backlog. Media concurrency is a chat / task / email lever only (voice is fixed at 1).
- **Hours** — the schedule (in its `TimeZone`) and event-day overrides must cover the event window. If overrides cannot be read, they are **(customer)**.
- **Change freeze** — CloudTrail mutations (`Create*` / `Update*` / `Delete*` / `Associate*`) during the freeze window; list changes by unexpected principals. Honour `NextToken`.
- **DR / runbook** — documented peak-load failover runbook, tested regularly (current guidance: **monthly**), and a phone-number re-point / cutover plan → all **(customer)**.

---

## Step P5 — Verdict

Assign each catalog item a status; a dimension takes the worst status of its items (🔷 ranks with ✅, ❔ with ⚠️); the verdict rolls up the dimensions.

| Verdict | Rule |
|---|---|
| ✅ **READY** | Every item ✅, 🔷 (attestation recorded) or ➖. List which items rest on attestations. |
| ⚠️ **READY WITH ACTIONS** | No ❌, but one or more ⚠️ / ❔. Proceed only after completing the actions (or collecting attestations) before the event. |
| ❌ **NOT READY** | One or more ❌ — e.g. projected peak exceeds a quota and the increase cannot land in time, IVR Lambdas cannot scale in time, a required resiliency capability cannot be built in time, or no monitoring and no time to add it. |

Every ❌ is **conditional on lead time** — the same gap with enough lead time is ⚠️.

---

## Step P6 — Report

Satisfy the Report Generation Gate in `references/global-rules.md` first. Then produce:

1. **Header** — `Verdict: ✅ READY | ⚠️ READY WITH ACTIONS | ❌ NOT READY` · date · event window · lead time (days)
2. **Event Parameters** — instance / Region, channels, observed peak and data windows, whether the baseline was quota-clipped, projected peak and method
3. **Readiness by Dimension** — `| Dimension | PEAK-ID | Status | Current | Required for event | Source (API, resource, timestamp / customer) | Action |` covering Capacity / Quota, Dependencies / Lambda, Resiliency, Network, Monitoring, Staffing / Routing, DR / Runbook
4. **Customer Attestations** — `| Item | Attested by | Date | Evidence |`, plus every ❔ item still awaiting attestation
5. **Required Actions (longest lead time first)** — each with its deadline relative to the event date (quota increases usually lead)
6. **Machine-readable verdict** (optional, for CI / gating):

```json
{
  "module": "peak-readiness",
  "instance_id": "<id>",
  "region": "<region>",
  "event_window": {"start": "<ISO8601>", "end": "<ISO8601>"},
  "projected_peak_concurrent_calls": 0,
  "projection_understated": false,
  "verdict": "READY | READY_WITH_ACTIONS | NOT_READY",
  "dimensions": [{"name": "capacity_quota", "status": "ready | attested | unverified | needs_action | blocker | not_applicable"}],
  "attestations": [{"item": "PEAK-041", "attested_by": "<name/role>", "date": "<ISO8601>", "evidence": "<note>"}],
  "blockers": [],
  "actions": [{"id": "PEAK-001", "summary": "<action>", "lead_time_days": 0, "deadline": "<ISO8601>"}]
}
```

Every action is a proposal only — this mode never files a quota request or changes a configuration.

---

## Finding catalog

| ID | Dimension | Item | Gap severity (worst case) |
|---|---|---|---|
| PEAK-001 | Capacity / Quota | Projected concurrent-call fraction < 0.80, and `CallsBreachingConcurrencyQuota` / `ThrottledCalls` = 0 in the baseline (> 0 = callers already rejected) | Blocker if the increase can't land in time, else Needs Action |
| PEAK-002 | Capacity / Quota | Phone-number quota has headroom for numbers the event adds | Needs Action |
| PEAK-003 | Capacity / Quota | User / queue / routing-profile / security-profile quotas have headroom | Needs Action |
| PEAK-004 | Capacity / Quota | Contact-flows-per-instance quota has headroom for new event flows | Needs Action |
| PEAK-005 | Capacity / Quota | Any quota in the Warning band (0.70–0.80) has an increase filed with adequate lead time | Needs Action |
| PEAK-006 | Capacity / Quota | Chat / task / email / campaign projected concurrency under each channel quota; instantaneous chat/task peak, email and campaign concurrency **(customer)** | Blocker if the increase can't land in time, else Needs Action |
| PEAK-007 | Capacity / Quota | Connect API request-rate headroom for surge-time Lambdas, wallboards and integrations, with retry + backoff **(customer)** | Needs Action |
| PEAK-008 | Capacity / Quota | Integration / analytics quotas (Lambda functions, Lex bots and aliases, Contact Lens concurrency) have headroom | Needs Action (Blocker if not fixable in time) |
| PEAK-010 | Dependencies | IVR Lambdas reach projected concurrency (Little's law vs. reserved / unreserved) | Blocker only if the shortfall can't be fixed in time |
| PEAK-011 | Dependencies | No current Lambda throttling on the IVR path | Needs Action |
| PEAK-012 | Dependencies | Lambda p95 < 50% of each block's timeout at projected load; p99 < timeout | Needs Action |
| PEAK-013 | Dependencies | Downstream integrations provisioned for the surge **(customer)** | Needs Action |
| PEAK-014 | Dependencies | Lex: V2 runtime concurrency attested **(customer)**; no TestBotAlias in production; no Lex V1 | Blocker (TestBotAlias / V1 not fixable in time), else Needs Action |
| PEAK-020 | Resiliency | Events that require it have Global Resiliency — replica in a supported pair + ACTIVE TDG | Needs Action (Blocker if required and not in place in time) |
| PEAK-021 | Network | Agent-site network requirements reachable **(customer)** — never ✅ | Blocker if a site is confirmed blocked and can't be fixed in time |
| PEAK-022 | Network | IP-range allowlisting only: `AmazonIpSpaceChanged` subscription **(customer)**; domain allowlist → ➖ | Needs Action |
| PEAK-030 | Staffing / Routing | Pre-event change freeze respected (no unexpected CloudTrail mutations) | Needs Action |
| PEAK-031 | Monitoring | Alarms on `ConcurrentCallsPercentage` (0.7 / 0.8), `CallsBreachingConcurrencyQuota`, `ThrottledCalls` | Needs Action |
| PEAK-032 | Monitoring | Alarms on `QueueSize` / `LongestQueueWaitTime` per critical queue, `MissedCalls`, `QueueCapacityExceededError` | Needs Action |
| PEAK-033 | Monitoring | Alarms on `ContactFlowErrors` per critical flow, `ContactFlowFatalErrors`, `MisconfiguredPhoneNumbers`, Lambda errors / throttles | Needs Action |
| PEAK-034 | Monitoring | Contact flow logs enabled and a CTR stream configured for post-event analysis; stream consumption **(customer)** | Needs Action |
| PEAK-035 | Staffing / Routing | Hours of operation (incl. event-day overrides) cover the event window | Needs Action (Blocker if not correctable in time) |
| PEAK-036 | Staffing / Routing | Serving flows have an overflow / saturation path and queue `MaxContacts` has headroom | Needs Action |
| PEAK-037 | Staffing / Routing | Chat / task / email media concurrency appropriate (voice-only → ➖) | Needs Action |
| PEAK-038 | Staffing / Routing | Offered load vs. agents on serving profiles; actual schedules **(customer)** | Needs Action |
| PEAK-039 | Staffing / Routing | `MisconfiguredPhoneNumbers` = 0 for event numbers; load / synthetic-test plan and results **(customer)** | Needs Action |
| PEAK-040 | DR / Runbook | Documented peak-load failover runbook **(customer)** | Needs Action |
| PEAK-041 | DR / Runbook | Failover tested regularly (monthly guidance) and recently for this scenario **(customer)** | Needs Action |
| PEAK-042 | DR / Runbook | Phone-number re-point / secondary-Region cutover plan **(customer)** | Needs Action |

Related Review-module findings (e.g. `OPS-002` alarms, `REL-001` TDG, `PERF-002` Lex test alias) may be cited alongside the PEAK ID.

---

## Sources

- [Amazon Connect service quotas](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-service-limits.html)
- [Requesting a service quota increase](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)
- [Monitoring Connect with CloudWatch](https://docs.aws.amazon.com/connect/latest/adminguide/monitoring-cloudwatch.html)
- [Managing Lambda concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)
- [Amazon Connect Global Resiliency](https://docs.aws.amazon.com/connect/latest/adminguide/get-started-connect-global-resiliency.html)
- [Amazon Lex V2 quotas](https://docs.aws.amazon.com/lexv2/latest/dg/quotas.html)
