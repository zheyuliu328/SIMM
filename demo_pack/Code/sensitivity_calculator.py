"""
Risk Sensitivity Calculator
============================
Independent calculation of risk sensitivities for model validation.

This module provides challenger calculations for:
- Delta (DV01, FX Delta, Credit Spread Delta)
- Vega (Volatility sensitivity)
- Gamma (Curvature/Second-order sensitivity)

These calculations are used to validate sensitivities provided by S&P system.

File: sensitivity_calculator.py
Version: 1.0.0
Date: 2026-02-27
Author: SIMM Validation Team
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass
class OptionParams:
    """Option parameters for sensitivity calculation"""
    spot: float
    strike: float
    time_to_expiry: float  # in years
    volatility: float
    risk_free_rate: float
    dividend_yield: float = 0.0
    notional: float = 1.0


class BlackScholesCalculator:
    """
    Black-Scholes option pricing and Greeks calculator.
    
    Used for independent validation of option sensitivities from S&P system.
    """
    
    @staticmethod
    def d1(params: OptionParams) -> float:
        """Calculate d1 parameter"""
        s, k, t, r, q, sigma = params.spot, params.strike, params.time_to_expiry, params.risk_free_rate, params.dividend_yield, params.volatility
        return (math.log(s / k) + (r - q + 0.5 * sigma ** 2) * t) / (sigma * math.sqrt(t))
    
    @staticmethod
    def d2(params: OptionParams) -> float:
        """Calculate d2 parameter"""
        return BlackScholesCalculator.d1(params) - params.volatility * math.sqrt(params.time_to_expiry)
    
    @staticmethod
    def price(params: OptionParams, option_type: OptionType) -> float:
        """Calculate option price using Black-Scholes formula"""
        d1 = BlackScholesCalculator.d1(params)
        d2 = BlackScholesCalculator.d2(params)
        s, k, t, r, q = params.spot, params.strike, params.time_to_expiry, params.risk_free_rate, params.dividend_yield
        
        if option_type == OptionType.CALL:
            price = s * math.exp(-q * t) * BlackScholesCalculator._N(d1) - k * math.exp(-r * t) * BlackScholesCalculator._N(d2)
        else:
            price = k * math.exp(-r * t) * BlackScholesCalculator._N(-d2) - s * math.exp(-q * t) * BlackScholesCalculator._N(-d1)
        
        return price * params.notional
    
    @staticmethod
    def delta(params: OptionParams, option_type: OptionType) -> float:
        """
        Calculate option Delta
        
        Delta = ∂V/∂S
        
        For FX options, this gives the FX Delta sensitivity.
        """
        d1 = BlackScholesCalculator.d1(params)
        t, q = params.time_to_expiry, params.dividend_yield
        
        if option_type == OptionType.CALL:
            delta = math.exp(-q * t) * BlackScholesCalculator._N(d1)
        else:
            delta = -math.exp(-q * t) * BlackScholesCalculator._N(-d1)
        
        return delta * params.notional
    
    @staticmethod
    def gamma(params: OptionParams) -> float:
        """
        Calculate option Gamma
        
        Gamma = ∂²V/∂S²
        
        This is the second-order sensitivity to spot price.
        """
        d1 = BlackScholesCalculator.d1(params)
        s, t, q, sigma = params.spot, params.time_to_expiry, params.dividend_yield, params.volatility
        
        gamma = math.exp(-q * t) * BlackScholesCalculator._n(d1) / (s * sigma * math.sqrt(t))
        return gamma * params.notional
    
    @staticmethod
    def vega(params: OptionParams) -> float:
        """
        Calculate option Vega
        
        Vega = ∂V/∂σ
        
        Sensitivity to volatility. Reported per 1% change in volatility.
        """
        d1 = BlackScholesCalculator.d1(params)
        s, t, q = params.spot, params.time_to_expiry, params.dividend_yield
        
        # Vega per 1% volatility change
        vega = s * math.exp(-q * t) * math.sqrt(t) * BlackScholesCalculator._n(d1) * 0.01
        return vega * params.notional
    
    @staticmethod
    def theta(params: OptionParams, option_type: OptionType) -> float:
        """Calculate option Theta (time decay)"""
        d1 = BlackScholesCalculator.d1(params)
        d2 = BlackScholesCalculator.d2(params)
        s, k, t, r, q, sigma = params.spot, params.strike, params.time_to_expiry, params.risk_free_rate, params.dividend_yield, params.volatility
        
        term1 = -s * math.exp(-q * t) * BlackScholesCalculator._n(d1) * sigma / (2 * math.sqrt(t))
        
        if option_type == OptionType.CALL:
            term2 = q * s * math.exp(-q * t) * BlackScholesCalculator._N(d1)
            term3 = -r * k * math.exp(-r * t) * BlackScholesCalculator._N(d2)
        else:
            term2 = -q * s * math.exp(-q * t) * BlackScholesCalculator._N(-d1)
            term3 = r * k * math.exp(-r * t) * BlackScholesCalculator._N(-d2)
        
        return (term1 + term2 + term3) * params.notional
    
    @staticmethod
    def rho(params: OptionParams, option_type: OptionType) -> float:
        """Calculate option Rho (sensitivity to interest rate)"""
        d2 = BlackScholesCalculator.d2(params)
        k, t, r = params.strike, params.time_to_expiry, params.risk_free_rate
        
        if option_type == OptionType.CALL:
            rho = k * t * math.exp(-r * t) * BlackScholesCalculator._N(d2) * 0.01
        else:
            rho = -k * t * math.exp(-r * t) * BlackScholesCalculator._N(-d2) * 0.01
        
        return rho * params.notional
    
    @staticmethod
    def _N(x: float) -> float:
        """Cumulative distribution function of standard normal"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def _n(x: float) -> float:
        """Probability density function of standard normal"""
        return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


