# Product Requirements Comparison Analysis

## 文档对比
- **Word文档**: `CHALLENGE_MODEL_REPORT.docx` - Challenge Model技术规范
- **Excel文档**: `ShacomBank_Product list_202601_v1.31.xlsx` - 产品需求清单

---

## 1. Excel需求清单总结 (20个产品)

### FX Cash (4个产品)
| # | 产品名称 | VM Required | Existing Product | IM Required | 备注 |
|---|---------|-------------|------------------|-------------|------|
| 1 | FX Outright Forward | R | NR | Y | |
| 2 | Non Deliverable Forward | R | R | Y | |
| 3 | Fx Swap | R | NR | Y | |
| 4 | Time option (Option Dated Forward) | R | NR | Y | |

### FX Option (7个产品)
| # | 产品名称 | VM Required | Existing Product | IM Required | 备注 |
|---|---------|-------------|------------------|-------------|------|
| 5 | Vanilla Option (European Style) | R | R | Y | 含call/put, digital barrier等 |
| 6 | Digital Option (European style) | R | R | Y | |
| 7 | Digital Range Option (European style) | R | R | N | |
| 8 | Touch Options | R | R | N | one-touch/no-touch/double-touch |
| 9 | Barrier Options, KO/RKO | R | R | N | European/American style |
| 10 | Barrier Options, KI/RKI | R | R | N | European/American style |
| 11 | Barrier Options, KIKO | R | R | N | |

### Precious Metals (1个产品)
| # | 产品名称 | VM Required | Existing Product | IM Required | 备注 |
|---|---------|-------------|------------------|-------------|------|
| 12 | Gold Option (Vanilla, Digital) | R | R | N | European/American |

### Structured Products (8个产品)
| # | 产品名称 | VM Required | Existing Product | IM Required | 备注 |
|---|---------|-------------|------------------|-------------|------|
| 13 | TARF without EKI (Generic TARF) | R | R | Y | |
| 14 | TARF with EKI | R | R | Y | |
| 15 | Pivot TARF | R | R | Y | |
| 16 | Digital TARF | R | R | Y | |
| 17 | Interest Rate Range Accrual Swap | R | R | N | USD 10Y CMS |
| 18 | IRS (with ARR features) | R | R | Y | fixed-float/float-float |
| 19 | Basis Swap (with ARR features) | R | R | N | |
| 20 | Cross Currency Swap (with ARR) | R | R | Y | |

---

## 2. Word文档产品覆盖情况 (T001-T020)

### Tier 1: Linear Products (低风险)
| Product ID | 产品类型 | 风险类别 | Excel对应产品 |
|------------|---------|----------|---------------|
| T001, T002 | InterestRateSwap | InterestRate | ✅ IRS (with ARR features) |
| T004 | FXForward | FX | ✅ FX Outright Forward |
| T006 | CrossCurrencySwap | FX | ✅ Cross Currency Swap (with ARR) |
| T007, T009 | EquitySwap, EquityForward | Equity | ❌ 不在Excel列表中 |
| T012, T013 | CDS_Index_IG, CDS_AAA | CreditQualifying | ❌ 不在Excel列表中 |
| T018 | CommoditySwap | Commodity | ❌ 不在Excel列表中 |
| T020 | GoldForward | Commodity | ❌ Gold Forward vs Gold Option |

### Tier 2: Vanilla Options (中等风险)
| Product ID | 产品类型 | 主要风险 | Excel对应产品 |
|------------|---------|----------|---------------|
| T003 | Swaption | IR Vega | ❌ 不在Excel列表中 |
| T005 | FXOption | FX Vega | ✅ Vanilla Option (部分) |
| T008 | EquityOption | Equity Vega | ❌ 不在Excel列表中 |
| T019 | CommodityOption | Commodity Vega | ❌ 不在Excel列表中 |

