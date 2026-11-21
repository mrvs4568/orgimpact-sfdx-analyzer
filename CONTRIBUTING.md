# Contributing

1. Create a focused feature branch and explain the problem and constraints in the PR.
2. Add a small Salesforce DX fixture that reproduces the behavior. Never commit customer metadata, tokens, or secrets.
3. Write a failing regression test before changing scanner, graph or scoring logic.
4. Run `python -m pytest -q` and the sample CLI commands from README.
5. Explain false-positive vs false-negative trade-offs; avoid claiming full Salesforce metadata semantic validation.
6. Keep the scanner read-only and all network integrations opt-in. Update ARCHITECTURE.md for data model or security changes.

A useful contribution demonstrates why the behavior is correct and what remains unsupported, not only that generated code compiles.
