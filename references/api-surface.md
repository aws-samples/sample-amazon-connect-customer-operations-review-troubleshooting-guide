# Amazon Connect Full API Surface — Organized by Well-Architected Pillar

Last updated: 2026-07-31 | Sources: docs.aws.amazon.com/connect/latest/APIReference, docs.aws.amazon.com/amazon-q-connect/latest/APIReference, docs.aws.amazon.com/service-authorization/latest/reference/list_connect.html

---

## Well-Architected Pillar 1 — Operational Excellence

### connect: namespace
| API Action | Description | Access Level |
|---|---|---|
| ListInstances | List all Connect instances in region | List |
| DescribeInstance | Instance details, service role, status | Read |
| DescribeInstanceAttribute | Instance feature flags (Contact Lens, outbound, etc.) | Read |
| ListInstanceStorageConfigs | List storage config associations — REQUIRED FIRST to get AssociationId. Requires `--resource-type` (e.g. CALL_RECORDINGS, CHAT_TRANSCRIPTS, SCHEDULED_REPORTS, MEDIA_STREAMS, CONTACT_TRACE_RECORDS, AGENT_EVENTS) | List |
| DescribeInstanceStorageConfig | S3/KMS storage config detail — requires AssociationId (from ListInstanceStorageConfigs) **and** `--resource-type` | Read |
| ListContactFlows | List all flows by type (CONTACT_FLOW, CUSTOMER_QUEUE, etc.) | List |
| DescribeContactFlow | Full flow definition including JSON content | Read |
| ListContactFlowModules | List reusable flow modules | List |
| DescribeContactFlowModule | Full module definition and status | Read |
| DescribeContactFlowModuleAlias | Describe alias of a flow module version | Read |
| BatchGetFlowAssociation | Get flow associations in batch | Read |
| ListQueues | List queues (STANDARD and AGENT types) | List |
| DescribeQueue | Queue details, hours of operation, status | Read |
| ListRoutingProfiles | List routing profiles | List |
| DescribeRoutingProfile | Routing profile config, default queue, channels | Read |
| ListRoutingProfileQueues | Queues assigned to a routing profile | List |
| ListAgentStatuses | List agent custom and system statuses | List |
| DescribeAgentStatus | Agent status details and type | Read |
| ListHoursOfOperations | List hours of operation configs | List |
| DescribeHoursOfOperation | HoO schedule and timezone | Read |
| DescribeHoursOfOperationOverride | Temporary HoO override | Read |
| SearchContacts | Search contact records by criteria | Read |
| DescribeContact | Contact record details | Read |
| ListContactReferences | References attached to a contact | List |
| GetContactAttributes | Attributes set during a contact | Read |
| ListTaskTemplates | List task templates | List |
| GetTaskTemplate | Task template definition | Read |
| ListRules | List event/automation rules (incl. notification-trigger rules) | List |
| DescribeRule | Rule condition and action config | Read |
| GetCurrentMetricData | Real-time queue/agent metrics ⚠️ SESSION POLICY SENSITIVE | Read |
| GetMetricData | Historical metrics (legacy) ⚠️ SESSION POLICY SENSITIVE | Read |
| GetMetricDataV2 | Historical metrics V2 (preferred) ⚠️ SESSION POLICY SENSITIVE | Read |
| GetCurrentUserData | Current agent state per user ⚠️ SESSION POLICY SENSITIVE | Read |

### cloudwatch: namespace (requires separate policy)
| API Action | Description |
|---|---|
| cloudwatch:DescribeAlarms | List alarms — filter to AWS/Connect namespace |
| cloudwatch:GetMetricData | Fetch time-series metric data |
| cloudwatch:GetMetricStatistics | Statistical summaries of metrics |
| cloudwatch:ListMetrics | Enumerate available metrics |

### logs: namespace (requires separate policy)
| API Action | Description |
|---|---|
| logs:DescribeLogGroups | Find /aws/connect/<instance-alias> log groups |
| logs:FilterLogEvents | Search logs by pattern |
| logs:StartQuery / GetQueryResults | CloudWatch Logs Insights queries |
| logs:GetLogEvents | Retrieve log events from a stream |
| logs:DescribeLogStreams | List log streams in a group |

**Key CloudWatch metrics for Connect (namespace: AWS/Connect):**
- QueueSize — number of contacts in a queue (dimension: QueueName)
- LongestQueueWaitTime — longest time (seconds) a contact waited in a queue (dimension: QueueName)
- ContactFlowErrors — non-fatal flow errors (error branch taken)
- ContactFlowFatalErrors — fatal errors terminating contacts
- MissedCalls — calls not answered by an agent within 20s
- ThrottledCalls — calls rejected because calls-per-second exceeded the quota
- CallsBreachingConcurrencyQuota — calls exceeding the concurrent-calls quota
- QueueCapacityExceededError — calls rejected because the queue was full
- ConcurrentCalls / ConcurrentCallsPercentage — active calls and % of quota
- ToInstancePacketLossRate — WebRTC packet loss (dimensions: Participant, Type of Connection, Instance ID, Stream Type)

