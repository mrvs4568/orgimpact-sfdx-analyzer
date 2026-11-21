# Architecture and design decisions

## Threat model

- Input is local, potentially untrusted Salesforce DX metadata from a repository.
- Scanner never executes Apex, Flow, JavaScript, or XML-supplied commands.
- XML DTD/entity declarations are refused and each source file has a 2 MiB cap. The file count is capped at 20,000. Symbolic-link files are not followed.
- Git integration uses `subprocess.run([...])` without shell interpretation and enforces a timeout. A Git repository supplied by the user is trusted for the purposes of invoking Git; running Git hooks is not part of scanning.
- Browser/API routes cannot change the filesystem scan root, and data is not sent to Salesforce or external AI services. Do not bind to a public network without authentication and threat review.
- The exported report includes metadata names and paths; review it before sharing outside your company.

## Dependency direction

A reference `A → B` means component A **depends on** component B. To assess a changed component B, traverse incoming edges, not outgoing edges. A breadth-first search records the shortest detected path from B to each consumer. The implementation returns both direct and indirect consumers and deduplicates consumer components before scoring.

## Evidence model

Each reference stores `source`, `target`, `relation`, `path`, and optional `line`. Text pattern matches include their source line. XML references carry a file path but no line in v0.1. References are included only when the target component exists in the currently scanned directory, avoiding implied or phantom graph nodes.

## Data flow

1. `scanner.component_for_path` identifies supported metadata components by Salesforce DX path conventions.
2. `scanner.scan` builds the component index, reads bounded files, extracts references and collects warnings.
3. `analyzer.parse_changes` strictly validates the change manifest; `git_changes` is an alternative source from Git diff.
4. `analyzer.analyze` groups multiple files per logical component, traverses reverse edges, and calculates a documented heuristic risk score.
5. `render.markdown_report`, `cli.main`, and `web.create_app` expose analysis without changing the indexed project.

## Known accuracy trade-offs

- Regex-based Apex parsing gives high speed and zero Salesforce dependencies, but does not build an AST; lexical false positives are possible, especially in comments, strings and ambiguous names.
- XML parser checks only specific well-known Flow/PermissionSet structures. Extending support should begin with fixture tests for each metadata type.
- Deleted components have no snapshot content. Historical edges require a two-revision graph comparison; treating deleted files as risk-free would be incorrect.
- Risk scoring is a prioritization heuristic. A score of 0 or no reported consumers does not mean a change is safe.

## Suggested hardening

Use fixtures from multiple API versions, reference a genuine grammar or parser for Apex, add a cached content-hash index, bound graph traversal on extremely dense metadata, and inspect Git submodules/symlinks for additional scanner exposure. Add native `sfdx-project.json` packageDirs discovery in place of the v0.1 path heuristics.
