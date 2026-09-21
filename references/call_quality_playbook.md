# Call Quality & Call Failure — Reference Guide

---

## Call Quality Intake Checklist (Category D)

**Run this checklist on any Connect troubleshooting pass — regardless of whether pillar assessments surfaced a PERF-CQ finding. Configuration gaps alone do not reveal active call quality symptoms.**

This is a decision checklist, not a scripted chat gate — resolve each item however fits the calling context (ask a human directly, read from a ticket/report, take as structured input). No step here requires waiting on a live chat turn.

### D0 — Call Quality Gate

Determine: is there an active or recent call quality issue? (choppy audio, one-way audio, dropped calls, echo, calls not arriving, etc.)

- **If NO** → record "No active call quality issues reported" and skip to reporting.
- **If YES** → work through D0.1–D0.5 below, then route to the matching PERF-CQ sub-pattern.

---

### D0.1 — Symptom Classification

Identify the symptom(s):

- Choppy / robotic audio
- One-way audio (agent can't hear customer, or vice versa)
- Dropped calls / sudden disconnects
- Echo
- Silence / dead air after connect
- Calls not arriving at Connect at all
- CCP not connecting / agent status stuck
- Other

Record the exact symptom(s) — this determines which PERF-CQ sub-pattern to prioritize.

---

### D0.2 — Scope Assessment

Determine scope:

a) Single agent
b) Multiple agents, same office/location
c) Multiple agents, different locations
d) All agents across the board

| Scope | Priority Path |
|-------|---------------|
| Single agent | PERF-CQ-002 (Agent-Side) first |
| Same-office multiple agents | PERF-CQ-002 (Network/Firewall) |
| Cross-location multiple agents | PERF-CQ-003 (Telephony) + PERF-CQ-002 |
| All agents | PERF-CQ-003 (Telephony/Instance-level) — escalate immediately |

---

### D0.3 — Contact ID Collection

Collect 3–5 Contact IDs from affected calls, with exact UTC timestamps of when the quality issue occurred. (Contact IDs are available in the Contact Control Panel history or Connect Real-Time/Historical Metrics reports.)

⚠️ **Time-sensitive:** Carrier log retention is typically 24–48 hours only. Collect Contact IDs as soon as possible if the issue is ongoing or recent. Tag each Contact ID with its observed symptom and UTC timestamp.

---

### D0.4 — CCP Log Collection (blocks PERF-CQ-004 only)

Agent-side call quality analysis (PERF-CQ-004) requires CCP logs. Collection methods:

**Method A — From the CCP directly (easiest):**
1. In the agent's CCP, open Settings (gear icon)
2. Click "Download Logs"
3. Save the .txt log file

**Method B — From browser DevTools (if CCP was refreshed):**
1. Open DevTools (F12) in the browser running CCP
2. Go to the Console tab
3. Right-click in the console → "Save as..."

**Method C — WebRTC Diagnostic Dump (advanced diagnosis):**
1. Open CCP in Chrome
2. In a new tab, go to `chrome://webrtc-internals/`
3. Reproduce the issue during a live call
4. Click "Download the PeerConnection updates and stats data"

⚠️ **Timing:** CCP logs are session-scoped. If the browser was refreshed or closed after the issue occurred, the logs are gone — capture immediately while the session is still active.

Once collected, logs need to be accessible for analysis (e.g., uploaded to S3 and the location shared):

```bash
aws s3 mb s3://connect-ccp-logs-<account-id> --region us-east-1
aws s3 cp ccp-log.txt s3://connect-ccp-logs-<account-id>/logs/
aws s3 cp webrtc-internals-dump.txt s3://connect-ccp-logs-<account-id>/logs/
```

**Note:** This step is required ONLY for PERF-CQ-004. PERF-CQ-001, 002, and 003 do not require CCP logs and must not be blocked waiting for them.

---

### D0.5 — Agent Network Context

Gather the affected agent's setup:

1. Is the agent on VPN? If yes, is split-tunneling enabled?
2. Is there a corporate proxy or firewall between the agent and the internet?
3. Are UDP port 3478 and TCP port 443 allowed through the firewall for `*.connect.aws` and `*.transport.connect.aws`?
4. What browser and version is the agent using?
5. Native CCP, embedded CCP (custom app), or third-party CTI (Salesforce, Zendesk, etc.)?