> **Not CloudWatch metrics:** agent/handle-time figures (ContactsHandled, ContactsAbandoned,
> ContactsQueued, AgentInteractionDuration, AfterContactWorkTime/ACW, average handle time) are
> **historical / real-time metrics**, not published to the AWS/Connect CloudWatch namespace and
> **cannot be alarmed on** via CloudWatch. Retrieve them with connect:GetMetricDataV2 (historical)
> or connect:GetCurrentMetricData (real-time — metric enums CONTACTS_IN_QUEUE, OLDEST_CONTACT_AGE, etc.).

---

## Well-Architected Pillar 2 — Security

### connect: namespace
| API Action | Description | Access Level |
|---|---|---|
| ListSecurityProfiles | List security profiles | List |
| DescribeSecurityProfile | Security profile permissions | Read |
| ListSecurityProfilePermissions | Granular permissions per profile | List |
| ListUsers | List users | List |
| DescribeUser | User details, security profile, routing profile | Read |
| ListUserHierarchyGroups | List agent hierarchy groups | List |
| DescribeUserHierarchyGroup | Hierarchy group details | Read |
| DescribeUserHierarchyStructure | Overall hierarchy structure | Read |
| ListAuthenticationProfiles | List SAML/auth profiles | List |
| DescribeAuthenticationProfile | SAML metadata, signing cert details | Read |
| ListLambdaFunctions | Lambda integrations on instance | List |
| ListLexBots | Lex V1 bots associated | List |
| ListBots | Lex V2 bots associated | List |
| ListApprovedOrigins | CORS approved origins | List |
| ListIntegrationAssociations | All integration types (EVENT, WISDOM, Q_IN_CONNECT, etc.) | List |
| ListSecurityKeys | Signing keys for instance | List |
| DescribeVocabulary | Custom vocabulary details | Read |
| Search custom vocabularies (no direct list-all API exists) | Read
| ListTagsForResource | Tags on Connect resources | Read |
| GetFederationToken | Generate SAML login URL for testing | Read |

### connectparticipant: namespace
| API Action | Description |
|---|---|
| connectparticipant:GetAttachment | Retrieve chat attachment |
| connectparticipant:GetAuthenticationUrl | Get auth URL for participant |
| connectparticipant:GetTranscript | Retrieve chat transcript |
| connectparticipant:DescribeView | Describe a chat view |

### amazon-q-connect (wisdom:) namespace
| API Action | Description |
|---|---|
| wisdom:ListAIGuardrails | List AI guardrails |
| wisdom:GetAIGuardrail | Guardrail config and topic filters |

### Requires additional policies
| Service | Actions | Purpose |
|---|---|---|
| cloudtrail | LookupEvents | Audit Connect API activity |
| kms | DescribeKey, ListKeys | Verify recording encryption |
| s3 | GetBucketPolicy, GetBucketEncryption | Recording/transcript storage security |
| iam | SimulatePrincipalPolicy | Test effective permissions |

---

## Well-Architected Pillar 3 — Reliability

### connect: namespace
| API Action | Description |
|---|---|
| ListTrafficDistributionGroups | List Traffic Distribution Groups (multi-region DR) |
| DescribeTrafficDistributionGroup | TDG status, linked instances |
| GetTrafficDistribution | Traffic split percentages per region |
| ListTrafficDistributionGroupUsers | Users in TDG |
| ReplicateInstance | Create replica of instance in another region |
| ListPhoneNumbers | All claimed phone numbers |
| DescribePhoneNumber | Phone number status (CLAIMED/IN_PROGRESS/FAILED) |
| ListHoursOfOperations | All HoO configs — check for coverage gaps |
| DescribeHoursOfOperation | Schedule details |
| DescribeHoursOfOperationOverride | Temporary overrides |
| ListLambdaFunctions | Lambda integrations (check for DLQ config) |
| ListAgentStatuses | Available agent states |
| DescribeAgentStatus | Agent status details |
| GetCurrentMetricData | Real-time metrics CONTACTS_IN_QUEUE, OLDEST_CONTACT_AGE ⚠️ SESSION POLICY SENSITIVE |

### cloudwatch: namespace
| Metric/Alarm | Reliability Purpose |
|---|---|
| QueueSize alarm | Alert on queue flooding (contacts in queue) |
| LongestQueueWaitTime alarm | Alert on SLA breach risk (longest wait in queue) |
| CallsBreachingConcurrencyQuota | Alert on capacity limit approach |
| ContactFlowFatalErrors | Alert on flow failures |

