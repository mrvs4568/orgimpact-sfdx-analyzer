# Security notes

OrgImpact is intended for local development. It reads Salesforce DX metadata on the filesystem and produces dependency reports. It does not require Salesforce OAuth, API keys, or credentials.

- Do not run the dashboard on a public address or expose it through a tunnel without adding authentication and conducting a security review.
- Do not upload real client or employer metadata to public GitHub. Metadata may include sensitive names, logic, and business context even without credentials.
- Keep `--root` restricted to an intended local DX project directory. The scanner limits file size/count and rejects XML DTDs but is not a general sandbox.
- Review JSON/Markdown reports before distributing them.
- Prefer a dedicated security issue without exploit details or contact the repository owner privately to report a vulnerability.
