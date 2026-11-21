# OrgImpact — Change Impact Review

**Static analysis only — not a deploy authorization.**

- Components indexed: 12
- Dependencies indexed: 15
- Changed components: 1
- Other impacted components: 9
- High-risk changes: 1

## Changed components

### `CustomObject:Account` — HIGH (100/100)

- Operation: modified
- Paths: `force-app/main/default/objects/Account/Account.object-meta.xml`
- Direct dependents: `ApexClass:AccountRiskService`, `ApexTrigger:AccountRiskTrigger`, `Flow:Account_Review`, `LWC:accountHealth`, `LWC:reviewQueue`, `PermissionSet:Account_Viewer`
- Transitive dependents: `ApexClass:AccountHealthBatch`, `ApexClass:AccountRiskController`, `Flow:Account_Followup`
- Risk evidence:
  - Base exposure for CustomObject: 55
  - Change operation modified: +10
  - Direct consumers (6): +48
  - Transitive consumers (3): +9
  - Score capped at 100; heuristic, not a deployment safety guarantee

## Impact summary

- `ApexClass:AccountHealthBatch` (depth 2; triggered by CustomObject:Account)
- `ApexClass:AccountRiskController` (depth 2; triggered by CustomObject:Account)
- `ApexClass:AccountRiskService` (depth 1; triggered by CustomObject:Account)
- `ApexTrigger:AccountRiskTrigger` (depth 1; triggered by CustomObject:Account)
- `Flow:Account_Followup` (depth 2; triggered by CustomObject:Account)
- `Flow:Account_Review` (depth 1; triggered by CustomObject:Account)
- `LWC:accountHealth` (depth 1; triggered by CustomObject:Account)
- `LWC:reviewQueue` (depth 1; triggered by CustomObject:Account)
- `PermissionSet:Account_Viewer` (depth 1; triggered by CustomObject:Account)

## Limitations and warnings

Read-only static analysis. Dynamic dependencies, permissions and deployment validation require separate review.

- No scan warnings
