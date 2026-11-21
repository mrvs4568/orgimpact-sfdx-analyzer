# Portfolio and qualification notes

## What this project demonstrates today

- Python 3.11+ package with typed domain models, a deterministic dependency scanner, and a readable graph algorithm.
- Salesforce DX domain knowledge: Apex, triggers, LWCs, Flow XML, objects, custom fields, permission sets.
- Safe input handling and explicit false-positive/false-negative trade-offs.
- CLI, FastAPI JSON endpoints, local dashboard, regression tests, GitHub Actions CI and reproducible synthetic example.

## What it does **not** demonstrate yet

- Integration with a real Salesforce org or credential management.
- Full Salesforce metadata semantics, robust parsing of all Apex syntax, actual deployments, business users, or long-term production maintenance.
- A long-lived record of your own decisions and improvements. A newly created project does not automatically prove sustained independent software engineering work.

## Before submitting to a program seeking a substantial project of your own

1. Run the code yourself on WSL, reproduce the included tests, and explain the graph algorithm and score formula in your own words.
2. Add a real, original feature or correctness fix through a feature branch, including a failing regression test and design discussion.
3. Test against metadata you own and are permitted to use, keeping all non-public Salesforce metadata out of a public repository.
4. Record honest design decisions and limitations in PR descriptions. Do not claim real production users or capabilities the repository does not have.
5. Build a traceable history of incremental work and consider adding a short screen recording of the local demo.

**Suggested first contribution:** Add a lexer or tokenizer that strips Apex comments and string literals before detecting class calls. Write fixtures where `AccountRiskService.refresh()` is present in a comment but not real code, compare lexical accuracy, and document any limitations.
