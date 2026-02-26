"""
SIMM 2.8 Challenge Model Framework
===================================
Implementation of tiered validation for SIMM 2.8 margin calculations.
Updated based on SPEC_EN vs Excel requirements analysis.

File: demo_pack/challenge_model_final.py
Version: 1.1.0
Date: 2026-02-26
Author: SIMM Challenger Team
"""

import math
from typing import Dict, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum, auto


class ProductTier(Enum):
    """Risk tier classification based on SIMM 2.8"""
    TIER_0_EXEMPT = auto()
    TIER_1_LINEAR = auto()
    TIER_2_VANILLA = auto()
    TIER_3_CREDIT = auto()
    TIER_4_EXOTIC = auto()


class BarrierType(Enum):
    """Barrier option types"""
    KO = auto()           # Knock Out
    RKO = auto()          # Reverse Knock Out
    KI = auto()           # Knock In
    RKI = auto()          # Reverse Knock In
    KIKO = auto()         # Knock In Knock Out (双 barrier)


class PayoutType(Enum):
    """Vanilla option payout currency"""
    DOMESTIC = auto()     # 本币支付
    FOREIGN = auto()      # 外币支付


class BarrierDirection(Enum):
    """Barrier direction for vanilla barrier options"""
    UP_AND_IN = auto()
    UP_AND_OUT = auto()
    DOWN_AND_IN = auto()
    DOWN_AND_OUT = auto()


@dataclass
class Trade:
    """Trade data structure with extended attributes for Excel requirements"""
    product_type: str
    notional: float
    currency_pair: Optional[str] = None
    underlying_spot: Optional[float] = None
    barrier_level: Optional[float] = None
    barrier_type: Optional[BarrierType] = None
    strike: Optional[float] = None
    days_to_expiry: Optional[int] = None
    sensitivities: Optional[Dict] = None
    credit_rating: Optional[str] = None
    is_digital: bool = False
    is_time_option: bool = False          # Time Option (Option Dated Forward)
    accumulated_gain: float = 0.0
    target: float = 0.0
    trade_date: Optional[str] = None
    value_date: Optional[str] = None
    payout_type: PayoutType = PayoutType.DOMESTIC
    barrier_direction: Optional[BarrierDirection] = None
    has_eki: bool = False                 # TARF with Enhanced Knock-In
    is_pivot: bool = False                # Pivot TARF
    is_digital_tarf: bool = False         # Digital TARF
    is_range_accrual: bool = False        # Range Accrual flag
    lower_barrier: Optional[float] = None # Range Accrual / KIKO lower barrier
    upper_barrier: Optional[float] = None # Range Accrual / KIKO upper barrier
    arr_features: bool = False            # Alternative Reference Rate (ARR) features
    
    def __post_init__(self):
        if self.sensitivities is None:
            self.sensitivities = {}


@dataclass
class SimmResult:
    """SIMM calculation result"""
    margin: float
    delta_risk: float = 0.0
    vega_risk: float = 0.0
    curvature_risk: float = 0.0


@dataclass
class ChallengeResult:
    """Challenge validation result"""
    status: str
    reason: str = ""
    recommendation: str = ""
    primary_margin: float = 0.0
    challenger_margin: Optional[float] = None


# SIMM 2.8 Parameters
FX_RW_G10 = 0.045
FX_RW_EM = 0.08
FX_THRESHOLD = 23e9

IR_RW = {
    '2W': 0.0117, '1M': 0.0168, '3M': 0.0214, '6M': 0.0269,
    '1Y': 0.0314, '2Y': 0.0355, '5Y': 0.0441, '10Y': 0.0519,
    '15Y': 0.0555, '20Y': 0.0571, '30Y': 0.0587
}

CRQ_THRESHOLD = 0.55

# Product Classifications based on SPEC_EN and Excel requirements
EXEMPT_PRODUCTS = ['FX_CASH', 'SPOT_FX']

