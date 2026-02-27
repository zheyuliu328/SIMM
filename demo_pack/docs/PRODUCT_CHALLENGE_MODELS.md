# Product-Level Challenge Models for SIMM Validation

## Document Information
- **Version**: 1.0.0
- **Date**: 2026-02-27
- **Purpose**: Product-specific challenge models for S&P SIMM validation
- **Scope**: ShacomBank Product List v1.31

---

## Executive Summary

This document defines **product-specific challenge models** for validating S&P SIMM calculations. Each product type has unique characteristics that require tailored validation approaches.

**Validation Principle**: "Test of 1 per risk type per product feature"

---

## 1. Interest Rate Swaps (IRS)

### 1.1 Product Characteristics
- **Linear product** - Delta risk only
- **Pay Fixed** = Negative duration (rates up, value down)
- **Receive Fixed** = Positive duration
- **PV01** = Sensitivity to 1bp parallel shift

### 1.2 Challenge Model: DV01 Recomputation

#### Mathematical Basis
```
DV01 = -Notional × Modified Duration × 0.0001
```

For a par swap:
- Modified Duration ≈ (1 - (1+r)^-n) / r
- Where r = swap rate, n = years to maturity

#### Validation Steps

**Step 1: Independent DV01 Calculation**
```python
# Challenger Model (Deloitte)
duration = calculate_swap_duration(fixed_rate, maturity)
challenger_dv01 = -notional * duration * 0.0001

# S&P Output
sp_dv01 = extract_from_sp_system(trade_id)

# Reconcile
variance = (challenger_dv01 - sp_dv01) / sp_dv01
assert abs(variance) < 0.05  # 5% tolerance
```

**Step 2: Sign Verification**
```python
if pay_fixed:
    assert sp_dv01 < 0  # Must be negative
else:
    assert sp_dv01 > 0  # Must be positive
```

**Step 3: Curve Consistency Check**
```python
# Verify S&P uses same curve for valuation and SIMM
valuation_curve = sp.get_valuation_curve(trade_id)
simm_curve = sp.get_simm_curve(trade_id)
assert valuation_curve == simm_curve
```

### 1.3 ARR Feature Validation

For Swaps with Alternative Reference Rate (ARR):

| ARR Type | Additional Check | Risk Weight Adjustment |
|----------|------------------|----------------------|
| ARR Average | Average of RFR over period | +2% |
| ARR Index | Compounded RFR index | +2% |
| Term ARR | Term rate based on RFR | +2% |

**Validation**: 
```python
if trade.has_arr_feature:
    expected_rw = base_rw * 1.02
    actual_rw = sp.get_risk_weight(trade_id)
    assert abs(actual_rw - expected_rw) < 0.001
```

### 1.4 Test Case: USD IRS Pay Fixed 5Y

| Parameter | Value |
|-----------|-------|
| Notional | USD 100,000,000 |
| Maturity | 5 Years |
| Fixed Rate | 4.5% |
| Pay/Receive | Pay Fixed |

**Expected Results**:
- DV01 ≈ -45,000 USD
- Duration ≈ 4.5 years
- SIMM Margin ≈ 2,000,000 USD (approx)

**Validation**:
```python
def validate_irs(trade):
    # 1. Calculate expected DV01
    expected_dv01 = calculate_irs_dv01(
        notional=100_000_000,
        rate=0.045,
        maturity=5,
        pay_fixed=True
    )
    
    # 2. Compare with S&P
    sp_dv01 = trade.sp_delta_sensitivities['5Y']
    variance = abs(expected_dv01 - sp_dv01) / abs(sp_dv01)
    
    # 3. Check
    if variance > 0.05:
        return FAIL(f"DV01 variance {variance:.1%} exceeds 5% tolerance")
    
    # 4. Sign check
    if sp_dv01 > 0:
        return FAIL("Pay Fixed IRS should have negative DV01")
    
    return PASS
```

---

## 2. FX Forwards

### 2.1 Product Characteristics
- **Linear product** - Linear payoff in spot
- **Delta = Notional** (in foreign currency terms)
- **No Vega** (no optionality)

### 2.2 Challenge Model: Forward Delta Verification

#### Mathematical Basis
```
FX Delta = Notional (foreign currency)

For Forward Price:
F = S × exp((r_domestic - r_foreign) × T)
```

#### Validation Steps

