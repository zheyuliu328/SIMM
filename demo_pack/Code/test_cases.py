"""
SIMM Validation Test Cases
===========================
Predefined test cases for SIMM model validation.

These test cases follow the "test of 1 per risk type" principle
and cover all product types in scope.

File: test_cases.py
Version: 1.0.0
Date: 2026-02-27
Author: SIMM Validation Team
"""

from simm_challenger_core import SimmChallengerModel, RiskClass, Sensitivity
from sensitivity_calculator import (
    BlackScholesCalculator, IRSensitivityCalculator, FXSensitivityCalculator,
    OptionParams, OptionType
)


class TestCaseLibrary:
    """
    Library of test cases for SIMM validation
    """
    
    @staticmethod
    def create_irs_test_case():
        """
        Test Case 1: USD Interest Rate Swap (Pay Fixed 5Y)
        
        Product: Interest Rate Swap
        Notional: USD 100,000,000
        Maturity: 5 Years
        Pay/Receive: Pay Fixed
        
        Expected Sensitivities:
        - DV01 (5Y): ~ -45,000 USD
        """
        print("\n" + "=" * 70)
        print("Test Case 1: USD IRS Pay Fixed 5Y")
        print("=" * 70)
        
        # Calculate sensitivities
        dv01 = IRSensitivityCalculator.calculate_swap_dv01(
            notional=100_000_000,
            fixed_rate=0.045,
            maturity_years=5,
            pay_fixed=True
        )
        
        print(f"Trade Details:")
        print(f"  Product: USD Interest Rate Swap")
        print(f"  Notional: USD 100,000,000")
        print(f"  Maturity: 5 Years")
        print(f"  Position: Pay Fixed")
        print(f"\nExpected Sensitivities:")
        print(f"  DV01 (5Y): ${dv01:,.2f}")
        
        # Create SIMM sensitivities
        sensitivities = [
            Sensitivity(
                risk_class=RiskClass.INTEREST_RATE,
                bucket='USD',
                tenor='5Y',
                delta=dv01,
                currency='USD'
            )
        ]
        
        # Calculate SIMM
        model = SimmChallengerModel()
        result = model.calculate_simm(sensitivities)
        
        print(f"\nSIMM Calculation Results:")
        print(f"  Delta Margin:    ${result.delta_margin:,.2f}")
        print(f"  Total IM:        ${result.total_margin:,.2f}")
        
        return {
            'trade_id': 'TC001_IRS_USD_5Y',
            'product_type': 'Interest Rate Swap',
            'sensitivities': {'DV01_5Y': dv01},
            'expected_simm': result.total_margin
        }
    
    @staticmethod
    def create_fx_forward_test_case():
        """
        Test Case 2: EUR/USD Forward
        
        Product: FX Forward
        Notional: EUR 10,000,000
        Tenor: 3 Months
        Position: Buy EUR / Sell USD
        
        Expected Sensitivities:
        - FX Delta: +10,000,000 EUR
        """
        print("\n" + "=" * 70)
        print("Test Case 2: EUR/USD Forward 3M")
        print("=" * 70)
        
        # Calculate sensitivities
        fx_delta = FXSensitivityCalculator.calculate_fx_delta_forward(
            notional=10_000_000,
            domestic_ccy='USD',
            foreign_ccy='EUR',
            is_buy=True
        )
        
        print(f"Trade Details:")
        print(f"  Product: FX Forward")
        print(f"  Currency Pair: EUR/USD")
        print(f"  Notional: EUR 10,000,000")
        print(f"  Tenor: 3 Months")
        print(f"  Position: Buy EUR / Sell USD")
        print(f"\nExpected Sensitivities:")
        print(f"  FX Delta: {fx_delta:,.2f} EUR")
        
        # Create SIMM sensitivities
        sensitivities = [
            Sensitivity(
                risk_class=RiskClass.FX,
                bucket='EUR',
                tenor='3M',
                delta=fx_delta,
                currency='EUR'
            )
        ]
        
        # Calculate SIMM
        model = SimmChallengerModel()
        result = model.calculate_simm(sensitivities)
        
        print(f"\nSIMM Calculation Results:")
        print(f"  Delta Margin:    ${result.delta_margin:,.2f}")
        print(f"  Total IM:        ${result.total_margin:,.2f}")
        
        return {
            'trade_id': 'TC002_FXFWD_EURUSD_3M',
            'product_type': 'FX Forward',
            'sensitivities': {'FX_Delta': fx_delta},
            'expected_simm': result.total_margin
        }
    
    @staticmethod
    def create_fx_option_test_case():
        """
        Test Case 3: EUR/USD Vanilla Call Option (ATM)
        
        Product: European Call Option
        Notional: EUR 10,000,000
        Strike: ATM (Spot = 1.0850)
        Expiry: 3 Months
        Volatility: 12%
        
        Expected Sensitivities:
        - Delta: ~ +5,000,000 EUR (50%)
        - Vega: ~ 12,000 USD (per 1% vol)
        - Gamma: ~ 0.045
        """
        print("\n" + "=" * 70)
        print("Test Case 3: EUR/USD Vanilla Call Option (ATM)")
        print("=" * 70)
        
        # Option parameters
        option_params = OptionParams(
            spot=1.0850,
            strike=1.0850,  # ATM
            time_to_expiry=0.25,  # 3 months
            volatility=0.12,
            risk_free_rate=0.045,  # USD rate
            dividend_yield=0.025,  # EUR rate
            notional=10_000_000
        )
        
        # Calculate Greeks
        delta = BlackScholesCalculator.delta(option_params, OptionType.CALL)
        gamma = BlackScholesCalculator.gamma(option_params)
        vega = BlackScholesCalculator.vega(option_params)
        theta = BlackScholesCalculator.theta(option_params, OptionType.CALL)
        
        print(f"Trade Details:")
        print(f"  Product: European Call Option")
        print(f"  Currency Pair: EUR/USD")
        print(f"  Notional: EUR 10,000,000")
        print(f"  Spot: 1.0850")
        print(f"  Strike: 1.0850 (ATM)")
        print(f"  Expiry: 3 Months")
        print(f"  Volatility: 12%")
        print(f"\nExpected Sensitivities (Challenger Model):")
        print(f"  Delta: {delta:,.2f} EUR ({delta/option_params.notional*100:.1f}%)")
        print(f"  Gamma: {gamma:.6f}")
        print(f"  Vega:  ${vega:,.2f} (per 1% vol change)")
        print(f"  Theta: ${theta:,.2f} per day")
        
        # Create SIMM sensitivities
        sensitivities = [
            Sensitivity(
                risk_class=RiskClass.FX,
                bucket='EUR',
                tenor='3M',
                delta=delta,
                vega=vega,
                currency='EUR'
            )
        ]
        
        # Calculate SIMM
        model = SimmChallengerModel()
        result = model.calculate_simm(sensitivities)
        
        print(f"\nSIMM Calculation Results:")
        print(f"  Delta Margin:     ${result.delta_margin:,.2f}")
        print(f"  Vega Margin:      ${result.vega_margin:,.2f}")
        print(f"  Curvature Margin: ${result.curvature_margin:,.2f}")
        print(f"  Total IM:         ${result.total_margin:,.2f}")
        
        return {
            'trade_id': 'TC003_FXOPT_EURUSD_CALL_ATM',
            'product_type': 'FX Vanilla Option',
            'sensitivities': {
                'Delta': delta,
                'Gamma': gamma,
                'Vega': vega,
                'Theta': theta
            },
            'expected_simm': result.total_margin
        }
    
    @staticmethod
    def create_fx_option_itm_test_case():
        """
        Test Case 4: EUR/USD Vanilla Call Option (ITM)
        
        Product: European Call Option
        Notional: EUR 10,000,000
        Strike: 1.0500 (ITM, spot = 1.0850)
        Expiry: 3 Months
        Volatility: 12%
        
        Expected Sensitivities:
        - Delta: ~ +7,500,000 EUR (75%)
        - Vega: ~ 8,000 USD (per 1% vol)
        """
        print("\n" + "=" * 70)
        print("Test Case 4: EUR/USD Vanilla Call Option (ITM)")
        print("=" * 70)
        
        # Option parameters (ITM)
        option_params = OptionParams(
            spot=1.0850,
            strike=1.0500,  # ITM
            time_to_expiry=0.25,
            volatility=0.12,
            risk_free_rate=0.045,
            dividend_yield=0.025,
            notional=10_000_000
        )
        
        # Calculate Greeks
        delta = BlackScholesCalculator.delta(option_params, OptionType.CALL)
        vega = BlackScholesCalculator.vega(option_params)
        
        print(f"Trade Details:")
        print(f"  Product: European Call Option")
        print(f"  Currency Pair: EUR/USD")
        print(f"  Notional: EUR 10,000,000")
        print(f"  Spot: 1.0850")
        print(f"  Strike: 1.0500 (ITM)")
        print(f"  Expiry: 3 Months")
        print(f"\nExpected Sensitivities:")
        print(f"  Delta: {delta:,.2f} EUR ({delta/option_params.notional*100:.1f}%)")
        print(f"  Vega:  ${vega:,.2f} (per 1% vol change)")
        
        return {
            'trade_id': 'TC004_FXOPT_EURUSD_CALL_ITM',
            'product_type': 'FX Vanilla Option',
            'sensitivities': {'Delta': delta, 'Vega': vega},
            'expected_simm': None
        }
    
    @staticmethod
    def create_fx_option_otm_test_case():
        """
        Test Case 5: EUR/USD Vanilla Call Option (OTM)
        
        Product: European Call Option
        Notional: EUR 10,000,000
        Strike: 1.1200 (OTM, spot = 1.0850)
        Expiry: 3 Months
        Volatility: 12%
        
        Expected Sensitivities:
        - Delta: ~ +2,500,000 EUR (25%)
        - Vega: ~ 15,000 USD (per 1% vol)
        """
        print("\n" + "=" * 70)
        print("Test Case 5: EUR/USD Vanilla Call Option (OTM)")
        print("=" * 70)
        
        # Option parameters (OTM)
        option_params = OptionParams(
            spot=1.0850,
            strike=1.1200,  # OTM
            time_to_expiry=0.25,
            volatility=0.12,
            risk_free_rate=0.045,
            dividend_yield=0.025,
            notional=10_000_000
        )
        
        # Calculate Greeks
        delta = BlackScholesCalculator.delta(option_params, OptionType.CALL)
        vega = BlackScholesCalculator.vega(option_params)
        
        print(f"Trade Details:")
        print(f"  Product: European Call Option")
        print(f"  Currency Pair: EUR/USD")
        print(f"  Notional: EUR 10,000,000")
        print(f"  Spot: 1.0850")
        print(f"  Strike: 1.1200 (OTM)")
        print(f"  Expiry: 3 Months")
        print(f"\nExpected Sensitivities:")
        print(f"  Delta: {delta:,.2f} EUR ({delta/option_params.notional*100:.1f}%)")
        print(f"  Vega:  ${vega:,.2f} (per 1% vol change)")
        
        return {
            'trade_id': 'TC005_FXOPT_EURUSD_CALL_OTM',
            'product_type': 'FX Vanilla Option',
            'sensitivities': {'Delta': delta, 'Vega': vega},
            'expected_simm': None
        }


def run_all_test_cases():
    """Run all test cases and generate report"""
    print("\n" + "=" * 70)
    print("SIMM VALIDATION TEST SUITE")
    print("=" * 70)
    print("\nRunning all test cases...\n")
    
    results = []
    
    # Run each test case
    results.append(TestCaseLibrary.create_irs_test_case())
    results.append(TestCaseLibrary.create_fx_forward_test_case())
    results.append(TestCaseLibrary.create_fx_option_test_case())
    results.append(TestCaseLibrary.create_fx_option_itm_test_case())
    results.append(TestCaseLibrary.create_fx_option_otm_test_case())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"\nTotal Test Cases: {len(results)}")
    print("\nTest Case IDs:")
    for result in results:
        print(f"  - {result['trade_id']}: {result['product_type']}")
    
    print("\n" + "=" * 70)
    print("\nUsage:")
    print("  1. Input these trades into S&P SIMM system")
    print("  2. Extract SIMM results from S&P")
    print("  3. Use validation_framework.py to reconcile")
    print("  4. Generate validation report")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    run_all_test_cases()
