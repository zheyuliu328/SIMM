"""
SIMM Validation - Complete Workflow Example
============================================
This script demonstrates the complete SIMM validation workflow:

1. Generate test case sensitivities using Challenger Model
2. Calculate SIMM using independent implementation
3. Compare against S&P SIMM results
4. Generate validation report

Usage:
    python run_validation.py

File: run_validation.py
Version: 1.0.0
Date: 2026-02-27
Author: SIMM Validation Team
"""

from simm_challenger_core import SimmChallengerModel, RiskClass, Sensitivity, SimmResult
from sensitivity_calculator import (
    BlackScholesCalculator, IRSensitivityCalculator, FXSensitivityCalculator,
    OptionParams, OptionType, SensitivityValidator
)
from validation_framework import (
    SimmReconciliationEngine, ValidationReportGenerator, TradeValidationReport,
    ValidationResult, ValidationStatus, TestCaseManager
)
from test_cases import TestCaseLibrary
from datetime import datetime


def run_complete_validation_example():
    """
    Complete validation workflow example
    """
    print("=" * 80)
    print(" SIMM MODEL VALIDATION - COMPLETE WORKFLOW")
    print("=" * 80)
    print(f"\nValidation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80)
    
    # =========================================================================
    # STEP 1: Define Test Trade (Simulating S&P input)
    # =========================================================================
    print("\n STEP 1: Define Test Trade")
    print("-" * 80)
    
    trade_info = {
        'trade_id': 'VAL_001',
        'product_type': 'FX_Vanilla_Option',
        'description': 'EUR/USD European Call Option (ATM)',
        'notional': 10_000_000,  # EUR
        'currency': 'EUR',
        'spot': 1.0850,
        'strike': 1.0850,
        'time_to_expiry_years': 0.25,  # 3 months
        'volatility': 0.12,
        'usd_rate': 0.045,
        'eur_rate': 0.025
    }
    
    print(f"Trade ID: {trade_info['trade_id']}")
    print(f"Product: {trade_info['description']}")
    print(f"Notional: {trade_info['notional']:,.0f} {trade_info['currency']}")
    print(f"Spot: {trade_info['spot']}")
    print(f"Strike: {trade_info['strike']}")
    print(f"Expiry: {trade_info['time_to_expiry_years']*12:.0f} months")
    print(f"Volatility: {trade_info['volatility']*100:.1f}%")
    
    # =========================================================================
    # STEP 2: Calculate Sensitivities using Challenger Model
    # =========================================================================
    print("\n STEP 2: Calculate Sensitivities (Challenger Model)")
    print("-" * 80)
    
    # Create option parameters
    option_params = OptionParams(
        spot=trade_info['spot'],
        strike=trade_info['strike'],
        time_to_expiry=trade_info['time_to_expiry_years'],
        volatility=trade_info['volatility'],
        risk_free_rate=trade_info['usd_rate'],
        dividend_yield=trade_info['eur_rate'],
        notional=trade_info['notional']
    )
    
    # Calculate Greeks using Black-Scholes
    challenger_delta = BlackScholesCalculator.delta(option_params, OptionType.CALL)
    challenger_gamma = BlackScholesCalculator.gamma(option_params)
    challenger_vega = BlackScholesCalculator.vega(option_params)
    
    print(f"Challenger Model Results:")
    print(f"  Delta: {challenger_delta:,.2f} EUR ({challenger_delta/trade_info['notional']*100:.1f}%)")
    print(f"  Gamma: {challenger_gamma:.6f}")
    print(f"  Vega:  ${challenger_vega:,.2f} (per 1% vol change)")
    
    # =========================================================================
    # STEP 3: Simulated S&P System Output
    # =========================================================================
    print("\n STEP 3: Simulated S&P System Output")
    print("-" * 80)
    
    # In real validation, these would come from S&P system
    # Simulating small variances (1-3%) to demonstrate validation
    sp_delta = challenger_delta * 1.02  # 2% variance
    sp_gamma = challenger_gamma * 0.98  # 2% variance
    sp_vega = challenger_vega * 1.015   # 1.5% variance
    
    sp_simm_result = SimmResult(
        total_margin=2_650_000,  # Simulated S&P SIMM output
        delta_margin=2_100_000,
        vega_margin=850_000,
        curvature_margin=320_000
    )
    
    print(f"S&P System Results:")
    print(f"  Delta: {sp_delta:,.2f} EUR ({sp_delta/trade_info['notional']*100:.1f}%)")
    print(f"  Gamma: {sp_gamma:.6f}")
    print(f"  Vega:  ${sp_vega:,.2f}")
    print(f"\nS&P SIMM Margin:")
    print(f"  Total Margin: ${sp_simm_result.total_margin:,.2f}")
    print(f"  Delta Margin: ${sp_simm_result.delta_margin:,.2f}")
    print(f"  Vega Margin:  ${sp_simm_result.vega_margin:,.2f}")
    
    # =========================================================================
    # STEP 4: Validate Sensitivities
    # =========================================================================
    print("\n STEP 4: Validate Sensitivities")
    print("-" * 80)
    
    validator = SensitivityValidator(tolerance_pct=5.0)
    
    # Validate Delta
    delta_validation = validator.validate_delta(
        sp_delta=sp_delta,
        challenger_delta=challenger_delta,
        context=f"{trade_info['trade_id']} - FX Delta"
    )
    
    print(f"Delta Validation:")
    print(f"  S&P Value:        ${delta_validation['sp_value']:,.2f}")
    print(f"  Challenger Value: ${delta_validation['challenger_value']:,.2f}")
    print(f"  Variance:         ${delta_validation['variance']:,.2f} ({delta_validation['variance_pct']:+.2f}%)")
    print(f"  Status:           {delta_validation['status']}")
    
    # Validate Vega
    vega_validation = validator.validate_delta(
        sp_delta=sp_vega,
        challenger_delta=challenger_vega,
        context=f"{trade_info['trade_id']} - Vega"
    )
    
    print(f"\nVega Validation:")
    print(f"  S&P Value:        ${vega_validation['sp_value']:,.2f}")
    print(f"  Challenger Value: ${vega_validation['challenger_value']:,.2f}")
    print(f"  Variance:         ${vega_validation['variance']:,.2f} ({vega_validation['variance_pct']:+.2f}%)")
    print(f"  Status:           {vega_validation['status']}")
    
    # =========================================================================
    # STEP 5: Calculate SIMM using Challenger Model
    # =========================================================================
    print("\n STEP 5: Calculate SIMM (Challenger Model)")
    print("-" * 80)
    
    # Create sensitivities for SIMM calculation
    sensitivities = [
        Sensitivity(
            risk_class=RiskClass.FX,
            bucket='EUR',
            tenor='3M',
            delta=challenger_delta,
            vega=challenger_vega,
            currency='EUR'
        )
    ]
    
    # Calculate SIMM
    simm_model = SimmChallengerModel()
    challenger_simm_result = simm_model.calculate_simm(sensitivities)
    
    print(f"Challenger SIMM Results:")
    print(f"  Delta Margin:     ${challenger_simm_result.delta_margin:,.2f}")
    print(f"  Vega Margin:      ${challenger_simm_result.vega_margin:,.2f}")
    print(f"  Curvature Margin: ${challenger_simm_result.curvature_margin:,.2f}")
    print(f"  Total IM:         ${challenger_simm_result.total_margin:,.2f}")
    
    # =========================================================================
    # STEP 6: Reconcile SIMM Results
    # =========================================================================
    print("\n STEP 6: Reconcile SIMM Results")
    print("-" * 80)
    
    reconciliation_engine = SimmReconciliationEngine(default_tolerance_pct=1.0)
    
    # Create validation report
    validation_report = TradeValidationReport(
        trade_id=trade_info['trade_id'],
        product_type=trade_info['product_type'],
        notional=trade_info['notional'],
        currency=trade_info['currency'],
        validation_date=datetime.now().isoformat()
    )
    
    # Reconcile Total Margin
    total_margin_result = reconciliation_engine.reconcile_total_margin(
        sp_margin=sp_simm_result.total_margin,
        challenger_margin=challenger_simm_result.total_margin,
        tolerance_pct=1.0
    )
    validation_report.add_result(total_margin_result)
    
    print(f"Total Margin Reconciliation:")
    print(f"  S&P SIMM:         ${total_margin_result.sp_value:,.2f}")
    print(f"  Challenger SIMM:  ${total_margin_result.challenger_value:,.2f}")
    print(f"  Variance:         ${total_margin_result.variance:,.2f} ({total_margin_result.variance_pct:+.2f}%)")
    print(f"  Status:           {total_margin_result.status.value}")
    print(f"  Details:          {total_margin_result.details}")
    
    # Reconcile component margins
    for component in [
        ('Delta Margin', sp_simm_result.delta_margin, challenger_simm_result.delta_margin),
        ('Vega Margin', sp_simm_result.vega_margin, challenger_simm_result.vega_margin),
        ('Curvature Margin', sp_simm_result.curvature_margin, challenger_simm_result.curvature_margin)
    ]:
        result = reconciliation_engine.reconcile_component(
            component_name=component[0],
            sp_value=component[1],
            challenger_value=component[2]
        )
        validation_report.add_result(result)
    
    # =========================================================================
    # STEP 7: Generate Validation Report
    # =========================================================================
    print("\n STEP 7: Generate Validation Report")
    print("-" * 80)
    
    report_gen = ValidationReportGenerator()
    report_gen.add_report(validation_report)
    
    # Generate JSON report
    json_report = report_gen.generate_json_report()
    print("\nJSON Report Generated (excerpt):")
    print(json_report[:600] + "...")
    
    # Generate Markdown report
    md_report = report_gen.generate_markdown_report()
    
    # Save reports
    json_filename = f"validation_report_{trade_info['trade_id']}.json"
    md_filename = f"validation_report_{trade_info['trade_id']}.md"
    
    report_gen.generate_json_report(json_filename)
    report_gen.generate_markdown_report(md_filename)
    
    print(f"\nReports saved:")
    print(f"  - {json_filename}")
    print(f"  - {md_filename}")
    
    # =========================================================================
    # STEP 8: Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print(" VALIDATION SUMMARY")
    print("=" * 80)
    
    summary = validation_report.get_summary()
    print(f"\nTrade ID: {summary['trade_id']}")
    print(f"Overall Status: {summary['overall_status']}")
    print(f"\nTotal Checks: {summary['total_checks']}")
    print(f"  Passed:   {summary['passed']}")
    print(f"  Failed:   {summary['failed']}")
    print(f"  Warnings: {summary['warnings']}")
    
    print("\n" + "=" * 80)
    print(" VALIDATION COMPLETE")
    print("=" * 80)
    
    return validation_report


def run_batch_validation():
    """
    Run validation on all test cases
    """
    print("\n" + "=" * 80)
    print(" BATCH VALIDATION - All Test Cases")
    print("=" * 80)
    
    # Import and run test cases
    from test_cases import run_all_test_cases
    test_results = run_all_test_cases()
    
    print("\n" + "=" * 80)
    print(" Batch validation would proceed as follows:")
    print("  1. Input each test case into S&P SIMM system")
    print("  2. Extract S&P results")
    print("  3. Run reconciliation for each trade")
    print("  4. Generate consolidated validation report")
    print("=" * 80)


if __name__ == "__main__":
    # Run single trade validation example
    run_complete_validation_example()
    
    # Uncomment to run batch validation
    # run_batch_validation()