class IRSensitivityCalculator:
    """
    Interest Rate Sensitivity Calculator
    
    Calculates DV01 and other IR sensitivities for swaps and bonds.
    """
    
    @staticmethod
    def calculate_dv01(notional: float, duration: float, 
                      bump_size: float = 0.0001) -> float:
        """
        Calculate DV01 (Dollar Value of 01)
        
        DV01 = Notional × Duration × 0.0001
        
        Args:
            notional: Trade notional amount
            duration: Modified duration in years
            bump_size: Rate bump size (default 1bp = 0.0001)
        
        Returns:
            DV01 sensitivity value
        """
        return -notional * duration * bump_size
    
    @staticmethod
    def calculate_pv01(notional: float, maturity_years: float,
                      coupon_rate: float, yield_rate: float) -> float:
        """
        Calculate PV01 (Present Value of 01) for a bond
        
        This is the change in present value for a 1bp change in yield.
        """
        # Simplified PV01 calculation
        # Full implementation would require bootstrapping yield curves
        duration = maturity_years / (1 + yield_rate)  # Simplified duration
        return -notional * duration * 0.0001
    
    @staticmethod
    def calculate_swap_dv01(notional: float, fixed_rate: float,
                           maturity_years: float, pay_fixed: bool = True) -> float:
        """
        Calculate DV01 for an Interest Rate Swap
        
        For a par swap, DV01 ≈ Notional × PV01(bond with coupon = swap rate)
        
        Args:
            notional: Swap notional
            fixed_rate: Fixed leg rate
            maturity_years: Swap maturity
            pay_fixed: True if paying fixed, False if receiving fixed
        
        Returns:
            DV01 value (negative if paying fixed, positive if receiving)
        """
        # Simplified: assume duration ≈ maturity for par swaps
        duration = maturity_years * 0.9  # Rough approximation
        dv01 = -notional * duration * 0.0001
        
        return dv01 if pay_fixed else -dv01


class FXSensitivityCalculator:
    """
    FX Sensitivity Calculator
    
    Calculates FX Delta for forwards and options.
    """
    
    @staticmethod
    def calculate_fx_delta_forward(notional: float, domestic_ccy: str,
                                   foreign_ccy: str, is_buy: bool = True) -> float:
        """
        Calculate FX Delta for a forward contract
        
        For an FX forward, Delta = Notional (in foreign currency terms)
        
        Args:
            notional: Notional in foreign currency
            domestic_ccy: Domestic currency code
            foreign_ccy: Foreign currency code  
            is_buy: True if buying foreign currency
        
        Returns:
            FX Delta (sensitivity to spot rate change)
        """
        delta = notional if is_buy else -notional
        return delta
    
    @staticmethod
    def calculate_fx_delta_option(option_params: OptionParams,
                                  option_type: OptionType,
                                  delta_type: str = 'spot') -> float:
        """
        Calculate FX Delta for an option
        
        Args:
            option_params: Option parameters
            option_type: CALL or PUT
            delta_type: 'spot' for spot delta, 'forward' for forward delta
        
        Returns:
            FX Delta sensitivity
        """
        spot_delta = BlackScholesCalculator.delta(option_params, option_type)
        
        if delta_type == 'forward':
            # Forward delta = Spot delta × exp(-r_f × T)
            r_f = option_params.dividend_yield  # Foreign rate for FX
            t = option_params.time_to_expiry
            spot_delta *= math.exp(-r_f * t)
        
        return spot_delta


