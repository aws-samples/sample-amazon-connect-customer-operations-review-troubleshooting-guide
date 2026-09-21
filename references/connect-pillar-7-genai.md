# Amazon Connect Operations Review — Pillar 7: Generative AI / AI-ML Lens

## Description

Assesses Amazon Connect AI capabilities: Q in Connect assistants, Connect AI Agents, AI Guardrails, AI Prompts, Contact Lens, knowledge bases, and evaluation forms. All wisdom: APIs require explicit grants — NOT covered by connect:*.

## When to Use

- Runs for instances classified as "AI-Focused"
- Phase 0 found WISDOM_ASSISTANT or Q_IN_CONNECT integration types
- User asks about AI agents, Q in Connect, guardrails, or Contact Lens

## Execution Strategy

```
Budget: 90 seconds
APIs: ~20 calls
Depends on: Phase 0 output (instance list, integrations)
Condition: Only if WISDOM_ASSISTANT or Q_IN_CONNECT found in ListIntegrationAssociations
SKIP entirely if: No AI integrations found in Phase 0
```

## Pre-Flight (5 seconds)

```
CRITICAL: wisdom:* is a SEPARATE IAM namespace from connect:*
The connect:* wildcard does NOT grant any wisdom: permissions.

Test: wisdom:ListAssistants (MaxResults=1)
  - SUCCESS → proceed with full AI assessment
  - AccessDeniedException → STOP. Mark Pillar 7 as:
    "NOT_ASSESSED: wisdom:* namespace not accessible. 
     Requires explicit wisdom:List* and wisdom:Get* grants.
     connect:* wildcard does NOT cover wisdom: APIs."
  - Do NOT attempt further wisdom:* calls if this fails.

Secondary test (Connect-side AI): 
  connect:ListRules (MaxResults=1) — for Contact Lens rules
  connect:ListEvaluationForms (MaxResults=1) — for QA forms
  These use connect: namespace and may succeed even if wisdom:* fails.
```

## Checks

### Check 7.1 — Q in Connect Assistants (15 seconds max)

**API calls**:
```
wisdom:ListAssistants (MaxResults=10)
wisdom:GetAssistant (for each, max 3)
  KEEP: Name, AssistantId, Status, Type, ServerSideEncryptionConfiguration
wisdom:ListAssistantAssociations (for each assistant)
  KEEP: AssociationType, AssociationData (KnowledgeBaseId or IntegrationArn)
```

**Checks**:
- [ ] Assistant status — ACTIVE (✅) vs CREATE_FAILED / DELETE_IN_PROGRESS (❌)
- [ ] Assistant per instance — is each AI-enabled instance linked to an assistant?
- [ ] Assistant associations — linked to knowledge base? Linked to correct instance?
- [ ] Encryption — server-side encryption configured?
- [ ] Orphaned assistants — ACTIVE but no associations

**Findings**:
- Assistant in CREATE_FAILED = 🔴 CRITICAL (AI broken, needs recreation)
- AI-enabled instance not linked to any assistant = 🟡 HIGH (integration incomplete)
- Assistant with no KB association = 🟡 HIGH (Q has nothing to recommend)

### Check 7.2 — Knowledge Bases (15 seconds max)

**API calls**:
```
wisdom:ListKnowledgeBases (MaxResults=10)
wisdom:GetKnowledgeBase (for each, max 3)
  KEEP: Name, KnowledgeBaseId, Status, KnowledgeBaseType, 
        LastContentModificationTime, SourceConfiguration
wisdom:ListContents (for first KB, MaxResults=10)
  KEEP: count + first 5 content names
wisdom:SearchContent (for first KB, query="test", MaxResults=1)
  Purpose: verify search is functional
```

**Checks**:
- [ ] KB status — ACTIVE vs CREATE_FAILED vs SYNC_FAILED
- [ ] Content freshness — LastContentModificationTime >30 days ago = stale
- [ ] Content count — 0 contents = KB exists but empty
- [ ] Source type — S3, ServiceNow, Salesforce, etc.
- [ ] Search functional — SearchContent returns results?
- [ ] Multiple KBs — segmented by topic or redundant?

**Findings**:
- KB in SYNC_FAILED = 🔴 CRITICAL (agents getting no/outdated recommendations)
- KB with 0 contents = 🔴 CRITICAL (empty knowledge base)
- KB content >30 days stale = 🟡 HIGH (potentially outdated answers)
- Search returns 0 results on generic query = 🟡 HIGH (indexing may be broken)