LINEAR_PRODUCTS = [
    'FX_FORWARD', 'FX_SWAP', 'NDF', 'IRS', 'BASIS_SWAP',
    'CROSS_CURRENCY_SWAP'  # Added: Cross Currency Swap (with ARR features)
]

VANILLA_OPTIONS = [
    'VANILLA_OPTION', 'GOLD_OPTION', 'FX_OPTION', 'SWAPTION',
    'TIME_OPTION'  # Added: Time Option (Option Dated Forward)
]

# Extended exotic products with detailed barrier types
EXOTIC_PRODUCTS = [
    'DIGITAL', 'TOUCH',
    'BARRIER', 'BARRIER_KO', 'BARRIER_RKO', 'BARRIER_KI', 'BARRIER_RKI', 'BARRIER_KIKO',
    'DIGITAL_RANGE'  # Added: Digital Range Option
]

COMPLEX_PRODUCTS = [
    'TARF', 'TARF_EKI', 'TARF_CAPPED',
    'TARF_PIVOT',       # Added: Pivot TARF
    'TARF_DIGITAL',     # Added: Digital TARF
    'RANGE_ACCRUAL'
]


def scaling_function(t_days: float) -> float:
    """SIMM 2.8 Section 11, Eq. 11.2"""
    return 0.5 * min(1.0, 14.0 / max(t_days, 1.0))


class OutOfScopeValidator:
    """Tier 0: FX Cash exemption (Section 3)"""
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        if trade.product_type in EXEMPT_PRODUCTS:
            if trade.trade_date == trade.value_date:
                return ChallengeResult(
                    status="PASSED",
                    reason="Section 3: FX Cash exempt from UMR",
                    primary_margin=0.0
                )
        return ChallengeResult(status="PASSED", reason="Requires SIMM")


class LinearProductChallenge:
    """Tier 1: Linear products validation (Section 7 & 12)"""
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        delta_sens = trade.sensitivities.get('delta', {})
        if not delta_sens:
            return ChallengeResult(
                status="CHALLENGE_FAILED",
                reason="Missing delta sensitivities",
                recommendation="CHECK_INPUT_DATA"
            )
        
        sum_abs_sens = sum(abs(v) for v in delta_sens.values())
        
        if 'FX' in trade.product_type or 'CROSS_CURRENCY' in trade.product_type:
            rw = FX_RW_G10
            threshold = FX_THRESHOLD
        else:
            rw = IR_RW.get('5Y', 0.0441)
            threshold = 35e9
        
        cr = max(1.0, math.sqrt(sum_abs_sens / threshold)) if sum_abs_sens > 0 else 1.0
        theoretical_max = sum_abs_sens * rw * cr
        
        # ARR features check
        if trade.arr_features:
            arr_adjustment = 1.02  # 2% adjustment for ARR complexity
            theoretical_max *= arr_adjustment
        
        if primary.margin > theoretical_max * 1.05:
            return ChallengeResult(
                status="CHALLENGE_FAILED",
                reason=f"Margin {primary.margin:,.0f} exceeds max {theoretical_max:,.0f}",
                recommendation="CHECK_AGGREGATION",
                primary_margin=primary.margin
            )
        
        return ChallengeResult(
            status="PASSED",
            reason="Linear aggregation valid",
            primary_margin=primary.margin
        )


