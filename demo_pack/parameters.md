# SIMM Parameters Documentation
## 参数来源与版本声明文档

---

## 1. 文档元数据

| 属性 | 值 |
|------|-----|
| **文档版本** | 1.0.0 |
| **SIMM版本** | 2.8+2506 |
| **发布日期** | 2025-02-24 |
| **参数校准日期** | 2025-06-01 |
| **生效日期** | 2025-12-06 |
| **ISDA文档日期** | 2025-10-14 |
| **文档用途** | 生产环境参数配置 |
| **维护者** | SIMM Challenger Team |

---

## 2. 参数来源声明

### 2.1 官方来源

| 参数类别 | 来源文档 | 章节 | URL |
|----------|----------|------|-----|
| 风险权重 (RW) | ISDA SIMM v2.8 | Section 5-9 | https://www.isda.org/simm/ |
| 相关性矩阵 (ρ, γ, ψ) | ISDA SIMM v2.8 | Section K | https://www.isda.org/simm/ |
| 集中度阈值 (T) | ISDA SIMM v2.8 | Section 5-9 | https://www.isda.org/simm/ |
| 期限结构 | ISDA SIMM v2.8 | Appendix A | https://www.isda.org/simm/ |
| 产品分类 | ISDA SIMM v2.8 | Section 3 | https://www.isda.org/simm/ |

### 2.2 版本控制策略

```yaml
versioning_strategy:
  format: "{major}.{minor}+{calibration_date}"
  example: "2.8+2506"
  
  components:
    major: "SIMM主版本 (2.x)"
    minor: "ISDA文档修订版本"
    calibration_date: "参数校准年月 (YYMM)"
  
  change_types:
    major_change: "公式结构变化 - 需要代码重构"
    minor_change: "参数数值变化 - 配置更新即可"
    patch_change: "文档勘误 - 无需代码变更"
```

---

## 3. 关键参数表

### 3.1 集中度阈值 (Concentration Thresholds)

#### 3.1.1 Interest Rate (Section 7)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 阈值 (High Volatility) | Tb_high | $28 billion | USD | 高波动货币 (EM) |
| 阈值 (Regular Volatility) | Tb_reg | $35 billion | USD | 常规货币 (G10) |
| 阈值 (Low Volatility) | Tb_low | $37 billion | USD | 低波动货币 |
| 同币种子曲线相关性 | φ | 98.1% | - | 不同期限结构间 |
| 跨币种相关性 | γ | 35% | - | 币种间聚合 |

**示例值计算：**
```python
# 示例：EUR利率组合集中度因子计算
sensitivities_eur = [1.5e9, 2.3e9, 0.8e9]  # 各期限敏感度(USD)
sum_abs_sens = sum(abs(s) for s in sensitivities_eur)  # 4.6e9
CR_b = max(1, sqrt(sum_abs_sens / Tb_reg))  # max(1, sqrt(4.6e9/35e9)) = 1.0
# 结果：无集中度调整 (CR=1.0表示分散良好)
```

#### 3.1.2 Credit Qualifying (Section 8)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 集中度阈值 | Tk | 55% | JT指数 | 同发行人汇总 |
| 集中度阈值 (指数) | Tk_idx | 55% | CJTI指数 | 指数成分集中度 |
| 浓度调整因子 | f_kl | min/max | - | 风险因子间 |

**示例值计算：**
```python
# 示例：某发行人敏感度集中度
sensitivities_issuer = [0.05, 0.03, 0.02]  # 各优先级敏感度
sum_abs_sens = sum(abs(s) for s in sensitivities_issuer)  # 0.10
CR_k = max(1, sqrt(sum_abs_sens / Tk))  # max(1, sqrt(0.10/0.55)) = 1.0

# 当集中度触发时 (假设 sum_abs_sens = 0.80)
CR_k_triggered = max(1, sqrt(0.80 / 0.55))  # = 1.21
# 结果：集中度调整因子 1.21 (21% add-on)
```

#### 3.1.3 Credit Non-Qualifying (Section 9)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 集中度阈值 | Tk | 55% | 证券化指数 | 证券化产品 |
| Bucket 1 (AAA) RW | RW_1 | 3.0% | - | RMBS/CMBS AAA级 |
| Bucket 4 (BBB) RW | RW_4 | 10.0% | - | 投资级 |
| Bucket 6 (Residual) RW | RW_6 | 100.0% | - | 非投资级/残差 |

**注意：** CRNQ不包含Base Correlation，仅使用Delta/Vega/Curvature

#### 3.1.4 Equity (Section 10)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 大市值阈值 | Tb_large | $15 billion | USD市值 | 大型股 |
| 小市值阈值 | Tb_small | $1.5 billion | USD市值 | 小型股 |
| 新兴市场乘数 | EM_mult | 1.5x | - | 新兴市场调整 |

#### 3.1.5 Commodity (Section 11)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 集中度阈值 | Tb | $2.1 billion | USD名义本金 | 各商品类别 |
| 跨桶相关性 | γ | 40% | - | 不同商品间 |

#### 3.1.6 FX (Section 12)