### Check 7.3 — AI Agents (15 seconds max)

**API calls**:
```
wisdom:ListAIAgents (MaxResults=10)
wisdom:GetAIAgent (for each, max 5)
  KEEP: Name, AIAgentId, Type, State, Configuration, Description
wisdom:ListAIAgentVersions (for each ACTIVE agent, MaxResults=5)
  KEEP: version numbers, state per version
```

**Checks**:
- [ ] AI Agent types — CUSTOMER_SELF_SERVICE vs AGENT_ASSIST (vs others)
- [ ] State — ACTIVE (deployed) vs DRAFT (not live)
- [ ] DRAFT agents in production-classified instance = risk (not finalized)
- [ ] Version pinning — production using a pinned version or latest?
- [ ] Configuration completeness — model specified? Guardrail attached?
- [ ] Multiple agents — segmented by use case or redundant?

**Findings**:
- DRAFT AI agent on production instance = 🔴 CRITICAL (not finalized, behavior may change)
- AI agent with no guardrail reference = 🟡 HIGH (unprotected AI responses)
- Agent using unpinned "latest" version = 🟡 MEDIUM (behavior changes without notice)
- 0 AI agents but Q in Connect integration exists = 🟡 HIGH (integration without implementation)

### Check 7.4 — AI Guardrails (15 seconds max)

**API calls**:
```
wisdom:ListAIGuardrails (MaxResults=10)
wisdom:GetAIGuardrail (for each, max 3)
  KEEP: Name, GuardrailId, Status, TopicPolicyConfig, 
        ContentPolicyConfig, WordPolicyConfig, SensitiveInformationPolicyConfig
wisdom:ListAIGuardrailVersions (for each, MaxResults=3)
  KEEP: version numbers, status per version
```

**Checks**:
- [ ] Guardrail exists for EVERY active AI agent — if not = CRITICAL gap
- [ ] Topic restrictions — what topics are blocked? (competitors, pricing, PII?)
- [ ] Content policy — toxicity, hate speech, violence filters enabled?
- [ ] Word policy — blocked words/phrases configured?
- [ ] PII detection — sensitive information policy configured?
- [ ] Version pinning — production on pinned version?
- [ ] Guardrail without agents — orphaned configuration

**Findings**:
- Active AI agent with NO guardrail = 🔴 CRITICAL (unprotected AI responses to customers)
- Guardrail with no topic restrictions = 🟡 HIGH (AI can discuss anything)
- Guardrail with no PII policy = 🟡 HIGH (AI may expose sensitive data)
- Guardrail version not pinned = 🟡 MEDIUM (behavior changes without notice)
- Guardrail exists but not referenced by any agent = 🟢 LOW (orphaned, cleanup)

### Check 7.5 — AI Prompts (10 seconds max)

**API calls**:
```
wisdom:ListAIPrompts (MaxResults=10)
wisdom:GetAIPrompt (for each, max 5)
  KEEP: Name, AIPromptId, Type, State, TemplateType, ModelId
wisdom:ListAIPromptVersions (for each, MaxResults=3)
  KEEP: version numbers, state per version
```

**Checks**:
- [ ] Prompt state — ACTIVE vs DRAFT
- [ ] DRAFT prompts referenced by ACTIVE agents = 🔴 CRITICAL (undefined behavior)
- [ ] Version pinning — production agents using pinned prompt version?
- [ ] Model selection — which foundation model configured? Latest available?
- [ ] Prompt type — ANSWER_GENERATION, INTENT_LABELING, QUERY_REFORMULATION, etc.
- [ ] Coverage — do all prompt types have corresponding prompts?

**Findings**:
- DRAFT prompt used by active AI agent = 🔴 CRITICAL (prompt may change anytime)
- Prompt version not pinned = 🟡 MEDIUM (prompt changes affect all agents)
- Missing prompt types (e.g., no QUERY_REFORMULATION) = 🟢 LOW (using defaults)

### Check 7.6 — Contact Lens (10 seconds max)

**Data source**: Phase 0 attributes + targeted calls

**API calls**:
```
connect:DescribeInstanceAttribute(CONTACT_LENS) — from Phase 0
connect:ListRules (MaxResults=20)
  KEEP: Name, Function (CONTACT_LENS_RULES), PublishStatus
connect:ListEvaluationForms (MaxResults=10)
  KEEP: Name, Status (ACTIVE/DRAFT)
```

