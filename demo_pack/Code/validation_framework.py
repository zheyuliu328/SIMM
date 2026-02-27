"""
SIMM Validation Framework
=========================
Framework for validating S&P SIMM calculations against Challenger Model.

This module provides:
- Reconciliation engine for S&P vs Challenger results
- Variance analysis and tolerance checking
- Validation report generation
- Test case management

File: validation_framework.py
Version: 1.0.0
Date: 2026-02-27
Author: SIMM Validation Team
"""

import json
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class ValidationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    PENDING = "PENDING"


@dataclass
class ValidationResult:
    """Individual validation check result"""
    check_name: str
    sp_value: float
    challenger_value: float
    variance: float
    variance_pct: float
    tolerance_pct: float
    status: ValidationStatus
    details: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'check_name': self.check_name,
            'sp_value': self.sp_value,
            'challenger_value': self.challenger_value,
            'variance': self.variance,
            'variance_pct': self.variance_pct,
            'tolerance_pct': self.tolerance_pct,
            'status': self.status.value,
            'details': self.details
        }


@dataclass
class TradeValidationReport:
    """Complete validation report for a single trade"""
    trade_id: str
    product_type: str
    notional: float
    currency: str
    validation_date: str
    results: List[ValidationResult] = field(default_factory=list)
    
    def add_result(self, result: ValidationResult):
        self.results.append(result)
    
    def get_summary(self) -> Dict:
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        
        return {
            'trade_id': self.trade_id,
            'total_checks': len(self.results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'overall_status': 'PASS' if failed == 0 else 'FAIL'
        }
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'product_type': self.product_type,
            'notional': self.notional,
            'currency': self.currency,
            'validation_date': self.validation_date,
            'summary': self.get_summary(),
            'results': [r.to_dict() for r in self.results]
        }


class SimmReconciliationEngine:
    """
    Reconciliation engine for comparing S&P SIMM vs Challenger Model
    """
    
    def __init__(self, default_tolerance_pct: float = 1.0):
        """
        Args:
            default_tolerance_pct: Default tolerance for variance checks (1% = 0.01)
        """
        self.default_tolerance_pct = default_tolerance_pct
    
    def reconcile_total_margin(self, sp_margin: float, challenger_margin: float,
                              tolerance_pct: Optional[float] = None) -> ValidationResult:
        """
        Reconcile total SIMM margin
        
        Args:
            sp_margin: Total margin from S&P system
            challenger_margin: Total margin from Challenger model
            tolerance_pct: Override default tolerance
        
        Returns:
            ValidationResult with variance analysis
        """
        tolerance = tolerance_pct or self.default_tolerance_pct
        
        if abs(sp_margin) < 1e-6:
            variance_pct = 0 if abs(challenger_margin) < 1e-6 else float('inf')
        else:
            variance_pct = ((challenger_margin - sp_margin) / sp_margin) * 100
        
        variance = challenger_margin - sp_margin
        
        # Determine status
        if abs(variance_pct) <= tolerance:
            status = ValidationStatus.PASS
            details = f"Variance within tolerance ({tolerance}%)"
        elif abs(variance_pct) <= tolerance * 2:
            status = ValidationStatus.WARNING
            details = f"Variance slightly above tolerance ({tolerance}%)"
        else:
            status = ValidationStatus.FAIL
            details = f"Variance exceeds tolerance ({tolerance}%)"
        
        return ValidationResult(
            check_name="Total SIMM Margin",
            sp_value=sp_margin,
            challenger_value=challenger_margin,
            variance=variance,
            variance_pct=variance_pct,
            tolerance_pct=tolerance,
            status=status,
            details=details
        )
    
    def reconcile_component(self, component_name: str,
                           sp_value: float, challenger_value: float,
                           tolerance_pct: Optional[float] = None) -> ValidationResult:
        """
        Reconcile a specific component (Delta, Vega, Curvature)
        
        Args:
            component_name: Name of the component (e.g., "Delta Margin")
            sp_value: Component value from S&P
            challenger_value: Component value from Challenger
            tolerance_pct: Override default tolerance
        """
        tolerance = tolerance_pct or self.default_tolerance_pct
        
        if abs(sp_value) < 1e-6:
            variance_pct = 0 if abs(challenger_value) < 1e-6 else float('inf')
        else:
            variance_pct = ((challenger_value - sp_value) / sp_value) * 100
        
        variance = challenger_value - sp_value
        
        if abs(variance_pct) <= tolerance:
            status = ValidationStatus.PASS
        elif abs(variance_pct) <= tolerance * 2:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAIL
        
        return ValidationResult(
            check_name=component_name,
            sp_value=sp_value,
            challenger_value=challenger_value,
            variance=variance,
            variance_pct=variance_pct,
            tolerance_pct=tolerance,
            status=status,
            details=f"Component: {component_name}"
        )
    
    def reconcile_sensitivities(self, sp_sensitivities: Dict[str, float],
                               challenger_sensitivities: Dict[str, float],
                               tolerance_pct: float = 5.0) -> List[ValidationResult]:
        """
        Reconcile individual sensitivities (Delta, Vega per bucket/tenor)
        
        Args:
            sp_sensitivities: Dict of {key: sensitivity} from S&P
            challenger_sensitivities: Dict of {key: sensitivity} from Challenger
            tolerance_pct: Tolerance for sensitivity variance
        
        Returns:
            List of ValidationResult for each sensitivity
        """
        results = []
        all_keys = set(sp_sensitivities.keys()) | set(challenger_sensitivities.keys())
        
        for key in all_keys:
            sp_val = sp_sensitivities.get(key, 0.0)
            ch_val = challenger_sensitivities.get(key, 0.0)
            
            if abs(sp_val) < 1e-6:
                variance_pct = 0 if abs(ch_val) < 1e-6 else float('inf')
            else:
                variance_pct = ((ch_val - sp_val) / sp_val) * 100
            
            variance = ch_val - sp_val
            
            if abs(variance_pct) <= tolerance_pct:
                status = ValidationStatus.PASS
            elif abs(variance_pct) <= tolerance_pct * 2:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAIL
            
            results.append(ValidationResult(
                check_name=f"Sensitivity: {key}",
                sp_value=sp_val,
                challenger_value=ch_val,
                variance=variance,
                variance_pct=variance_pct,
                tolerance_pct=tolerance_pct,
                status=status
            ))
        
        return results