### Tier 3: Credit Products (高风险)
| Product ID | 产品类型 | 信用评级 | Excel对应产品 |
|------------|---------|----------|---------------|
| T010, T011, T025 | CDS_IG | BBB+, A, BBB+ | ❌ 不在Excel列表中 |
| T012, T013 | CDS_Index_IG, CDS_AAA | AA, AAA | ❌ 不在Excel列表中 |
| T014, T015, T026 | CDS_HY | BB, B, BB- | ❌ 不在Excel列表中 |
| T016 | CDS_Distressed | CCC | ❌ 不在Excel列表中 |
| T017 | CDS_NoRating | None | ❌ 不在Excel列表中 |

### Tier 4: Exotic Products (关键风险 - Circuit Breaker)
| 产品类型 | 风险机制 | 公式问题 | Excel对应产品 |
|----------|---------|----------|---------------|
| Barrier (KO/KI) | Pin Risk near barrier | Vega → ∞ as Spot → Barrier | ✅ Barrier Options (部分) |
| Digital | Discontinuous payoff | Delta undefined at strike | ✅ Digital Option (部分) |
| TARF | Path dependency | Behavior changes near target | ✅ TARF variants (部分) |
| Touch | Binary trigger | Similar to Barrier | ✅ Touch Options |

---

## 3. 覆盖差距分析

### ✅ 已明确覆盖的产品 (7个)
1. **IRS (with ARR features)** → T001-T002 InterestRateSwap
2. **FX Outright Forward** → T004 FXForward
3. **Cross Currency Swap (with ARR)** → T006 CrossCurrencySwap
4. **Vanilla Option (European Style)** → T005 FXOption (部分)
5. **Digital Option** → Tier 4 Digital (部分)
6. **Barrier Options** → Tier 4 Barrier (部分)
7. **TARF variants** → Tier 4 TARF (部分)

### ❌ 缺失的产品 (13个)

#### FX Cash 类别缺失 (3个):
| # | 产品名称 | 严重程度 |
|---|---------|----------|
| 1 | Non Deliverable Forward | 🔴 高 - 常用产品 |
| 2 | Fx Swap | 🔴 高 - 常用产品 |
| 3 | Time option (Option Dated Forward) | 🟡 中 - 远期期权 |

#### FX Option 类别缺失 (4个):
| # | 产品名称 | 严重程度 |
|---|---------|----------|
| 4 | Digital Range Option | 🟡 中 - 范围数字期权 |
| 5 | Touch Options | 🟡 中 - 触碰期权 |
| 6 | Barrier Options (KI/RKI, KIKO) | 🔴 高 - 文档只提到KO/RKO |
| 7 | Vanilla Option中的barrier变体 | 🟡 中 - up-and-in/out等 |

#### Structured Products 类别缺失 (5个):
| # | 产品名称 | 严重程度 |
|---|---------|----------|
| 8 | TARF without EKI (Generic) | 🔴 高 - 明确需要 |
| 9 | TARF with EKI | 🔴 高 - 明确需要 |
| 10 | Pivot TARF | 🟡 中 - 变体产品 |
| 11 | Digital TARF | 🟡 中 - 变体产品 |
| 12 | Interest Rate Range Accrual Swap | 🟡 中 - CMS挂钩 |
| 13 | Basis Swap (with ARR) | 🟡 中 - 基础互换 |

#### Precious Metals 类别缺失 (1个):
| # | 产品名称 | 严重程度 |
|---|---------|----------|
| 14 | Gold Option (Vanilla, Digital) | 🟡 中 - 文档是GoldForward |

### ⚠️ 有但存在差异的产品 (4个)
1. **Vanilla Option**: Excel要求包括call/put, barrier变体, payout选择等；文档只提到Vanilla
2. **Barrier Options**: Excel区分KO/RKO, KI/RKI, KIKO；文档只笼统提到Barrier
3. **TARF**: Excel要求4种变体；文档只笼统提到TARF
4. **Gold产品**: Excel要求Gold Option；文档是GoldForward

---

## 4. 产品映射建议表

为了符合Excel要求，建议Word文档更新如下映射：