These answers determine whether the PERF-CQ-002 network checklist items apply.

---

### PERF-CQ Sub-Pattern Routing (Post-Intake)

Once D0.1–D0.5 are resolved, route to sub-patterns:

| Condition | Sub-Pattern |
|-----------|-------------|
| Contact IDs available + CTR available | PERF-CQ-001 first |
| Symptom = audio quality, scope = single agent | PERF-CQ-002 first |
| Symptom = calls not arriving, scope = all agents | PERF-CQ-003 first |
| CCP log collected and accessible | PERF-CQ-004 |

---

## PERF-CQ Sub-Patterns

- **PERF-CQ-001:** Initial Validation & Triage — Did Connect receive the call? Is a recording available? Check Disconnect Reason on CTR.
- **PERF-CQ-002:** Agent-Side Troubleshooting (WebRTC / CCP / Network) — assess impact scope, check WebRTC metrics (packet loss, jitter, RTT), network checklist, browser/CCP checklist, CCP log analysis.
- **PERF-CQ-003:** Telephony-Side Troubleshooting (Carrier / PSTN) — validate call reception, identify telephony path, collect data for AWS Support escalation.
- **PERF-CQ-004:** CCP Log Analysis — collect agent logs, parse for error signatures (ICE failures, signaling failures, packet loss, softphone errors), correlate findings.

## PERF-CQ Metrics Thresholds

| Metric | Acceptable | Degraded | Critical |
|--------|------------|----------|---------|
| Packet Loss (ToInstance / FromInstance) | < 1% | 1–5% | > 5% |
| Round-Trip Time (RTT) | < 150ms | 150–300ms | > 300ms |
| Jitter Buffer | < 30ms | 30–50ms | > 50ms |

---

## Glossary of Terms

| Term | Definition |
| --- | --- |
| **PABX** | Private Automatic Branch Exchange — a private telephone switchboard connecting internal devices to each other and the public telephone network |
| **AWS Support** | Front-line AWS Premium Support team handling cases through the Technical Issue channel |
| **Toll-Free Numbers** | Numbers callers can dial at no charge; route through RespOrg carriers before reaching AWS |
| **DIDs** | Direct Inward Dialing — locally-formatted numbers matching local subscriber dialing patterns |
| **CCP** | Contact Control Panel — the agent interface for receiving/managing calls and chats |
| **WebRTC** | Web Real-Time Communication — browser-based technology for encrypted audio/video; Connect uses it for softphone connectivity |
| **ICE** | Interactive Connectivity Establishment — protocol for NAT traversal in WebRTC (STUN/TURN) |
| **TURN** | Traversal Using Relays around NAT — relay server that carries WebRTC media over UDP 3478 when a direct peer-to-peer path can't be established |
| **CTR / contact record** | Metadata record for each contact in Amazon Connect (AWS now uses "contact record"; "contact trace record/CTR" is the former term) |

---

## Foundational Knowledge

### High-Level Architecture (Template)

A complete call-quality architecture should document these layers:

**Third-Party / Carrier Layer**:

- Third-party hosted numbers (Toll-Free) forwarding into Connect
- Third-party partner contact center transferring calls to Connect
- On-premises PABX forwarding calls into Connect

**AWS / Amazon Connect Layer**:

- Connect instance receiving calls via AWS carrier
- Contact flows processing the call
- Call recording capture point (before audio reaches agent)

**Agent / Corporate Network Layer**:

- WebRTC traffic path from Connect → internet → corporate network → agent browser
- Any proxies, firewalls, VPNs, or SSL inspection in the path
- Agent geographic and network groupings

**Recommended swim-lane layers for architecture diagrams**:

1. Customer on-premise PABX
2. Egress carrier from on-premise
3. AWS (Amazon Connect)
4. Egress to open internet for CCP WebRTC traffic
5. Corporate network and end agent

---

## Section 1: Initial Validation (Detailed)

Execute these validation steps to narrow scope. Include results when opening an AWS Support case.

### 1.1 Identify and Analyze Call Samples

- Collect 3–5 call samples demonstrating the issue
- Evaluate the entire call flow: Amazon Connect, CCP, on-premises services, carrier connectivity
- Record Contact IDs, timestamps (UTC), and observed symptoms

### 1.2 Check Amazon Connect Call Reception

