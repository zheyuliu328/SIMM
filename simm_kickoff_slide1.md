# Background: Regulatory Evolution, Definition Matrix, and Problem Statement

- **Regulatory Timeline (Condensed)**  
  2008–2009 crisis exposed bilateral OTC risk; 2011–2013 BCBS-IOSCO set margin standards; 2015–2020 UMR phased rollout; 2016 onward ISDA SIMM became market standard; 2023–2025 supervision tightened on version control, data lineage, and independent validation; current baseline: **SIMM v2.8+2506 (effective 6 Dec 2025)** assessed against HKMA SPM CR-G-14 expectations.

- **Definition Matrix (Core Terms)**  
  IM = collateral for potential future exposure; SIMM = standardized sensitivity-based IM model; Delta/Vega/Curvature = primary risk inputs; Buckets & Correlations = prescribed aggregation logic; Concentration Risk = threshold-based scaling; Golden Source = authoritative trade/market data; Independent Challenger = objective recomputation engine; Traceability Matrix = requirement → test → evidence → conclusion.

- **Problems This Framework Solves**  
  (1) Regulatory defensibility gap, (2) implementation integrity risk (version/parameter/logic), (3) sensitivity transmission risk (pricing → SIMM mapping), (4) data quality and lineage risk (sample + full reconciliation to GL/sub-ledger/golden source), (5) sustainability risk (reusable controls and repeatable artifacts).

- **Bottom Line**  
  This project converts SIMM from a pure calculation process into an **audit-ready control framework** across methodology, data, and governance.