| Excel产品 | 建议Product ID | Tier分类 | Challenge Class |
|-----------|---------------|----------|-----------------|
| FX Outright Forward | T004 | 🟢 Tier 1 | LinearProductChallenge |
| Non Deliverable Forward | **T021** | 🟢 Tier 1 | LinearProductChallenge |
| Fx Swap | **T022** | 🟢 Tier 1 | LinearProductChallenge |
| Time option | **T023** | 🟡 Tier 2 | VanillaOptionChallenge |
| Vanilla Option (European) | T005 | 🟡 Tier 2 | VanillaOptionChallenge |
| Digital Option | **T024** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Digital Range Option | **T025** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Touch Options | **T026** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Barrier Options (KO/RKO) | **T027** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Barrier Options (KI/RKI) | **T028** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Barrier Options (KIKO) | **T029** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Gold Option | T020 或 **T030** | 🟡 Tier 2 | VanillaOptionChallenge |
| TARF without EKI | **T031** | 🔴 Tier 4 | ExoticCircuitBreaker |
| TARF with EKI | **T032** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Pivot TARF | **T033** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Digital TARF | **T034** | 🔴 Tier 4 | ExoticCircuitBreaker |
| Interest Rate Range Accrual Swap | **T035** | 🟠 Tier 3 | CreditProductChallenge? |
| IRS (with ARR) | T001-T002 | 🟢 Tier 1 | LinearProductChallenge |
| Basis Swap (with ARR) | **T036** | 🟢 Tier 1 | LinearProductChallenge |
| Cross Currency Swap (with ARR) | T006 | 🟢 Tier 1 | LinearProductChallenge |

---

## 5. 格式问题检查

### ✅ 格式良好的部分
1. **文档结构**: 有清晰的Table of Contents
2. **章节编号**: 使用层次化编号 (1, 1.1, 1.1.1等)
3. **表格格式**: 产品映射表格清晰
4. **层级标识**: 使用颜色标识风险层级 (🟢🟡🟠🔴)
5. **公式标注**: 公式有编号 (Formula 1, Formula 2等)

### ⚠️ 发现的格式问题

#### 问题1: 产品ID不连续
- **位置**: Section 7.2 Product Mapping
- **问题**: 产品ID从T001到T020，但Excel要求的产品不完全对应
- **建议**: 添加新的Product ID (T021-T036) 来覆盖缺失产品

#### 问题2: 公式渲染问题
- **位置**: 多个章节
- **问题**: 公式显示为LaTeX格式，可能有渲染问题
  - Example: "Where: -  = Risk Weight from Table 1-6"
  - Example: " = Correlation coefficient"
- **建议**: 这些公式占位符在Word中需要正确渲染

#### 问题3: 表格对齐问题
- **位置**: Section 7.2 Product Mapping (Table)
- **问题**: 表格列对齐在文本提取中看起来有些错位
- **建议**: 检查Word中的实际表格对齐

#### 问题4: 页眉/页脚
- **位置**: 文档开始
- **问题**: 提取的文本中没有明显的页眉/页脚标记
- **建议**: 确认Word文档有页眉(如文档标题)和页脚(如页码)

#### 问题5: 文档日期
- **位置**: 第7行
- **问题**: 日期显示为"February 26, 2026" - 这是一个未来日期
- **建议**: 确认日期是否正确

---

## 6. 总结与建议

### 覆盖情况统计
- **总需求产品**: 20个
- **明确覆盖**: 7个 (35%)
- **部分覆盖**: 4个 (20%)
- **完全缺失**: 9个 (45%)

### 关键建议

#### 高优先级 (必须添加):
1. **Non Deliverable Forward** - FX现金产品
2. **Fx Swap** - FX现金产品
3. **TARF所有4种变体** - 结构化产品，IM Required = Y

#### 中优先级 (建议添加):
4. Digital Range Option
5. Touch Options
6. Barrier Options (KI/RKI, KIKO variants)
7. Gold Option (vs GoldForward)
8. Time option
9. Interest Rate Range Accrual Swap
10. Basis Swap

#### 文档格式修复:
1. 确认公式渲染正确
2. 更新产品映射表格 (Section 7.2)
3. 修正文档日期 (如需要)
4. 确保页眉页脚完整

---

*分析报告生成时间: 2026-02-26*
*公式部分未做修改，仅做内容检查*