**Step 1: Delta Equals Notional**
```python
# Challenger expects delta = notional
expected_delta = trade.notional  # 10,000,000 EUR

# S&P output
sp_delta = trade.sp_delta_sensitivities['EUR']

# For Buy EUR position, delta should equal notional
variance = abs(sp_delta - expected_delta) / expected_delta
assert variance < 0.01  # 1% tolerance for rounding
```

**Step 2: Forward Rate Validation**
```python
# Calculate theoretical forward rate
r_usd = 0.045  # USD rate
r_eur = 0.025  # EUR rate
T = 0.25  # 3 months

expected_fwd = spot * math.exp((r_usd - r_eur) * T)
sp_fwd = sp.get_forward_rate(trade_id)

assert abs(expected_fwd - sp_fwd) < 0.0001  # 1 pip tolerance
```

**Step 3: No Vega Confirmation**
```python
# FX Forward should have zero vega
sp_vega = trade.sp_vega_sensitivities.get('EUR', 0)
assert sp_vega == 0, "FX Forward should not have vega risk"
```

### 2.3 Test Case: EUR/USD Forward 3M

| Parameter | Value |
|-----------|-------|
| Notional | EUR 10,000,000 |
| Spot | 1.0850 |
| USD Rate | 4.5% |
| EUR Rate | 2.5% |
| Tenor | 3M |
| Position | Buy EUR / Sell USD |

**Expected Results**:
- FX Delta: +10,000,000 EUR
- Forward Rate: 1.0904
- Vega: 0
- SIMM Margin: ~710,000 USD

**Validation**:
```python
def validate_fx_forward(trade):
    # 1. Delta should equal notional
    expected_delta = trade.notional
    sp_delta = trade.sp_delta_sensitivities['EUR']
    
    if abs(sp_delta - expected_delta) / expected_delta > 0.01:
        return FAIL("FX Delta does not match notional")
    
    # 2. No vega
    if trade.sp_vega_margin != 0:
        return FAIL("FX Forward should have zero vega margin")
    
    # 3. Forward rate check
    expected_fwd = calculate_forward_rate(
        spot=trade.spot,
        r_domestic=trade.usd_rate,
        r_foreign=trade.eur_rate,
        T=trade.tenor
    )
    
    sp_fwd = trade.sp_forward_rate
    if abs(sp_fwd - expected_fwd) > 0.0001:
        return WARNING("Forward rate variance > 1 pip")
    
    return PASS
```

---

## 3. FX Vanilla Options

### 3.1 Product Characteristics
- **Non-linear** - Curvature risk applies
- **Greeks**: Delta, Gamma, Vega, Theta
- **Moneyness**: ATM, ITM, OTM

### 3.2 Challenge Model: Black-Scholes Verification

#### Mathematical Basis (Black-Scholes)
```
Call Delta = exp(-qT) × N(d1)
where d1 = [ln(S/K) + (r-q+σ²/2)T] / (σ√T)

Vega = S × exp(-qT) × √T × n(d1) × 0.01

Gamma = exp(-qT) × n(d1) / (S × σ × √T)
```

#### Validation Steps

**Step 1: Independent Greek Calculation**
```python
# Challenger Model (Deloitte Black-Scholes)
option = BlackScholesOption(
    S=trade.spot,
    K=trade.strike,
    T=trade.time_to_expiry,
    sigma=trade.volatility,
    r=trade.domestic_rate,
    q=trade.foreign_rate
)

challenger_delta = option.delta()
challenger_vega = option.vega()
challenger_gamma = option.gamma()
```

**Step 2: Sensitivity Reconciliation**
```python
# Compare with S&P
sp_delta = trade.sp_delta_sensitivities['EUR']
sp_vega = trade.sp_vega_sensitivities['EUR']

# Delta variance
delta_var = abs(challenger_delta - sp_delta) / sp_delta
assert delta_var < 0.05  # 5% tolerance

# Vega variance
vega_var = abs(challenger_vega - sp_vega) / sp_vega
assert vega_var < 0.05  # 5% tolerance
```

**Step 3: Vega-Gamma Relationship**
```python
# Theoretical relationship check
if challenger_gamma > 0:
    theoretical_vega = (challenger_gamma * 
                       trade.spot**2 * 
                       trade.volatility * 
                       math.sqrt(trade.time_to_expiry))
    
    ratio = sp_vega / theoretical_vega
    assert 0.5 <= ratio <= 2.0, "Vega-Gamma relationship abnormal"
```