**Checks**:
- [ ] Contact Lens enabled — from Phase 0 CONTACT_LENS attribute
- [ ] Contact Lens rules — automation rules configured? (auto-categorization, alerts)
- [ ] Evaluation forms — QA evaluation templates exist?
- [ ] PII redaction — Contact Lens redaction configured?
- [ ] Rules in DRAFT state — not active, not delivering value

**Findings**:
- Contact Lens enabled but 0 rules = 🟡 MEDIUM (analytics but no automation)
- Evaluation forms all in DRAFT = 🟡 MEDIUM (QA process not active)
- Contact Lens NOT enabled on AI instance = 🟡 HIGH (can't measure AI impact)

### Check 7.7 — Quick Responses (5 seconds max)

**API calls**:
```
wisdom:ListQuickResponses (MaxResults=10)
  KEEP: Name, Status, count
```

**Checks**:
- [ ] Quick responses configured — agent efficiency tool
- [ ] Count — 0 = agents typing everything manually
- [ ] Status — all ACTIVE?

**Findings**:
- 0 quick responses = 🟢 LOW (efficiency opportunity)
- Quick responses present = ✅ (agent efficiency tool deployed)

## Findings Output Format

```markdown
## Pillar 7: Generative AI / AI-ML Lens — Findings

### Assessment Coverage
- APIs attempted: {n}
- APIs succeeded: {n}
- APIs denied: {n}
- wisdom: namespace accessible: {YES / NO}
- Assessment completeness: {%}

### AI Topology
| Component | Count | Status |
|-----------|-------|--------|
| Q in Connect Assistants | {n} | {all ACTIVE / issues} |
| Knowledge Bases | {n} | {all ACTIVE / SYNC_FAILED} |
| AI Agents | {n} | {n} ACTIVE, {n} DRAFT |
| AI Guardrails | {n} | {n} attached, {n} orphaned |
| AI Prompts | {n} | {n} ACTIVE, {n} DRAFT |
| Contact Lens Rules | {n} | {n} published |
| Evaluation Forms | {n} | {n} ACTIVE |
| Quick Responses | {n} | {n} ACTIVE |

### AI Safety Matrix
| AI Agent | Guardrail Attached | Prompt Pinned | Version Pinned | State |
|----------|-------------------|---------------|----------------|-------|
| {name}   | {✅/❌}           | {✅/❌}       | {✅/❌}        | {ACTIVE/DRAFT} |

### Recommendations (Prioritized)
1. Attach guardrails to ALL active AI agents (safety-critical)
2. Pin AI agent + prompt versions for production stability
3. Move DRAFT agents/prompts to ACTIVE with proper versioning
4. Fix knowledge base sync failures
5. Enable Contact Lens on AI instances to measure AI effectiveness
6. Configure PII detection in guardrail sensitive information policy
7. Create Contact Lens rules for automated categorization
```

## Timeout Handling

```
At 70 seconds: Stop issuing new API calls.
Priority order if timeout: 7.3 → 7.4 → 7.5 → 7.1 → 7.2 → 7.6 → 7.7
(AI Agents + Guardrails + Prompts first — safety-critical)
At 80 seconds: Produce findings from data collected so far.
```

## Retry Policy

```
RETRY (once, 2-second wait): ThrottlingException
DO NOT RETRY: AccessDeniedException on wisdom:* — this is permanent, skip entire pillar

CRITICAL RULE: If wisdom:ListAssistants fails in pre-flight:
  - Do NOT attempt ANY other wisdom:* API
  - Mark ENTIRE pillar as "NOT_ASSESSED: wisdom namespace denied"
  - Still run Check 7.6 (Contact Lens) since it uses connect: namespace
  - Report the permission gap as a finding itself
```

## IAM Namespace Reminder

```
⚠️ IMPORTANT: 
- wisdom:ListAIAgents ≠ connect:ListAIAgents (there is no connect:ListAIAgents)
- ALL AI Agent/Guardrail/Prompt/KB APIs are in the wisdom: namespace
- connect:* grants ZERO access to wisdom: APIs
- Test wisdom: independently — it has its own IAM grants
- wisdom:List* on Resource:* does NOT support aws:ResourceTag conditions
```