| 参数 | 符号 | 数值 | 单位 | 用途 |
|------|------|------|------|------|
| 集中度阈值 | Tb | $23 billion | USD名义本金 | 货币对 |
| 风险权重 (G10) | RW_g10 | 4.5% | - | 主要货币对 |
| 风险权重 (EM) | RW_em | 8.0% | - | 新兴市场货币 |

### 3.2 风险权重示例 (Risk Weights Examples)

#### Credit Qualifying (CRQ) - 精选

| Bucket | 类别描述 | Delta RW | Vega RW |
|--------|----------|----------|---------|
| 1 | Sovereign (AAA/AA) | 0.5% | 1.0% |
| 2 | Sovereign (A/BBB) | 1.0% | 2.0% |
| 4 | Corporate (Investment Grade) | 1.5% | 3.0% |
| 7 | Corporate (High Yield) | 5.0% | 10.0% |
| 10 | Securitization (Qualifying) | 10.0% | 20.0% |
| 12 | Residual | 17.0% | 34.0% |

#### Credit Non-Qualifying (CRNQ) - 精选

| Bucket | 评级类别 | Delta RW | Vega RW |
|--------|----------|----------|---------|
| 1 | AAA/AA | 3.0% | 6.0% |
| 2 | A | 6.0% | 12.0% |
| 3 | BBB | 10.0% | 20.0% |
| 4 | BB | 25.0% | 50.0% |
| 5 | B及以下 | 50.0% | 100.0% |
| 6 | Residual | 100.0% | 200.0% |

### 3.3 相关性矩阵示例

#### Credit Qualifying - 桶内相关性 (Section 8)

```
        1     2     3     4     5     6     7     8     9    10    11    12
1    1.00  0.75  0.75  0.65  0.55  0.45  0.45  0.35  0.35  0.35  0.35  0.00
2    0.75  1.00  0.75  0.75  0.65  0.55  0.45  0.45  0.35  0.35  0.35  0.00
3    0.75  0.75  1.00  0.75  0.75  0.65  0.55  0.45  0.45  0.35  0.35  0.00
4    0.65  0.75  0.75  1.00  0.75  0.75  0.65  0.55  0.45  0.45  0.35  0.00
5    0.55  0.65  0.75  0.75  1.00  0.75  0.75  0.65  0.55  0.45  0.35  0.00
6    0.45  0.55  0.65  0.75  0.75  1.00  0.75  0.75  0.65  0.55  0.35  0.00
7    0.45  0.45  0.55  0.65  0.75  0.75  1.00  0.75  0.75  0.65  0.35  0.00
8    0.35  0.45  0.45  0.55  0.65  0.75  0.75  1.00  0.75  0.75  0.35  0.00
9    0.35  0.35  0.45  0.45  0.55  0.65  0.75  0.75  1.00  0.75  0.35  0.00
10   0.35  0.35  0.35  0.45  0.45  0.55  0.65  0.75  0.75  1.00  0.35  0.00
11   0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  0.35  1.00  0.00
12   0.00  0.00  0.00  0.00  0.00  0.00  0.00  0.00  0.00  0.00  0.00  1.00
```

---

## 4. 参数更新日志

| 日期 | 版本 | 变更类型 | 变更内容 | 影响范围 |
|------|------|----------|----------|----------|
| 2025-02-24 | 2.8+2506 | 创建 | 初始参数文档 | 全量 |
| 2025-06-01 | - | 计划 | 参数校准更新 | 待发布 |
| 2025-12-06 | - | 计划 | 正式生效 | 生产环境 |

---

## 5. 使用指南

### 5.1 生产环境加载

```python
from simm_challenger.config import SIMMParams

# 加载已验证的参数配置
params = SIMMParams.from_yaml("config/parameters.yaml")

# 验证版本匹配
assert params.version == "2.8+2506", "参数版本不匹配"
assert params.calibration_date == "2025-06-01", "校准日期不匹配"

# 使用参数计算
margin = calculator.calculate(trades, params)
```

### 5.2 代码中引用规范

```python
# ✅ 正确做法：从外部配置加载
CONCENTRATION_THRESHOLD_CREDIT = params.credit_qualifying.threshold

# ❌ 错误做法：硬编码参数
CONCENTRATION_THRESHOLD_CREDIT = 0.55  # 不要这样做！
```

---

## 6. 校验与合规

### 6.1 参数校验脚本

```bash
# 验证参数文件完整性
python scripts/validate_parameters.py --version 2.8+2506

# 对比ISDA官方文档
python scripts/compare_isda_params.py --source isda_simm_v2.8.pdf

# 生成参数校验报告
python scripts/generate_param_report.py --output reports/
```

### 6.2 签名校验

| 文件 | SHA256校验和 | 生成日期 |
|------|--------------|----------|
| parameters.yaml | (待生成) | 2025-02-24 |
| parameters.json | (待生成) | 2025-02-24 |
| parameters.md | (待生成) | 2025-02-24 |

---

*本文档为SIMM Challenger生产系统的权威参数来源。任何参数变更必须经过版本控制流程，并在本文档中更新记录。*
