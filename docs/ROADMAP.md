# Roadmap — engineering work for ongoing development

The repository is an **initial functional product**, not a claim of a mature or production-ready static analyzer. Use the following tasks as real technical milestones and record your reasoning in PRs.

## P0 — correctness and regression coverage

- [ ] Detect references inside Apex comments/strings and avoid reporting them as calls. Acceptance: negative fixtures and tests for multiline comments and string literals.
- [ ] Recognize direct Apex object field reads (`Account.Health_Score__c`) without confusing unrelated names. Acceptance: positive and negative tests.
- [ ] Add two-revision scans so deleted/renamed metadata retains previous consumer evidence. Acceptance: Git branch fixtures, rename and deleted-class cases.
- [ ] Expand Flow parsing to variable assignments, metadata and dynamic subflows with explicit unsupported warnings. Acceptance: fixture coverage for three Flow versions.

## P1 — usability

- [ ] Render an interactive evidence graph with source line links and cycle controls.
- [ ] Accept manifest files through a safe local UI upload (no arbitrary-path server reads).
- [ ] Add incremental scans using content hashes and benchmark with at least 10,000 metadata files.
- [ ] Export SARIF or GitHub PR annotations for discovered review risks.

## P2 — differentiated features

- [ ] Relate Apex test classes to impacted production classes, with uncertain associations labeled explicitly.
- [ ] Compare package metadata against a changed manifest for deployment dependency completeness.
- [ ] Build an Angular standalone frontend, retaining the documented REST contracts and accessible UI.
- [ ] Add pluggable, opt-in AI explanation **after** deterministic evidence generation; keep costs, privacy and redaction controls explicit.

## Suggested first AI-assisted task

**Issue: Correct Apex reference false positives in comments and string literals.** Write failing fixtures first; choose among lexical stripping, tokenization and parser-backed approaches, explain your chosen trade-off, then commit only after `pytest` passes. This is a meaningful task that requires engineering judgment rather than simple code generation.