**Step 4: Delta Range Check**
```python
# For call options, delta must be in [0, 1]
delta_ratio = sp_delta / trade.notional
if trade.option_type == 'CALL':
    assert 0 <= delta_ratio <= 1
else:
    assert -1 <= delta_ratio <= 0
```

### 3.3 Moneyness-Specific Validation

| Moneyness | Delta Expected | Vega Expected | Challenge Focus |
|-----------|---------------|---------------|-----------------|
| ATM (S=K) | ~50% | Maximum | Vega accuracy |
| ITM (S>K) | >50% | Lower | Delta accuracy |
| OTM (S<K) | <50% | Lower | Gamma accuracy |

### 3.4 Test Cases

#### Test Case 3a: EUR/USD Call ATM
```python
trade = {
    'notional': 10_000_000,
    'spot': 1.0850,
    'strike': 1.0850,  # ATM
    'volatility': 0.12,
    'time_to_expiry': 0.25
}

# Expected (Challenger)
expected_delta = 5_417_205  # 54.17%
expected_vega = 21_370
expected_gamma = 60_509_784
```

#### Test Case 3b: EUR/USD Call ITM
```python
trade = {
    'strike': 1.0500,  # ITM
    # ... other params same
}

expected_delta = 7_406_749  # 74.07%
expected_vega = 17_300
```

#### Test Case 3c: EUR/USD Call OTM
```python
trade = {
    'strike': 1.1200,  # OTM
    # ... other params same
}

expected_delta = 3_366_632  # 33.67%
expected_vega = 19_727
```

---

## 4. Barrier Options

### 4.1 Product Characteristics
- **Discontinuous payoff** at barrier
- **Pin risk** when spot near barrier
- **Types**: KO, KI, RKO, RKI, KIKO

### 4.2 Challenge Model: Pin Risk Detection

#### Circuit Breaker Trigger
```python
def check_pin_risk(trade):
    """
    Trigger circuit breaker if spot too close to barrier
    """
    proximity = abs(trade.spot - trade.barrier) / trade.barrier
    
    # KO/KI: 2% threshold
    # RKO/RKI: 3% threshold
    # KIKO: 2.5% threshold
    
    if 'RKO' in trade.product_type or 'RKI' in trade.product_type:
        threshold = 0.03
    elif 'KIKO' in trade.product_type:
        threshold = 0.025
    else:
        threshold = 0.02
    
    if proximity <= threshold:
        return CIRCUIT_BREAKER(
            f"Pin risk: spot {proximity:.1%} from barrier",
            recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
        )
    
    return PASS
```

#### Challenge: Vega Explosiveness
```python
def check_vega_explosiveness(trade):
    """
    Vega should not exceed reasonable bounds for barrier options
    """
    total_vega = sum(trade.sp_vega_sensitivities.values())
    vega_ratio = total_vega / trade.notional
    
    if vega_ratio > 0.50:  # Vega > 50% of notional
        return CIRCUIT_BREAKER(
            f"Vega {vega_ratio:.1%} exceeds 50% of notional",
            recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
        )
    
    return PASS
```

### 4.3 Validation Steps

1. **Barrier Distance Check** - Must be > 2% (or 3% for RKO/RKI)
2. **Vega Bound Check** - Must be < 50% of notional
3. **Digital Discontinuity** - If digital component, check strike proximity
4. **Fallback**: If any check fails, recommend Schedule-based method

---

## 5. TARF (Target Accrual Redemption Forward)

### 5.1 Product Characteristics
- **Path-dependent** - Accumulated gain affects payoff
- **Target feature** - Redemption when target reached
- **Knock-out** at target

### 5.2 Challenge Model: Target Behavior Validation

#### Behavioral Validation
```python
def validate_tarf_behavior(trade):
    """
    Validate TARF behaves correctly as target is approached
    """
    accumulated = trade.accumulated_gain
    target = trade.target_profit
    completion = accumulated / target
    
    # Check 1: Near target, vega should decrease
    if completion > 0.8:  # 80% of target reached
        vega_ratio = trade.sp_vega_margin / trade.sp_delta_margin
        
        if vega_ratio > 0.5:
            return WARNING(
                f"TARF at {completion:.1%} target but vega still high",
                "Should behave more like forward"
            )
    
    # Check 2: Target completion sanity
    if accumulated > target * 1.1:
        return FAIL("Accumulated gain exceeds target - trade should have knocked out")
    
    return PASS
```

