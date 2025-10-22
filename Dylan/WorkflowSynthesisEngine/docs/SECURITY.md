
# Security and Privacy
- Secrets are never stored in the repository; read strictly from environment variables defined in your YAML config via `api_key_env` names.
- Validate inputs at API boundaries; transcripts must be plain text (UTF-8). Add PII redaction as a dedicated agent if required by policy.
- Use TLS/HTTPS for all remote calls and restrict egress via firewall rules for local endpoints.
