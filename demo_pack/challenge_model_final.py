"""
SIMM 2.8 Challenge Model Framework
===================================
Implementation of tiered validation for SIMM 2.8 margin calculations.

File: demo_pack/challenge_model_final.py
Version: 1.0.0
Date: 2026-02-26
Author: SIMM Challenger Team
"""

import math
from typing import Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum, auto


class ProductTier(Enum):
    """Risk tier classification based on SIMM 2.8"""
    TIER_0_EXEMPT = auto()
    TIER_1_LINEAR = auto()
    TIER_2_VANILLA = auto()
    TIER_3_CREDIT = auto()
    TIER_4_EXOTIC = auto()


@dataclass
class Trade:
    """Trade data structure"""
    product_type: str
    notional: float
    currency_pair: Optional[str] = None
    underlying_spot: Optional[float] = None
    barrier_level: Optional[float] = None
    strike: Optional[float] = None
    days_to_expiry: Optional[int] = None
    sensitivities: Optional[Dict] = None
    credit_rating: Optional[str] = None
    is_digital: bool = False
    accumulated_gain: float = 0.0
    target: float = 0.0
    trade_date: Optional[str] = None
    value_date: Optional[str] = None
    
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

EXEMPT_PRODUCTS = ['FX_CASH', 'SPOT_FX']
LINEAR_PRODUCTS = ['FX_FORWARD', 'FX_SWAP', 'NDF', 'IRS', 'BASIS_SWAP']
VANILLA_OPTIONS = ['VANILLA_OPTION', 'GOLD_OPTION', 'FX_OPTION']
EXOTIC_PRODUCTS = ['DIGITAL', 'TOUCH', 'BARRIER', 'BARRIER_KO', 'BARRIER_KI']
COMPLEX_PRODUCTS = ['TARF', 'TARF_EKI', 'TARF_CAPPED', 'RANGE_ACCRUAL']


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
        
        if 'FX' in trade.product_type:
            rw = FX_RW_G10
            threshold = FX_THRESHOLD
        else:
            rw = IR_RW.get('5Y', 0.0441)
            threshold = 35e9
        
        cr = max(1.0, math.sqrt(sum_abs_sens / threshold)) if sum_abs_sens > 0 else 1.0
        theoretical_max = sum_abs_sens * rw * cr
        
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
        
        # Circuit Breaker 2: Near barrier
        if trade.barrier_level and trade.underlying_spot:
            prox = abs(trade.underlying_spot - trade.barrier_level) / trade.barrier_level
            if prox < 0.02:
                return ChallengeResult(
                    status="MANDATORY_FALLBACK",
                    reason=f"Pin risk: {prox*100:.1f}% from barrier",
                    recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                    primary_margin=primary.margin
                )
        
        # Circuit Breaker 3: Digital discontinuity
        if trade.is_digital:
            return ChallengeResult(
                status="MANDATORY_FALLBACK",
                reason="Digital option discontinuity",
                recommendation="USE_SCHEDULE_BASED_IMMEDIATELY",
                primary_margin=primary.margin
            )
        
        return ChallengeResult(status="PASSED", reason="No exotic risks detected")


class ConservativeFloorEnforcer:
    """Tier 4: Complex structures floor enforcement"""
    
    def _schedule_margin(self, trade: Trade) -> float:
        if 'TARF' in trade.product_type:
            return trade.notional * (0.15 if 'EKI' in trade.product_type else 0.10)
        return trade.notional * 0.10
    
    def challenge(self, trade: Trade, primary: SimmResult) -> ChallengeResult:
        floor = self._schedule_margin(trade)
        
        if primary.margin < floor * 0.8:
            return ChallengeResult(
                status="CHALLENGE_FAILED",
                reason="Margin below conservative floor",
                recommendation="RAISE_TO_SCHEDULE_BASED",
                primary_margin=primary.margin,
                challenger_margin=floor
            )
        
        # TARF path dependency check
        if 'TARF' in trade.product_type and trade.target > 0:
            completion = trade.accumulated_gain / trade.target
            if completion > 0.8 and primary.vega_risk > primary.delta_risk * 0.5:
                return ChallengeResult(
                    status="WARNING",
                    reason=f"TARF {completion:.0%} complete but high vega",
                    recommendation="VERIFY_PATH_DEPENDENCY"
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
        'FX_CASH': OutOfScopeValidator,
        'SPOT_FX': OutOfScopeValidator,
        'FX_FORWARD': LinearProductChallenge,
        'FX_SWAP': LinearProductChallenge,
        'NDF': LinearProductChallenge,
        'IRS': LinearProductChallenge,
        'BASIS_SWAP': LinearProductChallenge,
        'VANILLA_OPTION': VanillaOptionChallenge,
        'GOLD_OPTION': VanillaOptionChallenge,
        'FX_OPTION': VanillaOptionChallenge,
        'DIGITAL': ExoticCircuitBreaker,
        'TOUCH': ExoticCircuitBreaker,
        'BARRIER': ExoticCircuitBreaker,
        'BARRIER_KO': ExoticCircuitBreaker,
        'BARRIER_KI': ExoticCircuitBreaker,
        'TARF': ConservativeFloorEnforcer,
        'TARF_EKI': ConservativeFloorEnforcer,
        'TARF_CAPPED': ConservativeFloorEnforcer,
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
        elif product_type in EXOTIC_PRODUCTS:
            return ProductTier.TIER_4_EXOTIC
        else:
            return ProductTier.TIER_4_EXOTIC


# Usage example
if __name__ == "__main__":
    hub = SIMM28ChallengeHub()
    
    # Example: TARF trade
    trade = Trade(
        product_type='TARF_EKI',
        notional=10_000_000,
        accumulated_gain=8_500_000,
        target=10_000_000
    )
    result = SimmResult(margin=8_000_000)
    
    challenge = hub.challenge(trade, result)
    print(f"Status: {challenge.status}")
    print(f"Reason: {challenge.reason}")
