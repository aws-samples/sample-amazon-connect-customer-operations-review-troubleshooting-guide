# IAM Permission Error Reference for Amazon Connect

Last updated: 2026-09-10

---

## The Three Critical Error Types — Never Confuse Them

### Error Type 1: "no identity-based policy allows [action]"

**Meaning:** No IAM policy attached to the role grants this permission.

**Fix:** Attach an IAM policy to the role that grants the missing action.

**Common trap — tag conditions on List actions:**
If the policy uses `aws:ResourceTag` as a condition on `Resource: *` for List-level actions
(e.g., `logs:DescribeLogGroups`, `lambda:ListFunctions`, `kinesis:ListStreams`), IAM evaluates
the tag against `*` which has no tags — so the condition is NEVER true and the call fails
with this same error even though a policy statement exists.

Fix: Split List and Get/Describe into separate statements:
```json
{
  "Sid": "ListActionsNoTagCondition",
  "Effect": "Allow",
  "Action": [
    "logs:DescribeLogGroups",
    "logs:DescribeLogStreams",
    "lambda:ListFunctions",
    "lambda:ListTags",
    "kinesis:ListStreams",
    "firehose:ListDeliveryStreams",
    "lex:List*",
    "s3:ListAllMyBuckets"
  ],
  "Resource": "*"
},
{
  "Sid": "GetDescribeTagScoped",
  "Effect": "Allow",
  "Action": [
    "lambda:GetFunction",
    "kinesis:DescribeStream",
    "firehose:DescribeDeliveryStream",
    "lex:Describe*",
    "s3:GetBucketLocation",
    "s3:ListBucket",
    "s3:GetObject",
    "logs:FilterLogEvents",
    "logs:GetLogEvents",
    "logs:StartQuery",
    "logs:GetQueryResults",
    "wisdom:Get*",
    "wisdom:List*"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/env": ["cc-devops", "cc-devops-oregon"]
    }
  }
}
```

**Affected services (commonly):**
- cloudwatch:DescribeAlarms, cloudwatch:GetMetricData, cloudwatch:ListMetrics
- logs:DescribeLogGroups, logs:FilterLogEvents, logs:StartQuery, logs:GetQueryResults
- lambda:ListFunctions, lambda:GetFunction
- kms:DescribeKey, kms:ListKeys
- s3:GetBucketPolicy, s3:GetBucketEncryption, s3:GetBucketLifecycleConfiguration
- ce:GetCostAndUsage
- iam:SimulatePrincipalPolicy

**Resolved — no longer applies:** `cloudtrail:LookupEvents` (and `cloudtrail:DescribeTrails`,
`cloudtrail:GetTrailStatus`) is confirmed read-only/non-mutating and available under the
agent's standard controls as of 2026-09-10. It no longer requires a separate IAM grant and
should not be diagnosed under this error type.

---

### Error Type 2: "no session policy allows [action]"

**Meaning:** A session policy passed at sts:AssumeRole time restricts the action — OR an
AWS Organizations SCP denies it. The role's identity-based policy may technically allow it,
but the effective session permissions are further scoped down.

**This is a DIFFERENT problem from Error Type 1. Adding policies to the role will NOT fix it.**

**Primary fix for connect:GetCurrentMetricData — Set agentElevatedRoleArn:**

The DevOps Agent uses a monitor role for standard operations and an elevated role for
session-sensitive operations (including Connect real-time metrics). Setting the elevated
role ARN on the association resolves this permanently:

```bash
# Step 1: Create elevated role
aws iam create-role \
  --role-name DevOpsAgentElevatedRole-AgentSpace \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "aidevops.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "aws:SourceAccount": "ACCOUNT_ID" },
        "ArnLike": { "aws:SourceArn": "arn:aws:aidevops:REGION:ACCOUNT_ID:agentspace/*" }
      }
    }]
  }'

# Step 2: Attach Connect metrics permissions to elevated role
aws iam put-role-policy \
  --role-name DevOpsAgentElevatedRole-AgentSpace \
  --policy-name ConnectMetricsAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "connect:GetCurrentMetricData",
        "connect:GetMetricData",
        "connect:GetMetricDataV2",
        "connect:GetCurrentUserData"
      ],
      "Resource": "*"
    }]
  }'

# Step 3: Update association to reference elevated role
aws aidevops update-association \
  --agent-space-id AGENTSPACE_ID \
  --association-id ASSOCIATION_ID \
  --configuration '{"aws": {
    "accountId": "ACCOUNT_ID",
    "accountType": "monitor",
    "assumableRoleArn": "EXISTING_MONITOR_ROLE_ARN",
    "agentElevatedRoleArn": "NEW_ELEVATED_ROLE_ARN"
  }}' \
  --region REGION
```

**Other fix paths (if elevated role is not applicable):**
1. **Check AWS Organizations SCPs** — Look for explicit Deny on `connect:Get*`
2. **Check session policy in AssumeRole** — Inline session policy passed at assume time
3. **Check Permission Boundaries** — Boundary must also allow the action

**Diagnostic (requires iam:SimulatePrincipalPolicy):**
```bash
aws iam simulate-principal-policy \
  --policy-source-arn "arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME" \
  --action-names "connect:GetCurrentMetricData" \
  --resource-arns "arn:aws:connect:REGION:ACCOUNT_ID:instance/INSTANCE_ID"
```

