# Amazon Connect Operations Review — Pillar 2: Security

## Description

Assesses Amazon Connect security posture: IAM profiles, authentication, encryption, approved origins, audit trail, AI guardrails, and data protection.

## When to Use

- Always runs (for any discovered instance)
- User asks about security posture, permissions audit, or compliance

## Execution Strategy

```
Budget: 90 seconds
APIs: ~16 calls (after shared data from Phase 0)
Depends on: Phase 0 output (instance list, integrations, tags)
```

## Pre-Flight (5 seconds)

```
Test: connect:ListSecurityProfiles (MaxResults=1) on first instance
  - SUCCESS → proceed
  - AccessDeniedException → Mark pillar as "PARTIAL — core security checks only"
```

## Checks

### Check 2.1 — Security Profile Audit (25 seconds max)

**API calls**:
```
connect:ListSecurityProfiles (MaxResults=100, 1 page per instance)
connect:ListSecurityProfilePermissions (for top 5 profiles by name — Admin, CallCenter, QualityAnalyst, etc.)
```

**Sampling rule**: Describe permissions for UP TO 5 profiles:
1. Any profile with "Admin" in name
2. Any profile with "Agent" in name (most populated)
3. Any custom-named profile (not default AWS profiles)

**Checks**:
- [ ] Over-privileged profiles — Admin profile assigned to >5 users?
- [ ] Unused profiles — profiles with 0 assigned users
- [ ] Custom profiles exist — or only defaults? (defaults = no least-privilege effort)
- [ ] Permission count per profile — >50 permissions = review needed

### Check 2.2 — User & Authentication (20 seconds max)

**Data source**: Phase 0 shared data (ListUsers count) + targeted DescribeUser

**API calls**:
```
connect:DescribeUser (sample 10 users — first 5 + last 5 by creation)
connect:ListAuthenticationProfiles (MaxResults=10)
connect:DescribeAuthenticationProfile (for each found)
```

**Checks**:
- [ ] Identity type — SAML (✅ federated) vs CONNECT_MANAGED (⚠️ local passwords)
- [ ] SAML cert expiry — if authentication profile shows cert, check expiry date
- [ ] MFA enforcement — authentication profile config
- [ ] Duplicate/cross-domain users — same email across instances
- [ ] Inactive users — users with no recent login (if data available)

### Check 2.3 — Approved Origins & Network (10 seconds max)

**API calls**:
```
connect:ListApprovedOrigins (per instance)
```

**Checks**:
- [ ] Wildcard origins — `*` or `*.example.com` = CRITICAL
- [ ] HTTP (not HTTPS) origins — insecure
- [ ] Localhost origins in production — dev leftover
- [ ] Excessive origins (>20) — review needed

### Check 2.4 — Encryption & Storage (15 seconds max)

**API calls**:
```
connect:DescribeInstanceStorageConfig (per instance, for recordings + transcripts)
kms:DescribeKey (for the KMS key ARN from storage config)
s3:GetBucketEncryption (for recording bucket)
s3:GetBucketPolicy (for recording bucket)
```

**Checks**:
- [ ] Recording encryption — KMS key configured? AWS-managed or CMK?
- [ ] S3 bucket encryption — SSE-S3 minimum, SSE-KMS preferred
- [ ] Bucket policy — public access blocked? Least-privilege?
- [ ] Storage config exists — if no storage config, recordings may not be stored

**Error handling**: If kms/s3 APIs denied, note "Encryption verification requires kms:DescribeKey and s3:GetBucket* permissions" and skip.

### Check 2.5 — AI Guardrails (10 seconds max)

**Condition**: Only if Phase 0 found WISDOM_ASSISTANT or Q_IN_CONNECT integrations.

**API calls**:
```
wisdom:ListAIGuardrails (per assistant)
wisdom:GetAIGuardrail (for each found, max 3)
```

**Checks**:
- [ ] Guardrail exists — AI-enabled instance WITHOUT guardrail = CRITICAL
- [ ] Topic restrictions configured — what topics are blocked?
- [ ] Content filters enabled — PII, toxicity, etc.
- [ ] Guardrail version pinned — or using DRAFT?

**Pre-flight**: Test wisdom:ListAIGuardrails first. If denied → mark as "Pillar 7 dependency — wisdom: namespace not accessible"

### Check 2.6 — Audit Trail (10 seconds max)

**API calls**:
```
cloudtrail:LookupEvents
  LookupAttributes: [{AttributeKey: "EventSource", AttributeValue: "connect.amazonaws.com"}]
  MaxResults: 10
  StartTime: 7 days ago
```

**Checks**:
- [ ] CloudTrail logging Connect events — any events in last 7 days?
- [ ] If 0 events → CloudTrail may not be enabled for Connect (CRITICAL for compliance)
- [ ] Event types — CreateUser, UpdateContactFlowContent, DeleteQueue = change activity

**Error handling**: If cloudtrail:LookupEvents denied → note "Audit trail verification requires cloudtrail:LookupEvents"

## Findings Output Format

```markdown
## Pillar 2: Security — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- Assessment completeness: {%}

### Findings

#### 🔴 CRITICAL
- [SEC-001] Wildcard approved origin detected: {origin}
  - Impact: Any website can embed Connect CCP — XSS/clickjacking risk
  - Fix: Replace with specific domain origins

- [SEC-002] AI-enabled instance has no guardrails configured
  - Impact: AI agent can discuss unrestricted topics, potential data leakage
  - Fix: Create and attach AI guardrail with topic restrictions

- [SEC-003] No CloudTrail events for Connect in last 7 days
  - Impact: No audit trail — compliance and forensics gap
  - Fix: Verify CloudTrail is enabled and logging management events

#### 🟡 HIGH
- [SEC-004] CONNECT_MANAGED identity — local passwords without federation
- [SEC-005] Admin security profile assigned to {n} users (should be ≤3)
- [SEC-006] Recording storage using AWS-managed KMS (not CMK)

#### 🟡 MEDIUM
- [SEC-007] {n} unused security profiles — cleanup needed
- [SEC-008] No custom security profiles — using defaults only
- [SEC-009] Authentication profile — MFA not enforced

#### 🟢 LOW
- [SEC-010] {n} approved origins (review if all still needed)

### Recommendations (Prioritized)
1. Remove wildcard approved origins immediately
2. Attach guardrails to all AI-enabled instances
3. Migrate to SAML/federated identity if using CONNECT_MANAGED
4. Implement least-privilege security profiles
5. Enable CloudTrail for Connect API audit
```

## Timeout Handling

```
At 70 seconds: Stop issuing new API calls.
At 80 seconds: Produce findings from data collected so far.
Priority order if timeout approaching: 2.1 → 2.3 → 2.5 → 2.4 → 2.6 → 2.2
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException, ResourceNotFoundException
If wisdom:* fails → skip Check 2.5, note in output
If kms:/s3: fails → skip Check 2.4 partially, note in output
```