## ADR-003: AI Usage and Guardrails

### Status
Accepted

### Decision
Use AI strictly for summaries/explanations. Never auto-change books/records. All AI outputs are attributable and reviewable; a human approval step is mandatory.

### Guardrails
- PII redaction and data minimization before prompt construction
- Prompt hardening with schema-of-thought, explicit constraints, and refusal paths
- Regulator Mode: verbose provenance and references in outputs

### Failure Modes
- If AI unavailable or disabled (`AI_ENABLED=false`), system falls back to deterministic, rule-based narratives


