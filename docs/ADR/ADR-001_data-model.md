## ADR-001: Data Model — ISDA CDM Alignment

### Status
Accepted

### Context
We need a pragmatic, extensible schema aligned to ISDA CDM for trades, positions, and lifecycle events. Full CDM is expansive; v1 requires a subset that supports reconciliation and reporting.

### Decision
- Define `Trade`, `Position`, `LifecycleEvent` Pydantic models correlating to CDM fields.
- Maintain a local schema mapping table to document correspondences.

### Mapping Table (subset)

| Local Field | ISDA CDM Correlate | Notes |
|-------------|---------------------|-------|
| trade_id | tradeIdentifier | Unique identifier used for matching |
| product_code | product | Symbol/contract code |
| account | account | Optional account reference |
| quantity | quantity | Numeric quantity |
| price | price | Trade price |
| party_internal | party | Internal party role label |
| party_external | party | External party role label |
| execution_ts | tradeDate/time | Optional execution timestamp |

### Consequences
- Easier onboarding and normalization; CDM completeness deferred
- Clear path to extend for OTC lifecycle events and crypto/FX products