### lambda: namespace (requires separate policy)
| API Action | Description |
|---|---|
| lambda:GetFunction | Function config — timeout, runtime, DLQ config, tags |
| lambda:ListFunctions | Enumerate all Lambda functions in account |


---

## Well-Architected Pillar 4 — Performance Efficiency

### connect: namespace
| API Action | Description |
|---|---|
| GetMetricDataV2 | Historical metrics — AHT, abandonment, service level, occupancy ⚠️ SESSION POLICY SENSITIVE |
| GetCurrentMetricData | Real-time — agents available, contacts queued ⚠️ SESSION POLICY SENSITIVE |
| GetCurrentUserData | Per-agent current state ⚠️ SESSION POLICY SENSITIVE |
| ListRoutingProfiles | Identify routing profile bloat |
| DescribeRoutingProfile | Channel config, priority settings |
| ListRoutingProfileQueues | Queue assignments |
| ListQueues | Queue inventory |
| DescribeQueue | Queue config, max contacts |
| ListBots (Lex V2) / ListLexBots (Lex V1) | Bot associations on the instance |
| ListLambdaFunctions | Lambda performance dependencies |
| ListTaskTemplates / GetTaskTemplate | Task template efficiency |

### connectcampaignsv2: namespace
| API Action | Description |
|---|---|
| GetCampaignState | Current state: Initialized/Running/Paused/Stopped/Failed |
| GetCampaignStateBatch | Batch state for multiple campaigns |
| DescribeCampaign | Dialer config, channel subtype, schedule |
| ListCampaigns | All campaigns on instance |
| ListConnectInstanceIntegrations | Campaign integrations |

### Contact Lens (connect: namespace)
| API Action | Description |
|---|---|
| contact-lens:ListRealtimeContactAnalysisSegments | Real-time transcript/analysis segments (V1 lives in the `connect-contact-lens` namespace, NOT `connect:`) |
| connect:ListRealtimeContactAnalysisSegmentsV2 | V2 with output types (Raw/Redacted) — this one IS in the `connect:` namespace |
| connect:ListContactEvaluations | QA evaluation results |
| connect:DescribeContactEvaluation | Evaluation score details |
| connect:ListEvaluationForms | QA evaluation form templates |
| connect:DescribeEvaluationForm | Form structure and questions |

### amazon-q-connect (wisdom:) namespace
| API Action | Description |
|---|---|
| wisdom:GetRecommendations | Agent assist recommendations |
| wisdom:QueryAssistant | Manual Q in Connect query |
| wisdom:ListKnowledgeBases | Knowledge base inventory |
| wisdom:SearchContent | Content search performance |
| wisdom:SearchQuickResponses | Quick response search |

---

## Well-Architected Pillar 5 — Cost Optimization

### connect: namespace
| API Action | Description | Cost Signal |
|---|---|---|
| ListInstances | Enumerate all instances | Identify idle instances |
| DescribeInstance | Instance status | Confirm active vs idle |
| ListPhoneNumbers | All claimed numbers | DID ~$1/mo, toll-free ~$2/mo each |
| DescribePhoneNumber | Number status and association | Unclaimed but assigned = waste |
| ListUsers | User count per instance | 0 users = strong idle signal |
| ListQueues | Queue count | 0 standard queues = idle signal |
| ListContactFlows | Flow count | High count = maintenance overhead |
| ListAgentStatuses | Custom statuses | Effort indicator |

### connectcampaigns (V1): namespace
| API Action | Description |
|---|---|
| connectcampaigns:ListCampaigns | V1 campaign inventory |
| connectcampaigns:DescribeCampaign | V1 dialer config |
| connectcampaigns:GetCampaignState | Running/Paused/Stopped |

### connectcampaignsv2: namespace
| API Action | Description |
|---|---|
| connectcampaignsv2:ListCampaigns | V2 campaign inventory |
| connectcampaignsv2:DescribeCampaign | V2 dialer + channel config |
| connectcampaignsv2:GetCampaignState | Current execution state |

### Requires additional policies
| Service | Actions | Purpose |
|---|---|---|
| ce | GetCostAndUsage, GetCostForecast | Direct cost visibility |
| s3 | GetBucketLifecycleConfiguration | Recording retention costs |
| s3 | ListAllMyBuckets, GetBucketLocation | Recording bucket identification |

---

## Well-Architected Pillar 6 — Sustainability

### connect: namespace
| API Action | Description | Sustainability Signal |
|---|---|---|
| ListInstances | All instances | Consolidation candidates |
| DescribeInstanceAttribute | Feature flags | Identify over-provisioned features |
| ListContactFlows | Flow count | Stale flows = maintenance waste |
| ListQueues | Queue types | Async channels (chat/email) vs voice |
| ListBots / ListLexBots | Bot inventory | Self-service containment |
| ListIntegrationAssociations | Async channel integrations | Email/chat adoption |