- Monitor **CallsPerInterval** and **ConcurrentCalls** CloudWatch metrics
- Unexpected drops indicate telephony-side issues before Connect

### 1.3 Call Recording Availability

- If available: analyze for which leg (customer vs agent) has the audio issue
- Two distinct legs in the recording: Customer ↔ Connect, and Connect ↔ Agent

### 1.4 Disconnect Reason Analysis

| Disconnect Reason | Meaning | Path |
| --- | --- | --- |
| CONTACT_FLOW_DISCONNECT | Flow ended the call | Review flow logs |
| CUSTOMER_DISCONNECT | Caller side ended | Could be intentional, network, or audio |
| AGENT_DISCONNECT | Agent ended via CCP | Check if intentional or CCP error |
| TELECOM_PROBLEM | Carrier/network confirmed | Escalate to AWS Support immediately |
| THIRD_PARTY_DISCONNECT | Third-party integration ended | Check Lambda/integration timeouts |

### 1.5 Call Recording Analysis

Call recordings capture audio at the Amazon Connect instance level (before reaching the agent). This allows granular analysis of two legs:

- **Customer ↔ Amazon Connect** (carrier/telephony quality)
- **Amazon Connect ↔ Agent** (WebRTC/CCP quality)

If customer-side audio is clean but agent-side is degraded → agent network issue. If customer-side audio is degraded but agent-side is clean → carrier/telephony issue. If both are degraded → likely an Amazon Connect-side issue → escalate.

---

## Section 2: Agent-Side Troubleshooting (Detailed)

### 2.1 Assess Impact Scope

| Scope | Likely Cause | Action |
| --- | --- | --- |
| Single agent | Local device/network/browser | Agent-level troubleshooting |
| Multiple agents, same office | Office network/firewall/proxy | Network team engagement |
| Multiple agents, different locations | AWS-side or Connect config | Escalate to AWS Support |
| All agents | Instance-level or regional | Immediate escalation |

### 2.2 WebRTC Connectivity Requirements

Amazon Connect softphone requires:

- **UDP port 3478** (SEND/RECEIVE) — STUN/TURN for media; this is the media path
- **TCP port 443** — signalling/HTTPS and the WebSocket channel (control, not a media/TURN fallback)
- **WebSocket** — signaling channel over TCP 443 (must not be intercepted by proxy)
- **DNS resolution** — `*.connect.aws`, `*.transport.connect.aws`
- **Bandwidth** — minimum 100 kbps per concurrent softphone call
- **No SSL/TLS inspection** on WebRTC or WebSocket traffic

### 2.3 Common Agent-Side Issues and Fixes

| Issue | Symptom | Fix |
| --- | --- | --- |
| Multiple CCP tabs | Audio routing conflicts, echo | Close all but one tab |
| Browser extension interference | CCP fails to connect | Disable extensions, test in incognito |
| Outdated browser | Random disconnects | Update to latest supported version |
| Microphone permissions | No audio from agent | Grant mic permission in browser settings |
| VPN split-tunneling | High latency/packet loss | Route WebRTC traffic outside VPN |
| Proxy intercepting WebSocket | Signaling failure | Bypass proxy for Connect domains |

### 2.4 WebRTC Metrics Reference (CloudWatch)

| Metric | Namespace | What it measures |
| --- | --- | --- |
| ToInstancePacketLossRate | AWS/Connect | Packet-loss ratio (0–100%) for WebRTC calls in the instance, reported every 10s |

> Only `ToInstancePacketLossRate` is published to AWS/Connect. There is **no** `FromInstancePacketLossRate` metric.

Dimensions: `Participant=Agent`, `Type of Connection=WebRTC`, `Instance ID={ID}`, `Stream Type=Voice`

---

## Section 3: Telephony Troubleshooting (Detailed)

### 3.1 Telephony Engagement Best Practices

- **Carrier log retention**: Telecom carriers typically retain logs 24–48 hours only
- **Call samples must be < 24 hours old** when engaging AWS Support
- **Share call samples daily** for ongoing issues
- **Pre-approve media captures** — provide source/destination numbers and timing preferences
- **Ensure ops team receives** AWS Support case update notifications

### 3.2 Third-Party Escalation Checklist

