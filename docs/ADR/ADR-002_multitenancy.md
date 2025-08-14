## ADR-002: Multitenancy Strategy

### Status
Accepted

### Options Considered
1. Pooled DB (single Postgres schema, tenant_id column)
2. Single-tenant DB per tenant (separate Postgres instances)

### Decision
Start with pooled DB for app config and audit headers. Enforce tenant_id scoping in queries and S3 prefixes per tenant. Allow migration to per-tenant DB for large clients or strict isolation.

### Tradeoffs
- Pooled: +cost efficient, +operationally simple, -noisy neighbor risk, -blast radius larger
- Single-tenant: +isolation, +customization, -higher cost, -operational overhead

### Implementation Notes
- S3 layout: `s3://bucket/raw/{tenant_id}/...` and `processed/{tenant_id}/...`
- IAM conditions on `s3:prefix` and `aws:ResourceTag/Tenant`
- Optional SQS queues per tenant for backpressure isolation


