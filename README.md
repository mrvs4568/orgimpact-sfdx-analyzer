# OrgImpact

**Read-only Salesforce DX metadata change-impact analysis, with a CLI, dependency graph, explainable risk model, and local browser dashboard.**

> Early, functional v0.1 engineering project. Not a Salesforce deployment or security certification tool. This code is independently built as a portfolio project; it is not extracted from a client, employer, or production Salesforce org.

## Problem

An apparently small field, Flow, or Apex change may affect many downstream Salesforce components. Traditional file diffs show *what changed*, not *which static consumers could be affected*. OrgImpact indexes a local Salesforce DX source tree, traces static dependencies with evidence, and creates a review report you can attach to a PR.

## What works today

- Scans **Apex classes and triggers**, **Flow XML**, **Lightning Web Components**, **objects**, **custom fields**, and **permission sets** from a local Salesforce DX project.
- Builds an evidence-backed dependency graph for Apex calls, Apex `new`, SOQL object references, trigger objects, LWC Apex and schema imports, Flow object/subflow references, and permission-set object/field access.
- Traces **direct and transitive consumers** of changed components using a reverse graph traversal.
- Scores risk from component type, operation (add/modify/delete), and observed consumer counts. **The scoring is a transparent heuristic, not an official Salesforce rule.**
- Accepts a checked-in change manifest or **committed Git changes** from a merge base.
- Produces machine-readable JSON and a Markdown change-review artifact.
- Serves a local browser workbench and JSON API (FastAPI). The API cannot select arbitrary filesystem roots; the operator chooses the root when starting the server.
- Warns when XML is invalid, unsupported changes are encountered, or a component is missing.
- Includes a fully synthetic Salesforce DX sample plus CI and automated tests.

## Quick start

Requires Python 3.11 or newer. No Salesforce account, credentials, AI key, or external API required.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
```

View a sample source inventory:

```bash
orgimpact scan --root examples/sfdx-project
```

Create a Markdown review of the included sample modifications:

```bash
orgimpact analyze --root examples/sfdx-project \
  --changes examples/change-manifest.json \
  --format md --output review.md
```

Open the interactive UI:

```bash
orgimpact serve --root examples/sfdx-project
# Open http://127.0.0.1:8000
```

Run it against **your own local SFDX project**:

```bash
orgimpact analyze --root /path/to/your-sfdx-project \
  --changes /path/to/changes.json --format json --output report.json
```

### Git-aware analysis

Once the project exists in a Git repository, inspect *committed changes* between the common ancestor of `main` and `HEAD`:

```bash
orgimpact analyze --root /path/to/your-sfdx-project --git-base main
```

**Important:** `--git-base` does not include uncommitted or untracked work. It uses `git diff --no-renames --name-status -z main...HEAD`. For local edits, create a manifest or commit your changes on a feature branch first.

### Manifest format

The JSON file is an array of relative paths rooted at `--root`:

```json
[
  {"path": "force-app/main/default/objects/Account/fields/Health_Score__c.field-meta.xml", "status": "modified"},
  {"path": "force-app/main/default/classes/AccountRiskService.cls", "status": "modified"}
]
```

Allowed statuses: `added`, `modified`, `deleted`. Deleted items may no longer exist in the snapshot; their name and type still come from the file path, but historical dependencies **cannot be recovered without scanning the previous revision**.

## What the score means

| Component | Baseline points |
| --- | ---: |
| LWC | 20 |
| Apex class | 30 |
| Custom field | 40 |
| Permission set | 45 |
| Flow | 50 |
| Custom object | 55 |
| Apex trigger | 60 |

Add 5 for new, 10 for modified, 25 for deleted, 8 per direct consumer, and 3 per additional transitive consumer; capped at 100. Low: 0–39, Medium: 40–69, High: 70–100. Scores help prioritize **human review**; they do not predict deployment success, authorization, security, or runtime failures.

## Architecture

```text
SFDX source directory → scanner → component index + evidence edges
                                           ↓
change manifest / committed Git diff → change resolver → reverse graph walk
                                           ↓
                                   explainable risk model
                                           ↓
                          JSON report / Markdown / local web UI
```

Core analysis uses only Python's standard library. Web UI uses FastAPI + static HTML/CSS/JS, with no browser-side third-party dependencies. All analysis is performed locally; no Salesforce OAuth or secrets are needed. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Scope and limitations

The analyzer uses **conservative static pattern extraction**. It can miss dynamic Apex calls, generic references, managed package prefixes, Flow expression references, profiles/permission inheritance, and metadata outside the listed types. It may also flag a lexically matching code reference in a comment or string. File-level analysis is not equivalent to running Apex tests or evaluating Salesforce org configuration. The bundled sample is synthetic, not evidence of actual Salesforce org behavior.

- Large/unsafe files are skipped, with a warning; XML DTD/entity declarations are rejected.
- Paths supplied in the API are treated as metadata identifiers, not filesystem reads.
- The web server binds to `127.0.0.1` by default. Do **not** expose it publicly without an authentication/reverse-proxy/security review.
- The project does not modify source files or Salesforce org data.

## Developing the project with an AI coding assistant

The project intentionally has meaningful next steps. Good engineering tasks to work through independently: resolving false-positive references, preserving historical dependency graphs across deletions, richer Flow parsing, efficient incremental scanning, graph visualization, test-coverage correlation, and deployment-package analysis. Use issues with acceptance criteria, review AI-generated patches critically, and write tests that expose trade-offs before implementation.

Start with [`docs/ROADMAP.md`](docs/ROADMAP.md). Contributions should include regression tests and an explanation of the design decision. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Project ownership and license

This repository is prepared as original project source for the repository owner. No open-source license is included; **all rights are reserved until the owner chooses a license**. The example data and names are fictional. Do not add your employer's/client's metadata, tokens, credentials, or customer details to the public repository.

### Example: higher-risk object change

The alternate fixture demonstrates transitive impact through a Flow's subflow:

```bash
orgimpact analyze --root examples/sfdx-project \
  --changes examples/high-impact-manifest.json --format md
```
