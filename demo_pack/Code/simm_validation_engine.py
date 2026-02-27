"""
SIMM 2.8 Validation Engine
===========================
Challenge Model for validating S&P SIMM calculations.

This is NOT a SIMM calculator - it validates S&P SIMM outputs using:
1. Mathematical constraints and bounds
2. Independent sensitivity checks
3. Reasonableness checks
4. Circuit breakers for invalid results

File: simm_validation_engine.py
Version: 1.0.0
Date: 2026-02-27
Author: SIMM Validation Team
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"


@dataclass
class SpSimmOutput:
    """S&P SIMM system output data structure"""
    # Required inputs from S&P
    trade_id: str
    product_type: str
    notional: float
    currency: str
    
    # S&P Calculated Sensitivities
    delta_sensitivities: Dict[str, float] = field(default_factory=dict)
    vega_sensitivities: Dict[str, float] = field(default_factory=dict)
    gamma_sensitivities: Dict[str, float] = field(default_factory=dict)
    
    # S&P Calculated SIMM Margins
    delta_margin: float = 0.0
    vega_margin: float = 0.0
    curvature_margin: float = 0.0
    total_margin: float = 0.0
    
    # Trade parameters for validation
    spot_price: Optional[float] = None
    strike_price: Optional[float] = None
    time_to_maturity: Optional[float] = None  # in years
    volatility: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'product_type': self.product_type,
            'notional': self.notional,
            'currency': self.currency,
            'sp_delta_margin': self.delta_margin,
            'sp_vega_margin': self.vega_margin,
            'sp_curvature_margin': self.curvature_margin,
            'sp_total_margin': self.total_margin,
            'sp_delta_sens': self.delta_sensitivities,
            'sp_vega_sens': self.vega_sensitivities
        }


@dataclass
class ValidationCheck:
    """Individual validation check result"""
    check_name: str
    status: ValidationStatus
    sp_value: float
    expected_range: Tuple[float, float]
    message: str
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'check': self.check_name,
            'status': self.status.value,
            'sp_value': self.sp_value,
            'expected_min': self.expected_range[0],
            'expected_max': self.expected_range[1],
            'message': self.message,
            'recommendation': self.recommendation
        }


@dataclass
class ValidationReport:
    """Complete validation report for a trade"""
    trade_id: str
    validation_date: str
    overall_status: ValidationStatus
    checks: List[ValidationCheck] = field(default_factory=list)
    circuit_breaker_triggered: bool = False
    fallback_recommended: bool = False
    
    def add_check(self, check: ValidationCheck):
        self.checks.append(check)
        if check.status == ValidationStatus.CIRCUIT_BREAKER:
            self.circuit_breaker_triggered = True
            self.fallback_recommended = True
    
    def get_summary(self) -> Dict:
        passed = sum(1 for c in self.checks if c.status == ValidationStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == ValidationStatus.FAIL)
        warnings = sum(1 for c in self.checks if c.status == ValidationStatus.WARNING)
        circuit_breakers = sum(1 for c in self.checks if c.status == ValidationStatus.CIRCUIT_BREAKER)
        
        return {
            'trade_id': self.trade_id,
            'overall_status': self.overall_status.value,
            'total_checks': len(self.checks),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'circuit_breakers': circuit_breakers,
            'fallback_recommended': self.fallback_recommended
        }


class SimmValidationEngine:
    """
    SIMM 2.8 Validation Engine - Challenge Model
    
    This engine validates S&P SIMM outputs using mathematical constraints
    and independent calculations. It does NOT calculate SIMM itself.
    """
    
    # ISDA SIMM 2.8 Risk Weights for validation
    FX_RW_REGULAR = 0.071
    FX_RW_HIGH_VOL = 0.180
    
    IR_RW_5Y = 0.0441
    
    # Validation tolerances
    SENSITIVITY_TOLERANCE = 0.05  # 5%
    MARGIN_TOLERANCE = 0.01  # 1%
    
    def __init__(self):
        self.validation_log = []
    
    # =============================================================================
    # TIER 1: LINEAR PRODUCTS VALIDATION
    # =============================================================================
    
    def validate_linear_product(self, sp_output: SpSimmOutput) -> List[ValidationCheck]:
        """
        Validate S&P SIMM for linear products (IRS, FX Forward, etc.)
        
        Checks:
        1. Delta sign consistency (Pay/Receive)
        2. Margin subadditivity bound
        3. Risk weight reasonableness
        """
        checks = []
        
        # Check 1: Delta Sign Consistency
        checks.append(self._check_delta_sign(sp_output))
        
        # Check 2: Subadditivity Bound (K <= sum of absolute WS)
        checks.append(self._check_subadditivity(sp_output))
        
        # Check 3: Margin vs Notional reasonableness
        checks.append(self._check_margin_notional_ratio(sp_output))
        
        return checks
    
    def _check_delta_sign(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 1: Delta Sign Consistency
        
        For IRS Pay Fixed: Delta should be negative (rates up = value down)
        For IRS Receive Fixed: Delta should be positive
        """
        total_delta = sum(sp_output.delta_sensitivities.values())
        
        # Determine expected sign based on product type
        if 'PAY_FIXED' in sp_output.product_type.upper():
            expected_sign = -1
        elif 'RECEIVE_FIXED' in sp_output.product_type.upper():
            expected_sign = 1
        else:
            # For FX forwards, sign depends on direction
            expected_sign = 0  # Neutral
        
        if expected_sign != 0:
            actual_sign = 1 if total_delta > 0 else -1 if total_delta < 0 else 0
            
            if actual_sign == expected_sign:
                return ValidationCheck(
                    check_name="Delta Sign Consistency",
                    status=ValidationStatus.PASS,
                    sp_value=total_delta,
                    expected_range=(expected_sign * abs(total_delta), expected_sign * abs(total_delta)),
                    message=f"Delta sign {actual_sign} matches expected {expected_sign}",
                    recommendation=""
                )
            else:
                return ValidationCheck(
                    check_name="Delta Sign Consistency",
                    status=ValidationStatus.FAIL,
                    sp_value=total_delta,
                    expected_range=(expected_sign * 1e9, expected_sign * 1e9),
                    message=f"Delta sign mismatch: expected {expected_sign}, got {actual_sign}",
                    recommendation="CHECK_TRADE_DIRECTION"
                )
        
        return ValidationCheck(
            check_name="Delta Sign Consistency",
            status=ValidationStatus.PASS,
            sp_value=total_delta,
            expected_range=(total_delta, total_delta),
            message="No sign constraint for this product type",
            recommendation=""
        )
    
    def _check_subadditivity(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 2: Subadditivity Bound
        
        SIMM aggregation must satisfy: K <= sum of absolute weighted sensitivities
        
        Mathematical basis: ISDA SIMM 2.8 Section 4
        """
        # Calculate theoretical max (simplified)
        # In practice, this would use actual risk weights
        sum_abs_delta = sum(abs(d) for d in sp_output.delta_sensitivities.values())
        
        # Apply approximate risk weight
        if 'FX' in sp_output.product_type.upper():
            rw = self.FX_RW_REGULAR
        else:
            rw = self.IR_RW_5Y
        
        theoretical_max = sum_abs_delta * rw * 1.5  # 1.5 factor for concentration
        
        if sp_output.delta_margin <= theoretical_max * 1.01:  # 1% tolerance
            return ValidationCheck(
                check_name="Subadditivity Bound",
                status=ValidationStatus.PASS,
                sp_value=sp_output.delta_margin,
                expected_range=(0, theoretical_max * 1.01),
                message=f"Margin {sp_output.delta_margin:,.0f} within theoretical max {theoretical_max:,.0f}",
                recommendation=""
            )
        else:
            return ValidationCheck(
                check_name="Subadditivity Bound",
                status=ValidationStatus.FAIL,
                sp_value=sp_output.delta_margin,
                expected_range=(0, theoretical_max * 1.01),
                message=f"Margin {sp_output.delta_margin:,.0f} exceeds theoretical max {theoretical_max:,.0f}",
                recommendation="CHECK_AGGREGATION_FORMULA"
            )
    
    def _check_margin_notional_ratio(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 3: Margin vs Notional Reasonableness
        
        IM should typically be 0.1% to 10% of notional for linear products
        """
        if sp_output.notional == 0:
            return ValidationCheck(
                check_name="Margin/Notional Ratio",
                status=ValidationStatus.WARNING,
                sp_value=0,
                expected_range=(0.001, 0.10),
                message="Zero notional - cannot validate ratio",
                recommendation="CHECK_NOTIONAL_AMOUNT"
            )
        
        ratio = sp_output.total_margin / abs(sp_output.notional)
        
        if 0.001 <= ratio <= 0.10:  # 0.1% to 10%
            return ValidationCheck(
                check_name="Margin/Notional Ratio",
                status=ValidationStatus.PASS,
                sp_value=ratio,
                expected_range=(0.001, 0.10),
                message=f"Ratio {ratio:.2%} within expected range",
                recommendation=""
            )
        elif ratio > 0.10:
            return ValidationCheck(
                check_name="Margin/Notional Ratio",
                status=ValidationStatus.WARNING,
                sp_value=ratio,
                expected_range=(0.001, 0.10),
                message=f"Ratio {ratio:.2%} unusually high",
                recommendation="REVIEW_RISK_WEIGHTS"
            )
        else:
            return ValidationCheck(
                check_name="Margin/Notional Ratio",
                status=ValidationStatus.PASS,
                sp_value=ratio,
                expected_range=(0.001, 0.10),
                message=f"Ratio {ratio:.2%} - low but acceptable",
                recommendation=""
            )
    
    # =============================================================================
    # TIER 2: VANILLA OPTIONS VALIDATION
    # =============================================================================
    
    def validate_vanilla_option(self, sp_output: SpSimmOutput) -> List[ValidationCheck]:
        """
        Validate S&P SIMM for vanilla options
        
        Checks:
        1. Delta range [0, 1] for calls, [-1, 0] for puts
        2. Vega-Gamma relationship
        3. Moneyness bounds
        4. CVR reasonableness
        """
        checks = []
        
        # Check 1: Delta Range
        checks.append(self._check_delta_range(sp_output))
        
        # Check 2: Vega-Gamma Consistency
        checks.append(self._check_vega_gamma_ratio(sp_output))
        
        # Check 3: CVR Bound (Curvature should not exceed notional)
        checks.append(self._check_cvr_bound(sp_output))
        
        # Check 4: ATM Moneyness Check
        if sp_output.strike_price and sp_output.spot_price:
            checks.append(self._check_moneyness(sp_output))
        
        return checks
    
    def _check_delta_range(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 1: Delta must be in valid range
        
        Call: 0 <= Delta <= 1
        Put: -1 <= Delta <= 0
        """
        total_delta = sum(sp_output.delta_sensitivities.values())
        normalized_delta = total_delta / sp_output.notional if sp_output.notional != 0 else 0
        
        # Determine if call or put
        is_call = 'CALL' in sp_output.product_type.upper()
        
        if is_call:
            expected_range = (0.0, 1.0)
            if 0 <= normalized_delta <= 1:
                status = ValidationStatus.PASS
                message = f"Call delta {normalized_delta:.2%} within [0%, 100%]"
            else:
                status = ValidationStatus.FAIL
                message = f"Call delta {normalized_delta:.2%} outside valid range [0%, 100%]"
        else:
            expected_range = (-1.0, 0.0)
            if -1 <= normalized_delta <= 0:
                status = ValidationStatus.PASS
                message = f"Put delta {normalized_delta:.2%} within [-100%, 0%]"
            else:
                status = ValidationStatus.FAIL
                message = f"Put delta {normalized_delta:.2%} outside valid range [-100%, 0%]"
        
        return ValidationCheck(
            check_name="Delta Range Validity",
            status=status,
            sp_value=normalized_delta,
            expected_range=expected_range,
            message=message,
            recommendation="" if status == ValidationStatus.PASS else "CHECK_DELTA_CALCULATION"
        )
    
    def _check_vega_gamma_ratio(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 2: Vega-Gamma Relationship
        
        For vanilla options, Gamma ≈ Vega / (S × σ × sqrt(T))
        
        Expected ratio: 0.5 to 2.0 (within tolerance)
        """
        total_vega = sum(sp_output.vega_sensitivities.values())
        total_gamma = sum(sp_output.gamma_sensitivities.values())
        
        if total_vega == 0 or total_gamma == 0:
            return ValidationCheck(
                check_name="Vega-Gamma Relationship",
                status=ValidationStatus.WARNING,
                sp_value=0,
                expected_range=(0.5, 2.0),
                message="Cannot check ratio - zero vega or gamma",
                recommendation="CHECK_SENSITIVITY_DATA"
            )
        
        # Simplified check - in practice would use full formula
        ratio = abs(total_vega / total_gamma) if total_gamma != 0 else 0
        
        # Normalize ratio (this is simplified)
        normalized_ratio = ratio / 1000  # Scale adjustment
        
        if 0.5 <= normalized_ratio <= 2.0:
            return ValidationCheck(
                check_name="Vega-Gamma Relationship",
                status=ValidationStatus.PASS,
                sp_value=normalized_ratio,
                expected_range=(0.5, 2.0),
                message=f"Ratio {normalized_ratio:.2f} within expected range",
                recommendation=""
            )
        else:
            return ValidationCheck(
                check_name="Vega-Gamma Relationship",
                status=ValidationStatus.WARNING,
                sp_value=normalized_ratio,
                expected_range=(0.5, 2.0),
                message=f"Ratio {normalized_ratio:.2f} outside typical range",
                recommendation="VERIFY_OPTION_CHARACTERISTICS"
            )
    
    def _check_cvr_bound(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 3: Curvature Risk Bound
        
        CVR should not exceed notional principal for vanilla options
        If it does, this indicates the curvature formula may be breaking down.
        """
        if sp_output.curvature_margin > abs(sp_output.notional):
            return ValidationCheck(
                check_name="CVR Bound",
                status=ValidationStatus.CIRCUIT_BREAKER,
                sp_value=sp_output.curvature_margin,
                expected_range=(0, abs(sp_output.notional)),
                message=f"CVR {sp_output.curvature_margin:,.0f} exceeds notional {sp_output.notional:,.0f}",
                recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
            )
        else:
            return ValidationCheck(
                check_name="CVR Bound",
                status=ValidationStatus.PASS,
                sp_value=sp_output.curvature_margin,
                expected_range=(0, abs(sp_output.notional)),
                message=f"CVR {sp_output.curvature_margin:,.0f} within bounds",
                recommendation=""
            )
    
    def _check_moneyness(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Check 4: Moneyness Assessment
        
        For vanilla options, check if moneyness is reasonable
        """
        moneyness = sp_output.spot_price / sp_output.strike_price
        
        if 0.7 <= moneyness <= 1.3:  # Within 30% of strike
            return ValidationCheck(
                check_name="Moneyness Assessment",
                status=ValidationStatus.PASS,
                sp_value=moneyness,
                expected_range=(0.7, 1.3),
                message=f"Moneyness {moneyness:.2f} - option reasonably close to ATM",
                recommendation=""
            )
        else:
            return ValidationCheck(
                check_name="Moneyness Assessment",
                status=ValidationStatus.WARNING,
                sp_value=moneyness,
                expected_range=(0.7, 1.3),
                message=f"Moneyness {moneyness:.2f} - far from ATM, vanilla assumption may not hold",
                recommendation="REVIEW_VANILLA_CLASSIFICATION"
            )
    
    # =============================================================================
    # TIER 4: EXOTIC CIRCUIT BREAKERS
    # =============================================================================
    
    def check_exotic_circuit_breakers(self, sp_output: SpSimmOutput) -> List[ValidationCheck]:
        """
        Circuit breakers for exotic products
        
        Triggers fallback to Schedule-based method when SIMM formula is inapplicable.
        """
        checks = []
        
        # Circuit Breaker 1: Pin Risk (Barrier proximity)
        if 'BARRIER' in sp_output.product_type.upper():
            checks.append(self._check_pin_risk(sp_output))
        
        # Circuit Breaker 2: Digital Discontinuity
        if 'DIGITAL' in sp_output.product_type.upper():
            checks.append(self._check_digital_discontinuity(sp_output))
        
        # Circuit Breaker 3: Extreme Vega
        checks.append(self._check_extreme_vega(sp_output))
        
        return checks
    
    def _check_pin_risk(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Circuit Breaker 1: Pin Risk Detection
        
        If spot is within 2% of barrier for KO/KI options,
        SIMM curvature formula breaks down.
        """
        if sp_output.spot_price and sp_output.strike_price:
            # Approximate barrier with strike for this check
            proximity = abs(sp_output.spot_price - sp_output.strike_price) / sp_output.strike_price
            
            if proximity <= 0.02:  # Within 2%
                return ValidationCheck(
                    check_name="Pin Risk (Barrier Proximity)",
                    status=ValidationStatus.CIRCUIT_BREAKER,
                    sp_value=proximity,
                    expected_range=(0.02, 1.0),
                    message=f"Spot within {proximity:.1%} of barrier - PIN RISK DETECTED",
                    recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
                )
        
        return ValidationCheck(
            check_name="Pin Risk (Barrier Proximity)",
            status=ValidationStatus.PASS,
            sp_value=0,
            expected_range=(0.02, 1.0),
            message="No pin risk detected",
            recommendation=""
        )
    
    def _check_digital_discontinuity(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Circuit Breaker 2: Digital Option Discontinuity
        
        Digital options have discontinuous payoff at strike.
        SIMM formula is invalid when spot is very close to strike.
        """
        if sp_output.spot_price and sp_output.strike_price:
            proximity = abs(sp_output.spot_price - sp_output.strike_price) / sp_output.strike_price
            
            if proximity <= 0.01:  # Within 1%
                return ValidationCheck(
                    check_name="Digital Discontinuity",
                    status=ValidationStatus.CIRCUIT_BREAKER,
                    sp_value=proximity,
                    expected_range=(0.01, 1.0),
                    message=f"Digital option spot within {proximity:.1%} of strike - DISCONTINUITY",
                    recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
                )
        
        return ValidationCheck(
            check_name="Digital Discontinuity",
            status=ValidationStatus.PASS,
            sp_value=1.0,
            expected_range=(0.01, 1.0),
            message="Digital option not near discontinuity",
            recommendation=""
        )
    
    def _check_extreme_vega(self, sp_output: SpSimmOutput) -> ValidationCheck:
        """
        Circuit Breaker 3: Extreme Vega
        
        If vega exceeds 50% of notional, this indicates explosive risk
        and SIMM formula may not be suitable.
        """
        total_vega = sum(abs(v) for v in sp_output.vega_sensitivities.values())
        vega_ratio = total_vega / sp_output.notional if sp_output.notional != 0 else 0
        
        if vega_ratio > 0.50:  # Vega > 50% of notional
            return ValidationCheck(
                check_name="Extreme Vega",
                status=ValidationStatus.CIRCUIT_BREAKER,
                sp_value=vega_ratio,
                expected_range=(0, 0.50),
                message=f"Vega {vega_ratio:.1%} of notional - explosive risk detected",
                recommendation="USE_SCHEDULE_BASED_IMMEDIATELY"
            )
        
        return ValidationCheck(
            check_name="Extreme Vega",
            status=ValidationStatus.PASS,
            sp_value=vega_ratio,
            expected_range=(0, 0.50),
            message=f"Vega {vega_ratio:.1%} within acceptable range",
            recommendation=""
        )
    
    # =============================================================================
    # MAIN VALIDATION ENTRY POINT
    # =============================================================================
    
    def validate(self, sp_output: SpSimmOutput) -> ValidationReport:
        """
        Main validation entry point
        
        Routes to appropriate validation tier based on product type.
        """
        from datetime import datetime
        
        report = ValidationReport(
            trade_id=sp_output.trade_id,
            validation_date=datetime.now().isoformat(),
            overall_status=ValidationStatus.PASS
        )
        
        # Route to appropriate tier
        product = sp_output.product_type.upper()
        
        if any(x in product for x in ['FORWARD', 'SWAP', 'NDF', 'IRS']):
            # Tier 1: Linear Products
            checks = self.validate_linear_product(sp_output)
        
        elif any(x in product for x in ['VANILLA', 'OPTION']) and 'EXOTIC' not in product:
            # Tier 2: Vanilla Options
            checks = self.validate_vanilla_option(sp_output)
        
        elif any(x in product for x in ['BARRIER', 'DIGITAL', 'TARF', 'TOUCH']):
            # Tier 4: Exotics (with circuit breakers)
            checks = self.validate_vanilla_option(sp_output)  # Base checks
            checks.extend(self.check_exotic_circuit_breakers(sp_output))  # Circuit breakers
        
        else:
            # Default: Basic checks only
            checks = self.validate_linear_product(sp_output)
        
        # Add all checks to report
        for check in checks:
            report.add_check(check)
        
        # Determine overall status
        if any(c.status == ValidationStatus.CIRCUIT_BREAKER for c in checks):
            report.overall_status = ValidationStatus.CIRCUIT_BREAKER
        elif any(c.status == ValidationStatus.FAIL for c in checks):
            report.overall_status = ValidationStatus.FAIL
        elif any(c.status == ValidationStatus.WARNING for c in checks):
            report.overall_status = ValidationStatus.WARNING
        
        return report


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SIMM VALIDATION ENGINE - Example Usage")
    print("=" * 70)
    
    # Create validation engine
    engine = SimmValidationEngine()
    
    # Example 1: Validate Linear Product (IRS)
    print("\n1. Validating Linear Product (USD IRS)")
    print("-" * 70)
    
    sp_irs_output = SpSimmOutput(
        trade_id="IRS_001",
        product_type="IRS_PAY_FIXED",
        notional=100_000_000,
        currency="USD",
        delta_sensitivities={'5Y': -45000, '10Y': -15000},
        delta_margin=2_100_000,
        vega_margin=0,
        curvature_margin=0,
        total_margin=2_100_000
    )
    
    report_irs = engine.validate(sp_irs_output)
    
    print(f"Trade ID: {report_irs.trade_id}")
    print(f"Overall Status: {report_irs.overall_status.value}")
    print("\nValidation Checks:")
    for check in report_irs.checks:
        print(f"  {check.check_name}: {check.status.value}")
        print(f"    {check.message}")
    
    # Example 2: Validate Vanilla Option
    print("\n2. Validating Vanilla Option (EUR/USD Call)")
    print("-" * 70)
    
    sp_option_output = SpSimmOutput(
        trade_id="OPT_001",
        product_type="FX_VANILLA_CALL",
        notional=10_000_000,
        currency="EUR",
        delta_sensitivities={'3M': 5_417_205},  # 54.17% delta
        vega_sensitivities={'3M': 21_370},
        gamma_sensitivities={'3M': 60_509_784},
        delta_margin=384_622,
        vega_margin=1_517,
        curvature_margin=332,
        total_margin=384_625,
        spot_price=1.0850,
        strike_price=1.0850,
        time_to_maturity=0.25,
        volatility=0.12
    )
    
    report_opt = engine.validate(sp_option_output)
    
    print(f"Trade ID: {report_opt.trade_id}")
    print(f"Overall Status: {report_opt.overall_status.value}")
    print("\nValidation Checks:")
    for check in report_opt.checks:
        print(f"  {check.check_name}: {check.status.value}")
        print(f"    {check.message}")
    
    # Example 3: Circuit Breaker Example (Digital near strike)
    print("\n3. Circuit Breaker Example (Digital Option)")
    print("-" * 70)
    
    sp_digital_output = SpSimmOutput(
        trade_id="DIG_001",
        product_type="FX_DIGITAL_CALL",
        notional=10_000_000,
        currency="EUR",
        delta_sensitivities={'3M': 5_000_000},
        vega_sensitivities={'3M': 50_000_000},  # Extreme vega
        delta_margin=2_500_000,
        vega_margin=5_000_000,
        curvature_margin=10_000_000,
        total_margin=12_500_000,
        spot_price=1.0859,  # Very close to strike
        strike_price=1.0850,
        volatility=0.12
    )
    
    report_digital = engine.validate(sp_digital_output)
    
    print(f"Trade ID: {report_digital.trade_id}")
    print(f"Overall Status: {report_digital.overall_status.value}")
    print(f"Circuit Breaker Triggered: {report_digital.circuit_breaker_triggered}")
    print(f"Fallback Recommended: {report_digital.fallback_recommended}")
    print("\nValidation Checks:")
    for check in report_digital.checks:
        if check.status == ValidationStatus.CIRCUIT_BREAKER:
            print(f"  [!] {check.check_name}: {check.status.value}")
            print(f"      {check.message}")
            print(f"      Recommendation: {check.recommendation}")
    
    print("\n" + "=" * 70)