class ValidationReportGenerator:
    """
    Generates validation reports in various formats
    """
    
    def __init__(self):
        self.reports: List[TradeValidationReport] = []
    
    def add_report(self, report: TradeValidationReport):
        self.reports.append(report)
    
    def generate_json_report(self, output_file: Optional[str] = None) -> str:
        """Generate JSON format validation report"""
        report_data = {
            'report_date': datetime.now().isoformat(),
            'total_trades': len(self.reports),
            'summary': self._generate_summary(),
            'trades': [r.to_dict() for r in self.reports]
        }
        
        json_output = json.dumps(report_data, indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)
        
        return json_output
    
    def generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """Generate Markdown format validation report"""
        lines = []
        lines.append("# SIMM Validation Report")
        lines.append(f"\n**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Trades Validated:** {len(self.reports)}")
        lines.append("\n---\n")
        
        # Executive Summary
        lines.append("## Executive Summary")
        summary = self._generate_summary()
        lines.append(f"\n- **Overall Status:** {summary['overall_status']}")
        lines.append(f"- **Total Checks:** {summary['total_checks']}")
        lines.append(f"- **Passed:** {summary['total_passed']} ({summary['pass_rate']:.1f}%)")
        lines.append(f"- **Failed:** {summary['total_failed']}")
        lines.append(f"- **Warnings:** {summary['total_warnings']}")
        lines.append("\n---\n")
        
        # Per-trade details
        for report in self.reports:
            lines.append(f"## Trade: {report.trade_id}")
            lines.append(f"\n- **Product Type:** {report.product_type}")
            lines.append(f"- **Notional:** {report.notional:,.2f} {report.currency}")
            lines.append(f"- **Overall Status:** {report.get_summary()['overall_status']}")
            lines.append("\n### Validation Results\n")
            
            lines.append("| Check | S&P Value | Challenger | Variance | Status |")
            lines.append("|-------|-----------|------------|----------|--------|")
            
            for result in report.results:
                var_str = f"{result.variance:,.2f} ({result.variance_pct:+.2f}%)"
                lines.append(f"| {result.check_name} | {result.sp_value:,.2f} | "
                           f"{result.challenger_value:,.2f} | {var_str} | {result.status.value} |")
            
            lines.append("\n---\n")
        
        md_output = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(md_output)
        
        return md_output
    
    def _generate_summary(self) -> Dict:
        """Generate overall summary statistics"""
        total_checks = sum(len(r.results) for r in self.reports)
        total_passed = sum(
            sum(1 for res in r.results if res.status == ValidationStatus.PASS)
            for r in self.reports
        )
        total_failed = sum(
            sum(1 for res in r.results if res.status == ValidationStatus.FAIL)
            for r in self.reports
        )
        total_warnings = sum(
            sum(1 for res in r.results if res.status == ValidationStatus.WARNING)
            for r in self.reports
        )
        
        pass_rate = (total_passed / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'total_trades': len(self.reports),
            'total_checks': total_checks,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_warnings': total_warnings,
            'pass_rate': pass_rate,
            'overall_status': 'PASS' if total_failed == 0 else 'FAIL'
        }


