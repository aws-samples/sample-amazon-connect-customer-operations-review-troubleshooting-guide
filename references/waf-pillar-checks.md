# Well-Architected Framework Pillar Checks for Amazon Connect

Last updated: 2026-07-31

Note: "Well-Architected pillar" refers to the AWS Well-Architected Framework (WA Framework) — not WAF (Web Application Firewall).

Each check includes: what to look for, which API provides the data, and pass/fail criteria.

---

## Well-Architected Pillar 1 — Operational Excellence

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| Contact flow versioning | connect:ListContactFlows + DescribeContactFlow | Flows have consistent naming convention, IaC references in tags | No tags, no naming convention, flows named 'test' or 'copy' |
| Flow logging enabled | connect:DescribeInstanceAttribute (CONTACT_FLOW_LOGS) | Attribute = ENABLED | Attribute = DISABLED |
| CloudWatch dashboards | cloudwatch:ListDashboards | Dashboard exists with Connect metrics | No dashboards found |
| Alarms configured | cloudwatch:DescribeAlarms | Alarms on ContactsInQueue, OldestContactAge, ContactFlowFatalErrors | No alarms found |
| Multi-region awareness | connect:ListTrafficDistributionGroups | TDG exists for production instances | Production instance has no TDG |
| Consistent naming | connect:ListInstances | Alias follows pattern (env-appname-region) | Aliases like 'test123' or 'amazon-connect-<random>' |
| Custom agent statuses | connect:ListAgentStatuses | CUSTOM type statuses match business needs | Only ROUTABLE/OFFLINE system statuses |
| IaC tags | connect:ListTagsForResource | Tags: Environment, Owner, CostCenter, Application | No tags on instance or resources |

---

## Well-Architected Pillar 2 — Security

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| SAML MFA enforcement | connect:DescribeAuthenticationProfile | MFA enforced at IdP level (verify in IdP) | SAML configured without MFA verification |
| Least-privilege security profiles | connect:ListSecurityProfilePermissions | Profiles scoped to job function | Admin-level profile assigned to regular agents |
| No abandoned instances | connect:ListInstances + ListUsers + ListQueues | All instances have active users OR are tagged Dev/Test | Instance with 0 users, 0 queues, claimed phone number |
| Lambda IAM roles | connect:ListLambdaFunctions | Each Lambda ARN follows least-privilege | Lambda functions not audited |
| Approved origins locked down | connect:ListApprovedOrigins | Specific domains only, no wildcards | Wildcard origins or overly broad domains |
| CloudTrail enabled for Connect | cloudtrail:LookupEvents | Events logged for connect: API calls | No CloudTrail events found |
| KMS encryption for recordings | connect:DescribeInstanceStorageConfig + kms:DescribeKey | KMS key ID present in storage config | No KMS key — server-side S3 encryption only |
| AI guardrails configured | wisdom:ListAIGuardrails | Guardrails exist for AI-enabled instances | No guardrails on Q in Connect instances |
| Certificate expiry (SAML) | connect:DescribeAuthenticationProfile | Signing certificate valid > 30 days | Certificate expiring soon or already expired |
| Duplicate accounts | connect:ListUsers | No duplicate usernames or cross-domain users | Same user in multiple instances without justification |

---

## Well-Architected Pillar 3 — Reliability

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| DR via Traffic Distribution Group | connect:ListTrafficDistributionGroups | Production instance has active TDG | Production instance has ReplicationStatusSummaryList = [] |
| Phone number DR | connect:ListPhoneNumbers | Phone numbers documented and TDG-associated | Numbers not associated with TDG |
| Hours of operation coverage | connect:ListHoursOfOperations | HoO matches expected business hours | Only 'Basic Hours' with no custom overrides |
| Queue overflow handling | connect:DescribeContactFlow | All queues have overflow branches | Queue flow with no error/overflow handling |
| Lambda reliability | connect:ListLambdaFunctions | Functions have DLQ and retry config (verify in Lambda console) | Lambda integrated without confirmed DLQ |
| Service quota awareness | Via Support API / Connect console | Concurrent call quota monitored with alarm | No quota alarm configured |
| CloudWatch failure alarms | cloudwatch:DescribeAlarms | Alarms on ContactFlowFatalErrors, CallsBreachingConcurrencyQuota | No alarms |
| Multi-region instance replication | connect:DescribeInstance | ServiceRole includes replica region | Instance not replicated |