#### EKI (Enhanced Knock-In) Validation
```python
def validate_tarf_eki(trade):
    """
    TARF with EKI has additional knock-in barrier
    """
    if not trade.has_eki:
        return PASS
    
    # EKI barrier should be monitored
    if trade.spot < trade.eki_barrier:
        return CIRCUIT_BREAKER(
            "EKI barrier breached",
            recommendation="RECALCULATE_WITH_KNOCK_IN"
        )
    
    return PASS
```

---

## 6. Digital Options

### 6.1 Product Characteristics
- **Discontinuous payoff** at strike
- **Dirac delta** at strike price
- **European/American** style

### 6.2 Challenge Model: Discontinuity Detection

#### Circuit Breaker: Strike Proximity
```python
def check_digital_discontinuity(trade):
    """
    Digital options have undefined delta at strike
    SIMM formula breaks down near strike
    """
    proximity = abs(trade.spot - trade.strike) / trade.strike
    
    if proximity <= 0.01:  # Within 1% of strike
        return CIRCUIT_BREAKER(
            f"Digital option {proximity:.1%} from strike",
            recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
        )
    
    # If far from strike, can treat as vanilla
    if proximity > 0.05:  # > 5% from strike
        return PASS("Digital far from strike - vanilla approximation acceptable")
    
    return WARNING("Digital option approaching discontinuity")
```

---

## 7. Cross-Currency Swaps (CCS)

### 7.1 Product Characteristics
- **IR + FX risk** combined
- **Basis spread** between floating legs
- **Notional exchange** at maturity

### 7.2 Challenge Model: Dual Risk Validation

#### Step 1: IR Component Validation
```python
# Same as IRS validation for each leg
usd_leg_dv01 = validate_irs_leg(trade.usd_leg)
eur_leg_dv01 = validate_irs_leg(trade.eur_leg)
```

#### Step 2: FX Component Validation
```python
# Notional exchange at maturity creates FX risk
fx_exposure = trade.final_exchange_notional
expected_fx_delta = fx_exposure  # In foreign currency

sp_fx_delta = trade.sp_fx_delta
assert abs(sp_fx_delta - expected_fx_delta) / expected_fx_delta < 0.01
```

#### Step 3: Basis Spread Validation
```python
# Verify basis curve used correctly
basis_curve = sp.get_basis_curve(trade.ccy_pair)
expected_basis = market_data.get_basis_spread(trade.tenor)

assert abs(basis_curve - expected_basis) < 0.0001
```

---

## 8. Validation Summary Matrix

| Product | Primary Check | Secondary Check | Circuit Breaker |
|---------|--------------|-----------------|-----------------|
| IRS | DV01 Recomputation | Sign Verification | N/A |
| FX Forward | Delta = Notional | Forward Rate | N/A |
| FX Option (ATM) | Black-Scholes Delta/Vega | Vega-Gamma Ratio | N/A |
| FX Option (ITM/OTM) | Delta Range [0,1] | Moneyness | N/A |
| Barrier | Barrier Proximity | Vega Bound | Pin Risk >2% |
| TARF | Target Completion | Vega Decay | EKI Breach |
| Digital | Strike Proximity | N/A | <1% from strike |
| CCS | Dual Leg Validation | Basis Curve | N/A |

---

## 9. Deliverables

### 9.1 For Each Product Test
1. **Trade Parameters** - Input to S&P
2. **S&P Output** - Sensitivities + Margins
3. **Challenger Calculation** - Independent verification
4. **Variance Analysis** - Comparison results
5. **Validation Status** - PASS/FAIL/CIRCUIT_BREAKER

### 9.2 Validation Report Template
```json
{
  "trade_id": "IRS_001",
  "product_type": "IRS_PAY_FIXED",
  "validation_date": "2026-02-27",
  "checks": [
    {
      "check": "DV01_Recomputation",
      "sp_value": -45000,
      "challenger_value": -44850,
      "variance_pct": -0.33,
      "status": "PASS"
    },
    {
      "check": "Delta_Sign",
      "sp_value": -45000,
      "expected": "negative",
      "status": "PASS"
    }
  ],
  "overall_status": "PASS"
}
```

---

## Document Control
- **Version**: 1.0.0
- **Author**: SIMM Validation Team
- **Reviewed by**: [TBD]
- **Approved by**: [TBD]