class TestCaseManager:
    """
    Manages test cases for SIMM validation
    """
    
    def __init__(self):
        self.test_cases: List[Dict] = []
    
    def add_test_case(self, trade_id: str, product_type: str,
                     sp_inputs: Dict, expected_sensitivities: Dict,
                     description: str = ""):
        """
        Add a test case for validation
        
        Args:
            trade_id: Unique trade identifier
            product_type: Product classification
            sp_inputs: Trade parameters from S&P
            expected_sensitivities: Expected sensitivity outputs
            description: Test case description
        """
        self.test_cases.append({
            'trade_id': trade_id,
            'product_type': product_type,
            'sp_inputs': sp_inputs,
            'expected_sensitivities': expected_sensitivities,
            'description': description,
            'created_date': datetime.now().isoformat()
        })
    
    def get_test_cases_by_product(self, product_type: str) -> List[Dict]:
        """Get all test cases for a specific product type"""
        return [tc for tc in self.test_cases if tc['product_type'] == product_type]
    
    def save_test_cases(self, filename: str):
        """Save test cases to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.test_cases, f, indent=2)
    
    def load_test_cases(self, filename: str):
        """Load test cases from JSON file"""
        with open(filename, 'r') as f:
            self.test_cases = json.load(f)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SIMM Validation Framework - Example Usage")
    print("=" * 70)
    
    # Create reconciliation engine
    engine = SimmReconciliationEngine(default_tolerance_pct=1.0)
    
    # Example: Reconcile a trade
    print("\n1. Reconciling Single Trade")
    print("-" * 70)
    
    # Simulated S&P results
    sp_result = {
        'total_margin': 2500000,
        'delta_margin': 2000000,
        'vega_margin': 800000,
        'curvature_margin': 300000
    }
    
    # Simulated Challenger results
    challenger_result = {
        'total_margin': 2525000,  # 1% variance
        'delta_margin': 1980000,  # 1% variance
        'vega_margin': 820000,    # 2.5% variance
        'curvature_margin': 295000
    }
    
    # Create validation report
    report = TradeValidationReport(
        trade_id="TEST_001",
        product_type="FX_VANILLA_OPTION",
        notional=10000000,
        currency="EUR",
        validation_date=datetime.now().isoformat()
    )
    
    # Reconcile total margin
    total_result = engine.reconcile_total_margin(
        sp_margin=sp_result['total_margin'],
        challenger_margin=challenger_result['total_margin']
    )
    report.add_result(total_result)
    
    # Reconcile components
    for component in ['delta_margin', 'vega_margin', 'curvature_margin']:
        result = engine.reconcile_component(
            component_name=component.replace('_', ' ').title(),
            sp_value=sp_result[component],
            challenger_value=challenger_result[component]
        )
        report.add_result(result)
    
    print(f"Trade ID: {report.trade_id}")
    print(f"Product: {report.product_type}")
    print(f"Overall Status: {report.get_summary()['overall_status']}")
    print("\nDetailed Results:")
    for result in report.results:
        print(f"  {result.check_name}: {result.status.value} "
              f"(Variance: {result.variance_pct:+.2f}%)")
    
    # Generate reports
    print("\n2. Generating Reports")
    print("-" * 70)
    
    report_gen = ValidationReportGenerator()
    report_gen.add_report(report)
    
    # JSON report
    json_report = report_gen.generate_json_report()
    print("\nJSON Report Preview (first 500 chars):")
    print(json_report[:500] + "...")
    
    # Markdown report
    md_report = report_gen.generate_markdown_report()
    print("\n\nMarkdown Report Preview (first 800 chars):")
    print(md_report[:800] + "...")
    
    print("\n" + "=" * 70)