class SensitivityValidator:
    """
    Validates calculated sensitivities against S&P system outputs
    """
    
    def __init__(self, tolerance_pct: float = 5.0):
        """
        Args:
            tolerance_pct: Acceptable variance percentage (default 5%)
        """
        self.tolerance_pct = tolerance_pct
    
    def validate_delta(self, sp_delta: float, challenger_delta: float,
                      context: str = "") -> Dict:
        """
        Validate Delta sensitivity
        
        Args:
            sp_delta: Delta from S&P system
            challenger_delta: Independently calculated delta
            context: Description of the trade/sensitivity
        
        Returns:
            Validation result dictionary
        """
        if abs(sp_delta) < 1e-10:
            # Both should be close to zero
            variance_pct = abs(challenger_delta) * 100
            status = 'PASS' if variance_pct < self.tolerance_pct else 'WARNING'
        else:
            variance = challenger_delta - sp_delta
            variance_pct = (variance / sp_delta) * 100
            status = 'PASS' if abs(variance_pct) < self.tolerance_pct else 'FAIL'
        
        return {
            'sensitivity_type': 'DELTA',
            'context': context,
            'sp_value': sp_delta,
            'challenger_value': challenger_delta,
            'variance': challenger_delta - sp_delta,
            'variance_pct': variance_pct if abs(sp_delta) > 1e-10 else None,
            'tolerance_pct': self.tolerance_pct,
            'status': status
        }
    
    def validate_vega(self, sp_vega: float, challenger_vega: float,
                     context: str = "") -> Dict:
        """Validate Vega sensitivity"""
        return self.validate_delta(sp_vega, challenger_vega, f"{context} - VEGA")
    
    def validate_gamma(self, sp_gamma: float, challenger_gamma: float,
                      context: str = "") -> Dict:
        """Validate Gamma sensitivity"""
        # Use absolute tolerance for gamma (second-order)
        variance = challenger_gamma - sp_gamma
        status = 'PASS' if abs(variance) < max(abs(sp_gamma) * self.tolerance_pct / 100, 1e-6) else 'FAIL'
        
        return {
            'sensitivity_type': 'GAMMA',
            'context': context,
            'sp_value': sp_gamma,
            'challenger_value': challenger_gamma,
            'variance': variance,
            'tolerance_pct': self.tolerance_pct,
            'status': status
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Risk Sensitivity Calculator - Example Calculations")
    print("=" * 70)
    
    # Example 1: FX Option Greeks
    print("\n1. FX Option Greeks (Call, EUR/USD)")
    print("-" * 70)
    
    fx_option = OptionParams(
        spot=1.0850,
        strike=1.0900,
        time_to_expiry=0.25,  # 3 months
        volatility=0.12,  # 12%
        risk_free_rate=0.045,  # USD rate
        dividend_yield=0.025,  # EUR rate
        notional=10000000  # 10M EUR
    )
    
    price = BlackScholesCalculator.price(fx_option, OptionType.CALL)
    delta = BlackScholesCalculator.delta(fx_option, OptionType.CALL)
    gamma = BlackScholesCalculator.gamma(fx_option)
    vega = BlackScholesCalculator.vega(fx_option)
    
    print(f"Option Price:     ${price:,.2f}")
    print(f"Delta:            {delta:,.2f} (FX Delta in EUR)")
    print(f"Gamma:            {gamma:,.2f}")
    print(f"Vega:             ${vega:,.2f} (per 1% vol change)")
    
    # Example 2: IRS DV01
    print("\n2. Interest Rate Swap DV01")
    print("-" * 70)
    
    dv01 = IRSensitivityCalculator.calculate_swap_dv01(
        notional=100000000,  # 100M
        fixed_rate=0.045,
        maturity_years=5,
        pay_fixed=True
    )
    
    print(f"IRS DV01 (Pay Fixed 5Y): ${dv01:,.2f}")
    print(f"Interpretation: For 1bp rate increase, P&L changes by ${dv01:,.2f}")
    
    # Example 3: Validation Example
    print("\n3. Sensitivity Validation Example")
    print("-" * 70)
    
    validator = SensitivityValidator(tolerance_pct=5.0)
    
    # Simulated S&P output vs Challenger calculation
    sp_delta = 4500000  # S&P system delta
    challenger_delta = 4485000  # Our calculation
    
    validation = validator.validate_delta(
        sp_delta=sp_delta,
        challenger_delta=challenger_delta,
        context="EUR/USD Call Option 3M"
    )
    
    print(f"S&P Delta:        ${validation['sp_value']:,.2f}")
    print(f"Challenger Delta: ${validation['challenger_value']:,.2f}")
    print(f"Variance:         ${validation['variance']:,.2f} ({validation['variance_pct']:.2f}%)")
    print(f"Status:           {validation['status']}")
    
    print("\n" + "=" * 70)
