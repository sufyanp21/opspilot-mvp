## Security Notes (v1 Defaults)

### Encryption
- In transit: HTTPS/TLS is assumed via ingress or API Gateway
- At rest (prod): S3 buckets use KMS-managed keys (SSE-KMS); Postgres with encrypted storage; logs in encrypted buckets

### Identity & Access
- Principle of least privilege across IAM roles
- Scoped S3 prefixes per tenant (multi-tenant option)
- API keys/JWT-based auth recommended; RBAC roles: admin, operator, auditor (stubbed)

### Secrets
- No secrets in code; read from env vars or secret manager
- `OPENAI_API_KEY` only when `AI_ENABLED=true`

### Audit & Lineage
- Structured JSONL events with correlation IDs; optional hash-chain integrity
- Log sensitive fields in minimized/hashed form; PII redaction before persistence

### Data Retention
- Separate retention knobs for: raw uploads, processed artifacts, audit logs, exception lifecycle data
- Default short retention for raw uploads; longer for audit headers, policy-driven for reports

### Multitenancy
- Pooled vs single-tenant DBs; S3 prefixes per tenant; optional account-level isolation
- Tenant-aware encryption contexts and IAM conditions


