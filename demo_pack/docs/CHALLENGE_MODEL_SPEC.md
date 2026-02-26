# SIMM 2.8 Challenge Model Technical Specification

**Version**: 1.0  
**Date**: 2026-02-26  
**Author**: SIMM Challenger Team  
**Location**: `demo_pack/docs/CHALLENGE_MODEL_SPEC.md`

---

## 1. Overview

This document specifies the SIMM 2.8 Challenge Model framework for validating margin calculations across Shacom's product portfolio.

### 1.1 Purpose

- Validate SIMM 2.8 calculations using mathematical assertions
- Detect when standard SIMM formulas fail for exotic products
- Enforce automatic fallback to Schedule-Based methods when necessary

### 1.2 Scope

| Tier | Products | Challenge Strategy |
|------|----------|-------------------|
| Tier 0 | FX Cash | Exemption (Out of Scope) |
| Tier 1 | FX Forward, IRS, Basis Swap | Linear Aggregation Check |
| Tier 2 | Vanilla Options | Vega-Gamma Consistency |
| Tier 3 | CDS, Credit Index | Rating Classification + JTD |
| Tier 4 | Barrier, Digital, TARF | Circuit Breakers |

---

## 2. Architecture

### 2.1 Core Components

```
SIMM28ChallengeHub (Main Entry)
├── ProductClassifier (Tier assignment)
├── ChallengeModelRegistry (Strategy selection)
└── DiscrepancyDetector (Threshold validation)
```

### 2.2 Challenge Flow

```
Trade Input → Product Classification → Challenge Model Selection
                                        ↓
                    Primary SIMM Result ← Challenge Execution
                                        ↓
                    Pass / Warning / Fallback Decision
```

---

## 3. Tier Specifications

### 3.1 Tier 0: Exempt Products

**Products**: FX Cash (T+0 settlement)

**SIMM 2.8 Reference**: Section 3 (Product Definitions)

**Challenge Logic**:
```python
if trade_date == value_date:
    return {"status": "EXEMPT", "margin": 0}
```

---

### 3.2 Tier 1: Linear Products

**Products**: FX Forward, FX Swap, NDF, IRS, Basis Swap

**SIMM 2.8 Reference**: Section 7 (IR), Section 12 (FX)

**Challenge Assertions**:

1. **Aggregation Boundary**: `K <= sum(|WS_k|) * 1.01`
2. **Risk Weight Verification**: RW matches product type
3. **Concentration Ratio**: CR calculation check

**Formula**:
```
WS_k = RW_k * s_k * CR_k
K = sqrt(sum(WS_k^2) + sum(sum(rho_kl * f_kl * WS_k * WS_l)))
```

---

### 3.3 Tier 2: Vanilla Options

**Products**: FX Option, Gold Option

**SIMM 2.8 Reference**: Section 11 (Curvature Risk)

**Challenge Assertions**:

1. **Scaling Function**: `SF(t) = 0.5 * min(1, 14/t)`
2. **Moneyness Check**: `|moneyness - 1| <= 0.3`
3. **Vega-Gamma Ratio**: `0.3 <= ratio <= 3.0`

**Formula**:
```
CVR = SF(t) * sigma * Vega
```

---

### 3.4 Tier 3: Credit Products

**Products**: CDS, Credit Index Tranche

**SIMM 2.8 Reference**: Section 8 (CRQ), Section 9 (CRNQ)

**Challenge Assertions**:

1. **Rating Classification**:
   - CRQ: AAA, AA, A, BBB
   - CRNQ: BB, B, CCC, NR

2. **Jump-to-Default Check**: `Margin >= 0.5 * JTD` for distressed

**Formula**:
```
JTD = Notional * (1 - Recovery) * PD
```

---

### 3.5 Tier 4: Exotic Products (Circuit Breakers)

**Products**: Barrier, Digital, Touch, TARF, Range Accrual

**SIMM 2.8 Reference**: Section 11(a) Note

**Circuit Breakers**:

| Trigger | Condition | Action |
|---------|-----------|--------|
| CVR Explosion | CVR > Notional * 50% | Mandatory Fallback |
| Pin Risk | Distance to Barrier < 2% | Mandatory Fallback |
| Digital Near Strike | Spot within 1% of Strike | Warning |
| TARF Floor | Margin < 80% of Schedule | Raise to Schedule |

---

## 4. Implementation

### 4.1 File Structure

```
demo_pack/
├── challenge_model_final.py    # Main implementation
└── docs/
    └── CHALLENGE_MODEL_SPEC.md # This document
```

### 4.2 Usage Example

```python
from challenge_model_final import SIMM28ChallengeHub, Trade, SimmResult

hub = SIMM28ChallengeHub()

trade = Trade(
    product_type='TARF_EKI',
    notional=10_000_000,
    accumulated_gain=8_000_000,
    target=10_000_000
)

result = SimmResult(margin=8_500_000)
challenge_result = hub.challenge(trade, result)

if challenge_result.status == "MANDATORY_FALLBACK":
    # Use Schedule-Based calculation
    margin = calculate_schedule_based(trade)
```

---

## 5. References

### 5.1 ISDA SIMM 2.8 Sections

- Section 3: Product Definitions
- Section 7: Interest Rate Risk
- Section 8: Credit Qualifying
- Section 9: Credit Non-Qualifying
- Section 10: Equity Risk
- Section 11: Curvature Risk
- Section 12: FX Risk
- Section C.8: Curvature for Options (Note)

### 5.2 Key Formulas

| Formula | Section | Usage |
|---------|---------|-------|
| WS_k = RW_k * s_k * CR_k | 7.2.1 | Delta Margin |
| K = sqrt(sum(WS^2) + cross_terms) | 7.2.2 | Aggregation |
| SF(t) = 0.5 * min(1, 14/t) | 11.2 | Curvature Scaling |
| CVR = SF(t) * sigma * Vega | 11.1 | Curvature Risk |

---

## 6. Validation Status

| Component | Status | Evidence |
|-----------|--------|----------|
| Tier 1-2 Logic | ✅ Implemented | Code review passed |
| Tier 3-4 Breakers | ✅ Implemented | Circuit breaker tests |
| Formula Accuracy | ✅ Verified | Against ISDA SIMM 2.8 |
| Cross-Platform | ✅ Compatible | Windows/macOS/Linux |

---

**End of Specification**
