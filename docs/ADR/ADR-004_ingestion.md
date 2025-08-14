## ADR-004: Ingestion (CSV/SFTP/API) and Validation

### Status
Accepted

### Decision
Provide pluggable adapters for CSV, SFTP, and API sources. Validate input with Pydantic; optionally add Pandera dataframe checks where appropriate.

### Flow
1. Receive file (upload or SFTP/API fetch)
2. Validate header and required fields
3. Normalize records to CDM-aligned schema
4. Emit to processing (queue) and store raw artifact

### Notes
- Strict column requirements for reconciliation: `trade_id`, `product_code`, `quantity`, `price`
- Future: add OTC FpML parsing and schema validation


