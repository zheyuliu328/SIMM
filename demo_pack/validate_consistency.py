#!/usr/bin/env python3
"""
SIMM Demo Results vs Slides Key Numbers - Consistency Checker
演示结果与Slides关键数字一致性校验脚本

用途：
- 自动校验demo计算结果与slides声明数字的一致性
- 生成校验报告
- CI/CD门禁检查

版本：v1.0.0 (Round 3 Optimize)
"""

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from pathlib import Path


@dataclass
class ValidationRule:
    """校验规则定义"""
    name: str
    path: str  # JSON path to value in result
    expected_value: Decimal
    tolerance_pct: Decimal  # 容忍度百分比
    description: str


@dataclass
class ValidationResult:
    """单个校验结果"""
    rule_name: str
    passed: bool
    expected: Decimal
    actual: Decimal
    diff_pct: Decimal
    message: str


class SlidesConsistencyChecker:
    """
    Slides关键数字一致性校验器
    
    校验目标 (来自 v3_slides.md):
    - Total SIMM Margin: $12,847,392.56
    - IR Margin: $8,542,123.12 (66.5%)
    - Credit Qualifying (CRQ): $2,456,789.34 (19.1%)
    - Credit Non-Qualifying (CRNQ): $987,654.32 (7.7%)
    - Equity: $687,432.10 (5.3%)
    - FX: $173,393.68 (1.4%)
    """
    
    # Slides v3.0 关键数字定义
    SLIDES_KEY_NUMBERS = {
        "total_margin": Decimal("12847392.56"),
        "ir_margin": Decimal("8542123.12"),
        "crq_margin": Decimal("2456789.34"),
        "crnq_margin": Decimal("987654.32"),
        "equity_margin": Decimal("687432.10"),
        "fx_margin": Decimal("173393.68"),
    }
    
    # 百分比贡献 (用于交叉验证)
    SLIDES_CONTRIBUTIONS = {
        "ir_pct": Decimal("66.5"),
        "crq_pct": Decimal("19.1"),
        "crnq_pct": Decimal("7.7"),
        "equity_pct": Decimal("5.3"),
        "fx_pct": Decimal("1.4"),
    }
    
    DEFAULT_TOLERANCE = Decimal("5.0")  # 默认5%容忍度
    
    def __init__(self, tolerance_pct: Decimal = None):
        self.tolerance = tolerance_pct or self.DEFAULT_TOLERANCE
        self.results: List[ValidationResult] = []
        
    def validate_demo_result(self, demo_result: dict) -> List[ValidationResult]:
        """
        校验demo结果与slides关键数字
        
        Args:
            demo_result: simm_demo_explainable.py 的输出结果
            
        Returns:
            List[ValidationResult]: 校验结果列表
        """
        self.results = []
        
        # 1. 校验Total Margin
        actual_total = Decimal(str(demo_result.get("total_margin", 0)))
        self._check_value(
            "Total SIMM Margin",
            self.SLIDES_KEY_NUMBERS["total_margin"],
            actual_total,
            self.tolerance
        )
        
        # 2. 校验各Risk Class Margin
        risk_classes = demo_result.get("risk_class_margins", {})
        
        # IR
        actual_ir = Decimal(str(risk_classes.get("IR", 0)))
        self._check_value(
            "Interest Rate Margin",
            self.SLIDES_KEY_NUMBERS["ir_margin"],
            actual_ir,
            self.tolerance
        )
        
        # Credit (合并CRQ+CRNQ)
        credit_breakdown = demo_result.get("credit_breakdown", {})
        actual_crq = Decimal(str(credit_breakdown.get("crq_total", 0)))
        actual_crnq = Decimal(str(credit_breakdown.get("crnq_total", 0)))
        
        self._check_value(
            "Credit Qualifying (CRQ) Margin",
            self.SLIDES_KEY_NUMBERS["crq_margin"],
            actual_crq,
            self.tolerance
        )
        
        self._check_value(
            "Credit Non-Qualifying (CRNQ) Margin",
            self.SLIDES_KEY_NUMBERS["crnq_margin"],
            actual_crnq,
            self.tolerance
        )
        
        # Equity
        actual_eq = Decimal(str(risk_classes.get("EQ", 0)))
        self._check_value(
            "Equity Margin",
            self.SLIDES_KEY_NUMBERS["equity_margin"],
            actual_eq,
            self.tolerance
        )
        
        # FX
        actual_fx = Decimal(str(risk_classes.get("FX", 0)))
        self._check_value(
            "FX Margin",
            self.SLIDES_KEY_NUMBERS["fx_margin"],
            actual_fx,
            self.tolerance
        )
        
        # 3. 校验百分比贡献 (交叉验证)
        if actual_total > 0:
            actual_ir_pct = (actual_ir / actual_total * 100).quantize(Decimal("0.1"))
            self._check_value(
                "IR Contribution %",
                self.SLIDES_CONTRIBUTIONS["ir_pct"],
                actual_ir_pct,
                Decimal("1.0")  # 百分比用1%容忍度
            )
        
        return self.results
    
    def _check_value(self, name: str, expected: Decimal, actual: Decimal, 
                     tolerance_pct: Decimal):
        """执行单个数值校验"""
        if expected == 0:
            diff_pct = Decimal("0") if actual == 0 else Decimal("999")
        else:
            diff_pct = (abs(actual - expected) / expected * 100).quantize(Decimal("0.01"))
        
        passed = diff_pct <= tolerance_pct
        
        if passed:
            message = f"✅ PASS: 差异 {diff_pct}% (<= {tolerance_pct}% 容忍度)"
        else:
            message = f"❌ FAIL: 差异 {diff_pct}% (> {tolerance_pct}% 容忍度)"
        
        result = ValidationResult(
            rule_name=name,
            passed=passed,
            expected=expected,
            actual=actual,
            diff_pct=diff_pct,
            message=message
        )
        self.results.append(result)
    
    def generate_report(self) -> str:
        """生成校验报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("SIMM Demo vs Slides Consistency Check Report")
        lines.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
        lines.append("=" * 80)
        lines.append("")
        
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count
        
        lines.append(f"Summary: {passed_count}/{len(self.results)} checks passed")
        lines.append("")
        
        # 详细结果
        lines.append("-" * 80)
        lines.append("Detailed Results:")
        lines.append("-" * 80)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            lines.append(f"\n{status} | {result.rule_name}")
            lines.append(f"  Expected: ${result.expected:,.2f}")
            lines.append(f"  Actual:   ${result.actual:,.2f}")
            lines.append(f"  Diff:     {result.diff_pct}%")
            lines.append(f"  Status:   {result.message}")
        
        lines.append("")
        lines.append("=" * 80)
        
        if failed_count == 0:
            lines.append("✅ ALL CHECKS PASSED - Demo results are consistent with slides")
        else:
            lines.append(f"⚠️  {failed_count} CHECK(S) FAILED - Review differences above")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def exit_code(self) -> int:
        """返回shell退出码 (0=通过, 1=失败)"""
        failed_count = sum(1 for r in self.results if not r.passed)
        return 0 if failed_count == 0 else 1


def load_demo_result(filepath: str) -> dict:
    """加载demo结果文件"""
    path = Path(filepath)
    if not path.exists():
        # 如果文件不存在，尝试从Python模块导入
        print(f"Note: {filepath} not found, running demo to generate results...")
        try:
            import simm_demo_explainable as demo
            result = demo.run_demo()
            return {
                "total_margin": float(result.total_margin),
                "risk_class_margins": {
                    k.value: float(v) for k, v in result.risk_class_margins.items()
                },
                "credit_breakdown": result.credit_breakdown.to_dict() if result.credit_breakdown else {}
            }
        except Exception as e:
            print(f"Error running demo: {e}")
            return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate SIMM demo results against slides key numbers"
    )
    parser.add_argument(
        "--input", "-i",
        default="demo_result.json",
        help="Path to demo result JSON file"
    )
    parser.add_argument(
        "--tolerance", "-t",
        type=float,
        default=5.0,
        help="Tolerance percentage (default: 5.0)"
    )
    parser.add_argument(
        "--output", "-o",
        default="validation_report.txt",
        help="Output report file path"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with non-zero code on failure"
    )
    
    args = parser.parse_args()
    
    # 加载demo结果
    demo_result = load_demo_result(args.input)
    
    if not demo_result:
        print("Error: No demo result data available")
        sys.exit(1)
    
    # 执行校验
    checker = SlidesConsistencyChecker(tolerance_pct=Decimal(str(args.tolerance)))
    checker.validate_demo_result(demo_result)
    
    # 生成报告
    report = checker.generate_report()
    print(report)
    
    # 保存报告
    with open(args.output, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {args.output}")
    
    # CI模式退出码
    if args.ci:
        sys.exit(checker.exit_code())


if __name__ == "__main__":
    main()