class VanillaOptionChallenge:
    """Tier 2: Vanilla option validation (Section 11)"""
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        vega = trade.sensitivities.get('vega', 0)
        gamma = trade.sensitivities.get('gamma', 0)
        sigma = trade.sensitivities.get('implied_vol', 0.2)
        t_days = trade.days_to_expiry or 30
        
        # Time Option specific validation
        if trade.is_time_option:
            return self._challenge_time_option(trade, primary)
        
        if vega == 0:
            return ChallengeResult(
                status="WARNING",
                reason="Zero vega detected",
                recommendation="VERIFY_PRICING"
            )
        
        # Moneyness check
        if trade.underlying_spot and trade.strike:
            moneyness = trade.underlying_spot / trade.strike
            if abs(moneyness - 1.0) > 0.3:
                return ChallengeResult(
                    status="WARNING",
                    reason=f"Moneyness {moneyness:.2f} far from 1.0",
                    recommendation="CHECK_VANILLA_ASSUMPTION"
                )
        
        # Barrier direction check for barrier vanilla options
        if trade.barrier_direction:
            return self._challenge_barrier_vanilla(trade, primary)
        
        # Payout type check
        if trade.payout_type == PayoutType.FOREIGN:
            # Foreign payout requires additional FX risk consideration
            fx_adj = trade.sensitivities.get('fx_delta', 0)
            if abs(fx_adj) > trade.notional * 0.1:
                return ChallengeResult(
                    status="WARNING",
                    reason="High FX delta for foreign payout option",
                    recommendation="CHECK_FX_RISK"
                )
        
        # Vega-Gamma consistency
        sf = scaling_function(t_days)
        cvr_simm = sf * sigma * vega
        
        s = trade.underlying_spot or trade.strike or 100.0
        if gamma != 0:
            time_factor = min(1.0, 14.0 / t_days)
            cvr_gamma = 0.5 * gamma * (s ** 2) * (sigma ** 2) * time_factor
            
            if cvr_gamma > 0:
                ratio = cvr_simm / cvr_gamma
                if not (0.3 <= ratio <= 3.0):
                    return ChallengeResult(
                        status="CHALLENGE_FAILED",
                        reason=f"Vega-Gamma ratio {ratio:.2f} out of range",
                        recommendation="USE_SCHEDULE_BASED",
                        primary_margin=primary.margin
                    )
        
        return ChallengeResult(
            status="PASSED",
            reason="Vanilla option validation passed",
            primary_margin=primary.margin
        )
    
    def _challenge_time_option(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        """Validate Time Option (Option Dated Forward)"""
        # Time option behaves like a forward with optionality on fixing date
        delta = trade.sensitivities.get('delta', 0)
        
        if abs(delta) > trade.notional * 1.1:
            return ChallengeResult(
                status="CHALLENGE_FAILED",
                reason="Time Option delta exceeds forward-like behavior",
                recommendation="CHECK_OPTION_WINDOW"
            )
        
        return ChallengeResult(
            status="PASSED",
            reason="Time Option validation passed",
            primary_margin=primary.margin
        )
    
    def _challenge_barrier_vanilla(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        """Validate vanilla options with barrier features"""
        barrier_dist = abs(trade.underlying_spot - trade.strike) / trade.strike
        
        if trade.barrier_direction in [BarrierDirection.UP_AND_IN, BarrierDirection.DOWN_AND_IN]:
            # Knock-in: barrier must be crossed for option to activate
            if barrier_dist < 0.05:
                return ChallengeResult(
                    status="WARNING",
                    reason="Barrier too close to strike for knock-in",
                    recommendation="CHECK_BARRIER_DISTANCE"
                )
        
        elif trade.barrier_direction in [BarrierDirection.UP_AND_OUT, BarrierDirection.DOWN_AND_OUT]:
            # Knock-out: option ceases if barrier is crossed
            if barrier_dist < 0.03:
                return ChallengeResult(
                    status="WARNING",
                    reason="Barrier too close to spot for knock-out",
                    recommendation="HIGH_KNOCKOUT_RISK"
                )
        
        return ChallengeResult(
            status="PASSED",
            reason=f"Barrier vanilla option ({trade.barrier_direction.name}) validation passed",
            primary_margin=primary.margin
        )


class CreditProductChallenge:
    """Tier 3: Credit products validation (Section 8 & 9)"""
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        qualifying = ['AAA', 'AA', 'A', 'BBB', 'BBB+', 'BBB-']
        is_qualifying = trade.credit_rating in qualifying if trade.credit_rating else False
        
        distressed = ['CCC', 'CC', 'C']
        if trade.credit_rating in distressed:
            recovery = 0.40
            pd = trade.sensitivities.get('default_prob', 0.05)
            jtd = trade.notional * (1 - recovery) * pd
            
            if primary.margin < jtd * 0.5:
                return ChallengeResult(
                    status="WARNING",
                    reason=f"Margin may not capture JTD risk {jtd:,.0f}",
                    recommendation="RAISE_MARGIN",
                    primary_margin=primary.margin
                )
        
        return ChallengeResult(
            status="PASSED",
            reason="Credit validation passed",
            primary_margin=primary.margin
        )


class ExoticCircuitBreaker:
    """Tier 4: Exotic products circuit breakers (Section 11a)"""
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        # Circuit Breaker 1: CVR too high
        cvr = primary.curvature_risk
        if cvr > trade.notional * 0.50:
            return ChallengeResult(
                status="MANDATORY_FALLBACK",
                reason="CVR > 50% notional - formula unsuitable",
                recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                primary_margin=primary.margin
            )
        
        # Circuit Breaker 2: Near barrier with barrier type specifics
        if trade.barrier_level and trade.underlying_spot:
            prox = abs(trade.underlying_spot - trade.barrier_level) / trade.barrier_level
            
            # Reverse barrier (RKO/RKI) has higher pin risk
            if trade.barrier_type in [BarrierType.RKO, BarrierType.RKI]:
                threshold = 0.03  # 3% for reverse barriers
            elif trade.barrier_type == BarrierType.KIKO:
                threshold = 0.025  # 2.5% for double barriers
            else:
                threshold = 0.02  # 2% for regular barriers
            
            if prox < threshold:
                barrier_type_str = trade.barrier_type.name if trade.barrier_type else "Standard"
                return ChallengeResult(
                    status="MANDATORY_FALLBACK",
                    reason=f"{barrier_type_str} Pin risk: {prox*100:.1f}% from barrier",
                    recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                    primary_margin=primary.margin
                )
        
        # Circuit Breaker 3: Digital discontinuity
        if trade.is_digital:
            # Digital Range Option has dual discontinuity
            if trade.product_type == 'DIGITAL_RANGE':
                if trade.lower_barrier and trade.upper_barrier:
                    prox_lower = abs(trade.underlying_spot - trade.lower_barrier) / trade.lower_barrier
                    prox_upper = abs(trade.underlying_spot - trade.upper_barrier) / trade.upper_barrier
                    if prox_lower < 0.01 or prox_upper < 0.01:
                        return ChallengeResult(
                            status="MANDATORY_FALLBACK",
                            reason="Digital Range near barrier (dual discontinuity)",
                            recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                            primary_margin=primary.margin
                        )
            
            return ChallengeResult(
                status="MANDATORY_FALLBACK",
                reason="Digital option discontinuity",
                recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                primary_margin=primary.margin
            )
        
        # Circuit Breaker 4: KIKO double barrier check
        if trade.barrier_type == BarrierType.KIKO:
            if trade.lower_barrier and trade.upper_barrier:
                barrier_width = (trade.upper_barrier - trade.lower_barrier) / trade.underlying_spot
                if barrier_width < 0.05:  # Less than 5% width
                    return ChallengeResult(
                        status="MANDATORY_FALLBACK",
                        reason="KIKO barrier width too narrow (<5%)",
                        recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                        primary_margin=primary.margin
                    )
        
        return ChallengeResult(status="PASSED", reason="No exotic risks detected")


class ConservativeFloorEnforcer:
    """Tier 4: Complex structures floor enforcement with EKI distinction"""
    
    def _schedule_margin(self, trade: Trade) -> float:
        """Calculate schedule-based margin with EKI distinction"""
        base_factor = 0.10
        
        if 'TARF' in trade.product_type:
            # TARF with EKI has higher floor
            if trade.has_eki or 'EKI' in trade.product_type:
                base_factor = 0.15
            elif trade.is_digital_tarf:
                base_factor = 0.18  # Digital TARF highest floor
            elif trade.is_pivot:
                base_factor = 0.16  # Pivot TARF
            else:
                base_factor = 0.10  # Standard TARF without EKI
        
        return trade.notional * base_factor
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        floor = self._schedule_margin(trade)
        
        if primary.margin < floor * 0.8:
            eki_status = "with EKI" if (trade.has_eki or 'EKI' in trade.product_type) else "without EKI"
            return ChallengeResult(
                status="CHALLENGE_FAILED",
                reason=f"Margin below conservative floor ({eki_status})",
                recommendation="RAISE_TO_SCHEDULE_BASED",
                primary_margin=primary.margin,
                challenger_margin=floor
            )
        
        # TARF path dependency check with EKI consideration
        if 'TARF' in trade.product_type and trade.target > 0:
            completion = trade.accumulated_gain / trade.target
            
            # For TARF with EKI, allow higher vega near completion
            vega_threshold = 0.7 if (trade.has_eki or 'EKI' in trade.product_type) else 0.5
            
            if completion > 0.8 and primary.vega_risk > primary.delta_risk * vega_threshold:
                eki_note = " (EKI active)" if (trade.has_eki or 'EKI' in trade.product_type) else ""
                return ChallengeResult(
                    status="WARNING",
                    reason=f"TARF {completion:.0%} complete but high vega{eki_note}",
                    recommendation="VERIFY_PATH_DEPENDENCY"
                )
        
        # Pivot TARF specific check
        if trade.is_pivot:
            if trade.accumulated_gain > 0 and trade.accumulated_gain < trade.target * 0.5:
                # Early in pivot TARF, gamma should be controlled
                gamma = trade.sensitivities.get('gamma', 0)
                if abs(gamma) > trade.notional * 0.001:
                    return ChallengeResult(
                        status="WARNING",
                        reason="Pivot TARF high gamma in early stage",
                        recommendation="CHECK_PIVOT_STRUCTURE"
                    )
        
        return ChallengeResult(
            status="PASSED",
            reason="Above conservative floor",
            primary_margin=primary.margin,
            challenger_margin=floor
        )


class SIMM28ChallengeHub:
    """Main entry point for SIMM 2.8 Challenge Model"""
    
    REGISTRY = {
        # Tier 0: Exempt
        'FX_CASH': OutOfScopeValidator,
        'SPOT_FX': OutOfScopeValidator,
        
        # Tier 1: Linear Products
        'FX_FORWARD': LinearProductChallenge,
        'FX_SWAP': LinearProductChallenge,
        'NDF': LinearProductChallenge,
        'IRS': LinearProductChallenge,
        'BASIS_SWAP': LinearProductChallenge,
        'CROSS_CURRENCY_SWAP': LinearProductChallenge,  # Added
        
        # Tier 2: Vanilla Options
        'VANILLA_OPTION': VanillaOptionChallenge,
        'GOLD_OPTION': VanillaOptionChallenge,
        'FX_OPTION': VanillaOptionChallenge,
        'SWAPTION': VanillaOptionChallenge,
        'TIME_OPTION': VanillaOptionChallenge,  # Added: Time Option
        
        # Tier 3: Credit Products
        'CDS': CreditProductChallenge,
        'CDS_INDEX': CreditProductChallenge,
        
        # Tier 4: Exotic Products (with detailed barrier types)
        'DIGITAL': ExoticCircuitBreaker,
        'DIGITAL_RANGE': ExoticCircuitBreaker,  # Added: Digital Range Option
        'TOUCH': ExoticCircuitBreaker,
        'BARRIER': ExoticCircuitBreaker,
        'BARRIER_KO': ExoticCircuitBreaker,
        'BARRIER_RKO': ExoticCircuitBreaker,    # Added: Reverse KO
        'BARRIER_KI': ExoticCircuitBreaker,
        'BARRIER_RKI': ExoticCircuitBreaker,    # Added: Reverse KI
        'BARRIER_KIKO': ExoticCircuitBreaker,   # Added: KIKO
        
        # Tier 4: Complex Products (with EKI distinction)
        'TARF': ConservativeFloorEnforcer,
        'TARF_EKI': ConservativeFloorEnforcer,
        'TARF_CAPPED': ConservativeFloorEnforcer,
        'TARF_PIVOT': ConservativeFloorEnforcer,    # Added: Pivot TARF
        'TARF_DIGITAL': ConservativeFloorEnforcer,  # Added: Digital TARF
        'RANGE_ACCRUAL': ConservativeFloorEnforcer,
    }
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        """Execute challenge for a trade"""
        challenge_class = self.REGISTRY.get(trade.product_type)
        if not challenge_class:
            return ChallengeResult(
                status="UNKNOWN_PRODUCT",
                reason=f"No challenger for {trade.product_type}",
                primary_margin=primary.margin
            )
        
        challenger = challenge_class()
        return challenger.challenge(trade, primary)
    
    def get_tier(self, product_type: str) -> ProductTier:
        """Get risk tier for product"""
        if product_type in EXEMPT_PRODUCTS:
            return ProductTier.TIER_0_EXEMPT
        elif product_type in LINEAR_PRODUCTS:
            return ProductTier.TIER_1_LINEAR
        elif product_type in VANILLA_OPTIONS:
            return ProductTier.TIER_2_VANILLA
        elif product_type in ['CDS', 'CDS_INDEX']:
            return ProductTier.TIER_3_CREDIT
        else:
            return ProductTier.TIER_4_EXOTIC
    
    def list_supported_products(self) -> Dict[str, list]:
        """List all supported products by tier"""
        return {
            'Tier_0_Exempt': EXEMPT_PRODUCTS,
            'Tier_1_Linear': LINEAR_PRODUCTS,
            'Tier_2_Vanilla': VANILLA_OPTIONS,
            'Tier_3_Credit': ['CDS', 'CDS_INDEX'],
            'Tier_4_Exotic': EXOTIC_PRODUCTS,
            'Tier_4_Complex': COMPLEX_PRODUCTS
        }


# Usage examples
if __name__ == "__main__":
    hub = SIMM28ChallengeHub()
    
    print("=== Supported Products ===")
    products = hub.list_supported_products()
    for tier, items in products.items():
        print(f"\n{tier}: {len(items)} products")
        for p in items[:5]:
            print(f"  - {p}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")
    
    print("\n=== Example: TARF with EKI ===")
    trade = Trade(
        product_type='TARF_EKI',
        notional=10_000_000,
        accumulated_gain=8_500_000,
        target=10_000_000,
        has_eki=True
    )
    result = SimmResult(margin=8_000_000)
    challenge = hub.challenge(trade, result)
    print(f"Status: {challenge.status}")
    print(f"Reason: {challenge.reason}")
    
    print("\n=== Example: Cross Currency Swap ===")
    trade = Trade(
        product_type='CROSS_CURRENCY_SWAP',
        notional=50_000_000,
        arr_features=True
    )
    result = SimmResult(margin=2_500_000)
    challenge = hub.challenge(trade, result)
    print(f"Status: {challenge.status}")
    print(f"Reason: {challenge.reason}")
    
    print("\n=== Example: Barrier RKO ===")
    trade = Trade(
        product_type='BARRIER_RKO',
        notional=5_000_000,
        underlying_spot=100.0,
        barrier_level=102.0,
        barrier_type=BarrierType.RKO
    )
    result = SimmResult(margin=500_000, curvature_risk=100_000)
    challenge = hub.challenge(trade, result)
    print(f"Status: {challenge.status}")
    print(f"Reason: {challenge.reason}")