### amazon-q-connect (wisdom:) namespace
| API Action | Sustainability Signal |
|---|---|
| wisdom:ListAIAgents | AI self-service agents |
| wisdom:GetAIAgent | Agent config — containment rate indicator |
| wisdom:GetRecommendations | Agent assist — reduces handle time |

### connectcampaignsv2: namespace
| API Action | Sustainability Signal |
|---|---|
| connectcampaignsv2:DescribeCampaign | Agentless campaigns = lower compute |

---

## Well-Architected Pillar 7 — Generative AI / AI-ML Lens

### amazon-q-connect (wisdom:) namespace — Full API Surface
| API Action | Description |
|---|---|
| CreateAssistant / GetAssistant / ListAssistants | Q in Connect assistant management |
| CreateKnowledgeBase / GetKnowledgeBase / ListKnowledgeBases | Knowledge base management |
| GetRecommendations | Real-time agent recommendations |
| NotifyRecommendationsReceived | Mark recommendations as received |
| QueryAssistant | Manual query against assistant |
| CreateSession / GetSession | Session lifecycle management |
| CreateContent / GetContent / ListContents | Knowledge content management |
| GetContentSummary | Content sync status check |
| SearchContent / SearchSessions | Content and session search |
| CreateQuickResponse / GetQuickResponse / ListQuickResponses | Quick response management |
| SearchQuickResponses | Quick response search |
| CreateAIAgent / GetAIAgent / ListAIAgents / UpdateAIAgent | AI agent lifecycle |
| GetAIAgentVersions / ListAIAgentVersions | AI agent version management |
| ActivateAIAgent / DeactivateAIAgent | AI agent activation state |
| CreateAIGuardrail / GetAIGuardrail / ListAIGuardrails / UpdateAIGuardrail | Guardrail management |
| CreateAIGuardrailVersion / ListAIGuardrailVersions | Guardrail versioning |
| CreateAIPrompt / GetAIPrompt / ListAIPrompts / UpdateAIPrompt | Prompt management |
| GetAIPromptVersions / ListAIPromptVersions | Prompt versioning |
| ListAssistantAssociations / GetAssistantAssociation | Assistant-to-instance associations |
| TagResource / UntagResource / ListTagsForResource | Resource tagging |

### Contact Lens (connect: namespace)
| API Action | Description |
|---|---|
| contact-lens:ListRealtimeContactAnalysisSegments | Real-time transcript segments (V1 lives in the `connect-contact-lens` namespace, NOT `connect:`) |
| connect:ListRealtimeContactAnalysisSegmentsV2 | V2 with Raw/Redacted output types — this one IS in the `connect:` namespace |
| connect:ListContactEvaluations | QA evaluation results per contact |
| connect:DescribeContactEvaluation | Evaluation score and answers |
| connect:StartContactEvaluation | Start a QA evaluation |
| connect:SubmitContactEvaluation | Submit evaluation answers |
| connect:ListEvaluationForms | QA form templates |
| connect:DescribeEvaluationForm | Form structure |
| connect:ListRules | Contact Lens automation rules |
| connect:DescribeRule | Rule condition and action config |
| connect:CreateRule / UpdateRule / DeleteRule | Rule lifecycle |

### Connect Cases (connectcases:) namespace
| API Action | Description |
|---|---|
| connectcases:ListDomains | List Cases domains |
| connectcases:GetDomain | Domain config and status |
| connectcases:SearchCases | Search cases by criteria |
| connectcases:GetCase | Individual case details |
| connectcases:ListCaseFields / GetCaseField | Case field definitions |
| connectcases:ListLayouts / GetLayout | Case layout templates |
| connectcases:ListTemplates / GetTemplate | Case templates |
| connectcases:SearchRelatedItems | Items linked to a case |

---

## Permission-Only Actions (IAM policy use only — not directly callable)

These actions exist in IAM policies but are not directly invocable API calls:

| IAM Action | Description |
|---|---|
| connect:AssociateCustomerProfilesDomain | Associate Customer Profiles domain |
| connect:DisassociateCustomerProfilesDomain | Disassociate Customer Profiles domain |
| connect:SendIntegrationEvent | Send integration events |
| connect:SendOutboundChatMessage | Send outbound chat |
| connect:SendOutboundWebNotification | Send outbound web notification |
| connect:DescribeForecastingPlanningSchedulingIntegration | FPS integration status |
| connect:StartForecastingPlanningSchedulingIntegration | Enable FPS integration |
| connect:StopForecastingPlanningSchedulingIntegration | Disable FPS integration |