When the issue is downstream of Amazon Connect (customer's carrier, PABX, or third-party):

- Identify which segment of the call path is affected
- Gather: source number, destination number, timestamp, call duration, symptom
- Engage the third-party provider with the same data
- Request: CDR (Call Detail Records), media quality reports, route traces
- Confirm: number porting status, route announcements, congestion indicators

### 3.3 Toll-Free vs DID Considerations

| Type | Routing Path | Common Issues |
| --- | --- | --- |
| Toll-Free | Caller → RespOrg carrier → AWS carrier → Connect | Higher latency, carrier congestion, RespOrg routing delays |
| DID | Caller → local carrier → AWS carrier → Connect | Number porting issues, local number formatting |

### 3.4 International Considerations

- Numbers must be in E.164 format (+{country_code}{number})
- Some countries have regulatory restrictions on inbound/outbound
- International calls have higher inherent latency
- Check country-specific CLI (Caller Line Identification) requirements

---

## Section 4: Engaging AWS Support

### When to Open a Case (Call Quality)

- TELECOM_PROBLEM disconnect reason on any call
- Consistent packet loss > 5% with no local network explanation
- Calls confirmed not arriving at Connect
- Audio issues affecting all agents regardless of location/network
- International routing failures with correct E.164 formatting

### What to Include in the Case

**Required**:

- 3–5 Contact IDs with exact UTC timestamps
- Source and destination phone numbers (E.164 format)
- Call samples < 24 hours old
- Description of audio issue (one-way, choppy, dropped, silence, echo)
- Whether inbound only, outbound only, or both
- Impact scope (single agent, multiple, all)

**Recommended**:

- Call recordings with timestamp of quality issue
- CloudWatch metric screenshots (CallsPerInterval, PacketLoss)
- CCP logs
- Pre-approval for telephony media captures
- Network topology diagram showing agent connectivity path

### Best Practice

- Use **chat or phone** for case creation (not web form) — provide comprehensive data upfront, minimize follow-ups, accelerate service-team engagement.

---

## Section 5: Appendix

### A. WebRTC Diagnostic Dump (Advanced)

For persistent agent-side issues that standard metrics can't explain:

1. Open CCP in Chrome
2. Navigate to: `chrome://webrtc-internals/`
3. Reproduce the issue during a call
4. Click "Download the PeerConnection updates and stats data"
5. Store the dump alongside the CCP log for analysis

The dump provides per-second resolution on:

- ICE candidate pairs and connectivity checks
- Codec negotiation results
- Bandwidth estimation history
- Packet loss/jitter at 1-second granularity
- TURN relay usage

### B. CCP Log Collection Procedures

**Method A — CCP Settings (simplest)**:

- In CCP → gear icon → "Download Logs"
- Saves a text file with session events

**Method B — Browser DevTools**:

- Open DevTools (F12) → Console tab
- Reproduce the issue
- Right-click in console → "Save as..."

**Method C — amazon-connect-streams.js**:

- If using the Streams API, logs write to the browser console by default
- Capture full console output during the problematic call

**⚠️ Timing**: CCP logs are session-scoped. Refreshing or closing the browser clears them. Capture immediately after the issue occurs.

### C. Proactive Monitoring Recommendations

- Implement call canaries (synthetic test calls) on critical numbers
- Set CloudWatch alarms on:
  - `CallsPerInterval` sudden drops (>50% below baseline)
  - `ConcurrentCallsPercentage` approaching quota (>80%)
  - `ToInstancePacketLossRate` exceeding 5%
- Review and update call simulations to match evolving customer interactions
- Monitor agent CCP connectivity via periodic health checks

### D. Key Documentation Links

- [Voice channel in Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/concepts-telephony.html)
- [CTR data model (Disconnect Reasons)](https://docs.aws.amazon.com/connect/latest/adminguide/ctr-data-model.html)
- [Set up call recordings](https://docs.aws.amazon.com/connect/latest/adminguide/set-up-recordings.html)
- [Supported browsers for CCP](https://docs.aws.amazon.com/connect/latest/adminguide/browsers.html)
- [Contact flow log troubleshooting](https://repost.aws/knowledge-center/connect-contact-flow-errors)
- [CloudWatch monitoring for Connect](https://catalog.workshops.aws/amazon-connect-operational-workshop/en-US/3awsservicesforamazonconnectoperations/1amazoncloudwatch)
- [CCP Log Parser tool](https://tools.connect.aws/ccp-log-parser/)
