# DerivaClear: 12-Week Pilot-Ready Roadmap

This document outlines the strategic, three-phase plan to evolve the DerivaClear MVP from a strong technical demo into a pilot-ready, enterprise-grade platform. The roadmap is designed to build a defensible business by focusing on a key market differentiator: the unified management of post-trade position and margin risk for derivatives.

**Guiding Principles:**
-   **Differentiate Day One:** Lead with our unique, integrated margin reconciliation module.
-   **Targeted Specialization:** Engineer for the specific needs of our beachhead segment (mid-tier derivatives desks).
-   **Enterprise-Grade Foundation:** Prioritize configurability, immutable audit trails, and operational safety to build trust.
-   **Explainable AI:** Use transparent, auditable AI to foster user confidence and adoption.

---

### **Investor Readiness Status Bar: `[████████░░] 80%`**

**Current State:** Defensible Product, Pilot-Ready.
This roadmap provides a compelling narrative for Series A investors and a clear value proposition for our first pilot customers. It demonstrates not only technical competence but also sharp business acumen and product-market fit.

---

### **Phase 1: Build the Differentiated, Enterprise-Grade Foundation (Weeks 1-4)**

*   **Objective:** Establish our core differentiator (margin recon) from day one, wrapped in the enterprise-grade auditability and flexibility required to earn a pilot's trust.
*   **Key Deliverables:**
    1.  **Config-Driven Rules Engine:**
        *   **Action:** Decommission hardcoded thresholds and rules.
        *   **Implementation:** Create DB-backed models (`AnomalyRuleConfig`, `RootCauseRuleConfig`) for per-product/desk rules. Build a secure `/admin/rules` API and a simple UI for CRUD operations. Services will **hot-reload** this configuration, allowing rule changes without restarts.
    2.  **Immutable Audit & Lineage (Pulled Forward):**
        *   **Action:** Make comprehensive, immutable logging a core, non-negotiable feature.
        *   **Implementation:** Every critical action (login, rule change, ingestion, recon run, resolution) **must** write to an immutable `AuditLog` table *before* the action is considered complete.
    3.  **'Day 1' Margin Reconciliation MVP (NEW):**
        *   **Action:** Build the foundational module for margin reconciliation.
        *   **Implementation:** Implement a service to reconcile client-calculated margin vs. clearinghouse statements (e.g., CME SPAN files), establishing our unique value proposition from the first demo.
    4.  **Derivatives-Focused Ingestion (ENHANCED):**
        *   **Action:** Design the ingestion engine with a specialized focus.
        *   **Implementation:** The idempotent ingestion engine will have first-class support for a key derivatives format (e.g., exchange trade capture reports, simplified FpML), making our specialization tangible.
    5.  **Scoped & Auditable Auto-Resolution:**
        *   **Action:** Implement the `apply-suggestion` endpoint with strict safety controls.
        *   **Implementation:** Logic will **only auto-apply for pre-defined, low-risk classes**. All other suggestions remain "recommended-only." Every action will have a clear rollback path and be fully audited.

---

### **Phase 2: Establish Explainable, Risk-Aware AI (Weeks 5-10)**

*   **Objective:** Apply our transparent AI framework not just to reconciliations, but directly to our core differentiator—margin and risk—and solve the real-world problem of messy data.
*   **Key Deliverables:**
    1.  **Break & Margin Prediction Model:**
        *   **Action:** Train the initial LightGBM break prediction model.
        *   **Implementation & Data Strategy:** The initial model will be trained on **weak labels bootstrapped from our rules engine**, enriched with human-in-the-loop feedback from pilots. Performance is secondary to explainability.
    2.  **Explainable AI for Trade & Margin Risk (ENHANCED):**
        *   **Action:** Build the API and UI to expose model explainability.
        *   **Implementation:** The `/exceptions/{id}/explain` SHAP endpoint will support both trade breaks and margin anomalies (e.g., "Margin difference is high because: Notional increased 20%, Volatility Surface shifted").
    3.  **Flexible Data Transformation Layer (NEW):**
        *   **Action:** Create a dedicated, UI-configurable service for data transformation.
        *   **Implementation:** This service will handle real-world data cleanup (standardizing IDs, formats, etc.), de-risking pilot integration.
    4.  **Refined Terminology ("Insights/Trends"):**
        *   **Action:** Adjust UI and API language to manage customer expectations.
        *   **Implementation:** All instances of "Benchmarking" will be renamed to **"Performance Insights"** or **"Operational Trends"** until cross-client data is available.

---

### **Phase 3: "Solution-in-a-Box" Pilot Launch (Weeks 11-12)**

*   **Objective:** Package our differentiated platform into a solution that is easy to sell, easy to onboard, and speaks directly to the needs of our target customers.
*   **Key Deliverables:**
    1.  **"Solution-in-a-Box" Onboarding (ENHANCED):**
        *   **Action:** Create pre-built templates for our beachhead segment.
        *   **Implementation:** The admin UI will feature templates like "FCM Futures Reconciliation" that pre-configure data sources, mappings, and rules for rapid deployment.
    2.  **Differentiated GTM Narrative & Package (ENHANCED):**
        *   **Action:** Align all sales, marketing, and compliance materials with our core value proposition.
        *   **Implementation:** The lead message is: **"DerivaClear provides a single, AI-powered view of your post-trade position and risk,"** positioning us as a smarter risk management tool.
    3.  **Comprehensive Data Exports & Security Posture:**
        *   **Action:** Finalize easy-export features and frame our SOC-2 readiness.
        *   **Implementation:** Ensure all data (recon results, exceptions, audit logs) is easily exportable. Frame SOC-2 documentation around building a platform for mission-critical financial workflows.