---

## Well-Architected Pillar 4 — Performance Efficiency

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| Routing profile hygiene | connect:ListRoutingProfiles | No test/temp routing profiles in production | Profiles named 'test', 'temp', or containing phone numbers |
| Flow count manageable | connect:ListContactFlows | < 50 flows per instance, no ARCHIVED flows in production | 80+ flows, mixed active/archived |
| Bot containment baseline | connect:ListBots + CloudWatch | Containment rate > 30% for self-service bots | No metrics, no bot configuration |
| Regional latency alignment | connect:ListInstances regions | Instances in same region as majority of agents/customers | Instance region mismatched with customer base |
| Historical metrics baseline | connect:GetMetricDataV2 | AHT, service level, abandonment tracked | Metrics API blocked |
| Campaign dialer efficiency | connectcampaignsv2:DescribeCampaign | Dialer type matches use case (Progressive/Predictive/Agentless) | Wrong dialer type for volume |
| Q in Connect containment | wisdom:GetRecommendations | Recommendations accepted rate tracked | No tracking |

---

## Well-Architected Pillar 5 — Cost Optimization

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| No idle instances | connect:ListInstances + ListUsers + ListQueues | All instances: users > 0 OR standard queues > 0 OR tagged as Dev/Test | Instance with 0 users AND 0 queues AND no Dev/Test tag |
| Phone number utilization | connect:ListPhoneNumbers | All numbers associated with active queues/flows | Number claimed but no queue/flow association |
| Stale flow cleanup | connect:ListContactFlows | No flows with 'test', 'old', 'copy', 'delete' in name | Many test/copy flows in production instance |
| Recording storage lifecycle | s3:GetBucketLifecycleConfiguration | Lifecycle policy transitions to IA/Glacier after 90 days | No lifecycle policy on recording bucket |
| Cost allocation tags | connect:ListTagsForResource | Tags: CostCenter, Environment, Application on all instances | No cost allocation tags |
| Campaign efficiency | connectcampaignsv2:DescribeCampaign | Agentless for notifications, Progressive for moderate volume | Predictive dialer for low-volume campaigns |

---

## Well-Architected Pillar 6 — Sustainability

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| Instance consolidation | connect:ListInstances | Dev instances consolidated, idle instances decommissioned | 3+ instances with 0 queues + 0 users |
| Self-service adoption | connect:ListBots + ListIntegrationAssociations | Bots associated, Q in Connect enabled | No bots, no Q in Connect integration |
| Async channel adoption | connect:ListQueues (channel types) | Chat/email queues exist alongside voice | Voice-only with no async channels |
| Agentless campaign usage | connectcampaignsv2:DescribeCampaign | Agentless used for notifications/reminders | All campaigns agent-staffed |
| Data retention policy | s3:GetBucketLifecycleConfiguration | Recordings deleted after retention period | No lifecycle = indefinite storage |
| Demand-aligned hours | connect:DescribeHoursOfOperation | HoO matches actual call volume patterns | 24/7 HoO with low off-hours volume |

---

## Well-Architected Pillar 7 — Generative AI / AI-ML Lens

| Check | API | Pass Criteria | Fail Signal |
|---|---|---|---|
| Q in Connect block published | connect:DescribeContactFlow | Flow State = ACTIVE containing Q block | Flow in DRAFT with Q block |
| Knowledge base synced | wisdom:GetKnowledgeBase | Status = ACTIVE | Status = CREATE_FAILED or SYNC_FAILED |
| AI agent activated | wisdom:ListAIAgents | Agent state = ACTIVE | Agent in DRAFT state |
| Guardrails configured | wisdom:ListAIGuardrails | At least one guardrail with topic restrictions | No guardrails on Q in Connect instances |
| VoiceID per-region domain | connect:ListIntegrationAssociations (VOICE_ID type) | Voice ID integration exists per region used | Voice ID configured in one region only |
| PII redaction | connect:DescribeInstanceAttribute (CONTACT_LENS_VOICE/CHAT) | Contact Lens enabled + PII redaction configured | Contact Lens disabled |
| Contact Lens evaluation forms | connect:ListEvaluationForms | At least one active evaluation form | No evaluation forms |
| AI prompt versioning | wisdom:ListAIPromptVersions | Prompts versioned, production uses pinned version | Using DRAFT prompt in production |