**Commonly affected:** connect:GetCurrentMetricData, connect:GetMetricData, connect:GetMetricDataV2

---

### Error Type 3: wisdom:* Not Covered by connect*

**Meaning:** The `connect*` IAM wildcard only covers the `connect:` IAM namespace.
Amazon Q in Connect, Connect AI Agents, AI Guardrails, and AI Prompts all use the
`wisdom:` namespace — completely separate from `connect:`.

**Scope of wisdom: namespace:**
- Amazon Q in Connect (formerly Wisdom) — assistants, knowledge bases, recommendations
- Connect AI Agents — ListAIAgents, GetAIAgent, ActivateAIAgent, ListAIAgentVersions
- AI Guardrails — ListAIGuardrails, GetAIGuardrail, ListAIGuardrailVersions
- AI Prompts — ListAIPrompts, GetAIPrompt, ListAIPromptVersions
- Quick Responses — ListQuickResponses, GetQuickResponse, SearchQuickResponses
- Knowledge content — ListContents, GetContent, SearchContent, GetContentSummary

**Fix — Add wisdom: read policy (no tag condition on List actions):**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "QInConnectAndConnectAIAgentsReadOnly",
    "Effect": "Allow",
    "Action": [
      "wisdom:GetAssistant", "wisdom:ListAssistants",
      "wisdom:GetKnowledgeBase", "wisdom:ListKnowledgeBases",
      "wisdom:GetRecommendations", "wisdom:QueryAssistant",
      "wisdom:SearchContent", "wisdom:ListContents",
      "wisdom:GetContentSummary",
      "wisdom:ListAIAgents", "wisdom:GetAIAgent",
      "wisdom:ListAIAgentVersions", "wisdom:GetAIAgentVersions",
      "wisdom:ListAIGuardrails", "wisdom:GetAIGuardrail",
      "wisdom:ListAIGuardrailVersions",
      "wisdom:ListAIPrompts", "wisdom:GetAIPrompt",
      "wisdom:ListAIPromptVersions", "wisdom:GetAIPromptVersions",
      "wisdom:ListQuickResponses", "wisdom:GetQuickResponse",
      "wisdom:SearchQuickResponses",
      "wisdom:ListAssistantAssociations", "wisdom:GetAssistantAssociation",
      "wisdom:GetSession"
    ],
    "Resource": "*"
  }]
}
```

**Note:** `wisdom:ListAssistants` and `wisdom:ListKnowledgeBases` must use `Resource: *`
with NO tag condition — these are list-level actions that cannot resolve resource tags.
Ref: docs.aws.amazon.com/service-authorization/latest/reference/list_q-in-connect.html

---

## IAM Namespace Reference for Connect-Adjacent Services

| Service | IAM Namespace | Covered by connect*? | Notes |
|---|---|---|---|
| Amazon Connect | connect: | ✅ Yes | All List/Describe/Get actions |
| Amazon Q in Connect / Wisdom | wisdom: | ❌ No | Separate grant required |
| Connect AI Agents | wisdom: | ❌ No | Part of wisdom: namespace |
| Connect AI Guardrails | wisdom: | ❌ No | Part of wisdom: namespace |
| Connect AI Prompts | wisdom: | ❌ No | Part of wisdom: namespace |
| Connect Outbound Campaigns V1 | connectcampaigns: | ❌ No | Separate grant required |
| Connect Outbound Campaigns V2 | connectcampaignsv2: | ❌ No | Separate grant required |
| Connect Cases | connectcases: | ❌ No | Separate grant required |
| Connect Participant (Chat) | connectparticipant: | ❌ No | Separate grant required |
| Contact Lens (analysis APIs) | connect: | ✅ Yes | Same connect: namespace |
| CloudWatch | cloudwatch: | ❌ No | Separate grant, no tag condition |
| CloudWatch Logs | logs: | ❌ No | Split List vs Get statements |
| CloudTrail (LookupEvents, DescribeTrails, GetTrailStatus) | cloudtrail: | ✅ Yes | Resolved 2026-09-10 — read-only, available under standard agent controls, no separate grant needed |
| KMS | kms: | ❌ No | Separate grant required |
| S3 | s3: | ❌ No | ListAllMyBuckets ≠ ListBucket |
| Cost Explorer | ce: | ❌ No | Separate grant required |
| Lambda | lambda: | ❌ No | ListFunctions needs Resource:* no tag |
| Kinesis | kinesis: | ❌ No | ListStreams needs Resource:* no tag |
| Lex | lex: | ❌ No | Separate grant required |

---

## CloudWatch + Logs Fix JSON (Error Type 1)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ConnectCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LogsListReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LogsContentConnectOnly",
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:StartQuery",
        "logs:GetQueryResults",
        "logs:StopQuery"
      ],
      "Resource": [
        "arn:aws:logs:*:ACCOUNT_ID:log-group:/aws/connect/*",
        "arn:aws:logs:*:ACCOUNT_ID:log-group:/aws/connect/*:*"
      ]
    }
  ]
}
```

**Replace ACCOUNT_ID with your AWS account ID before applying.**
