# OrgImpact — Change Impact Review

**Static analysis only — not a deploy authorization.**

- Components indexed: 12
- Dependencies indexed: 15
- Changed components: 2
- Other impacted components: 5
- High-risk changes: 0

## Changed components

### `ApexClass:AccountRiskService` — MEDIUM (67/100)

- Operation: modified
- Paths: `force-app/main/default/classes/AccountRiskService.cls`
- Direct dependents: `ApexClass:AccountHealthBatch`, `ApexClass:AccountRiskController`, `ApexTrigger:AccountRiskTrigger`
- Transitive dependents: `LWC:accountHealth`
- Risk evidence:
  - Base exposure for ApexClass: 30
  - Change operation modified: +10
  - Direct consumers (3): +24
  - Transitive consumers (1): +3
  - Score capped at 100; heuristic, not a deployment safety guarantee

### `CustomField:Account.Health_Score__c` — MEDIUM (66/100)

- Operation: modified
- Paths: `force-app/main/default/objects/Account/fields/Health_Score__c.field-meta.xml`
- Direct dependents: `LWC:accountHealth`, `PermissionSet:Account_Viewer`
- Transitive dependents: None detected
- Risk evidence:
  - Base exposure for CustomField: 40
  - Change operation modified: +10
  - Direct consumers (2): +16
  - Transitive consumers (0): +0
  - Score capped at 100; heuristic, not a deployment safety guarantee

## Impact summary

- `ApexClass:AccountHealthBatch` (depth 1; triggered by ApexClass:AccountRiskService)
- `ApexClass:AccountRiskController` (depth 1; triggered by ApexClass:AccountRiskService)
- `ApexTrigger:AccountRiskTrigger` (depth 1; triggered by ApexClass:AccountRiskService)
- `LWC:accountHealth` (depth 1; triggered by ApexClass:AccountRiskService, CustomField:Account.Health_Score__c)
- `PermissionSet:Account_Viewer` (depth 1; triggered by CustomField:Account.Health_Score__c)

## Limitations and warnings

Read-only static analysis. Dynamic dependencies, permissions and deployment validation require separate review.

- No scan warnings
