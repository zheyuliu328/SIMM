# 三项目文档产品化 - 修改清单汇总

**任务**: 为 FCT、NLP-Factor、Credit-One 三个项目产出并落地用户路径文档
**负责人**: Alpha (用户路径与文档产品化)
**日期**: 2026-02-08

---

## 一、修改清单总览

### 1. FCT (Financial Control Tower)

| 文件路径 | 操作 | 状态 |
|:---------|:-----|:-----|
| `fct/README.md` | 重构 | ✅ 已生成 README_NEW.md |
| `fct/docs/quickstart.md` | 新建 | ✅ 已完成 |
| `fct/docs/configuration.md` | 新建 | ✅ 已完成 |
| `fct/docs/faq.md` | 新建 | ✅ 已完成 |

### 2. NLP-Factor

| 文件路径 | 操作 | 状态 |
|:---------|:-----|:-----|
| `nlp-factor/README.md` | 重构 | ✅ 已生成 README_NEW.md |
| `nlp-factor/docs/quickstart.md` | 新建 | ✅ 已完成 |
| `nlp-factor/docs/configuration.md` | 新建 | ✅ 已完成 |
| `nlp-factor/docs/faq.md` | 新建 | ✅ 已完成 |

### 3. Credit-One

| 文件路径 | 操作 | 状态 |
|:---------|:-----|:-----|
| `credit-one/README.md` | 重构 | ✅ 已生成 README_NEW.md |
| `credit-one/docs/quickstart.md` | 新建 | ✅ 已完成 |
| `credit-one/docs/configuration.md` | 新建 | ✅ 已完成 |
| `credit-one/docs/faq.md` | 新建 | ✅ 已完成 |
| `credit-one/docs/` | 新建目录 | ✅ 已完成 |

---

## 二、README 顶部结构统一

每个项目的 README 统一采用以下结构:

```markdown
# 项目名称

[徽章]

**一句话定位**: 面向风险建模、审计与研究的 [具体功能] 工具

---

## 核心能力 (3条)

1. [能力1]
2. [能力2]
3. [能力3]

---

## Quickstart (3 分钟)

```bash
# 三行命令
command_1
command_2
command_3
```

**输出工件**:
- 工件1
- 工件2
- 工件3

---

## 文档导航

| 文档 | 内容 | 阅读时间 |
|:-----|:-----|:---------|
| docs/quickstart.md | ... | 10 分钟 |
| docs/configuration.md | ... | 30 分钟 |
| docs/faq.md | ... | 按需 |

---

## 项目结构

```
...
```

---

## 技术栈

...

---

## 作者

**Zheyu Liu** - 面向风险建模、审计与研究的工具开发

---

*面向风险建模、审计与研究的工具*
```

---

## 三、关键纠偏落实

### 3.1 监管合规描述纠偏

| 项目 | 原描述 | 修改后 |
|:-----|:-------|:-------|
| FCT | "Production-Ready ERP Audit System for Enterprise Financial Control" | "面向风险建模、审计与研究的 ERP 数据对账与欺诈检测工具" |
| NLP-Factor | "Production-grade factor research framework" | "面向量化研究的港股新闻情绪因子研究框架" |
| Credit-One | "Basel III / IFRS 9 compliant PD prediction" | "面向风险建模与研究的信用风险评分工具" |

### 3.2 删除的夸大描述

- ❌ "符合监管要求" - 无事实源支持
- ❌ "Production Ready" - 暗示生产就绪
- ❌ "SR 11-7 Compliant" - 无认证支持
- ❌ "Audit Ready" - 暗示审计合规
- ❌ "实时 Inference < 100ms" - 未经验证的性能声明
- ❌ "2500 TPS" - 未经验证的吞吐量声明

### 3.3 统计严谨性强化

**NLP-Factor**:
- 明确标注: "t-statistic = -1.30，当前数据量下尚未达到传统显著性阈值（|t| > 2）"
- 避免误导性陈述，强调需要 24 个月+数据

---

## 四、文档信息架构

### 4.1 用户路径设计

| 时间 | 目标 | 文档 |
|:-----|:-----|:-----|
| 3 分钟 | 完成安装并看到输出 | README Quickstart |
| 10 分钟 | 理解功能并验证输出 | docs/quickstart.md |
| 30 分钟 | 接入真实数据/配置 | docs/configuration.md |
| 按需 | 解决具体问题 | docs/faq.md |

### 4.2 文档内容规范

**quickstart.md**:
- 前置要求
- 分步骤指导（每步预估时间）
- 预期输出（可复制粘贴的示例）
- 验证步骤
- 故障速查表

**configuration.md**:
- 配置步骤
- 字段映射规范（表格形式）
- 常见失败点（现象/排查/解决）
- 验证清单
- 生产环境建议

**faq.md**:
- 按主题分类（安装/运行/配置/数据/模型）
- 问题-答案格式
- 包含代码示例

---

## 五、落地执行命令

### 5.1 FCT 项目

```bash
# 备份原 README
mv fct/README.md fct/README.md.bak

# 应用新 README
mv fct/README_NEW.md fct/README.md

# 确认文档文件
ls -la fct/docs/
# 应包含: quickstart.md, configuration.md, faq.md
```

### 5.2 NLP-Factor 项目

```bash
# 备份原 README
mv nlp-factor/README.md nlp-factor/README.md.bak

# 应用新 README
mv nlp-factor/README_NEW.md nlp-factor/README.md

# 确认文档文件
ls -la nlp-factor/docs/
# 应包含: quickstart.md, configuration.md, faq.md, data_lineage.md
```

### 5.3 Credit-One 项目

```bash
# 备份原 README
mv credit-one/README.md credit-one/README.md.bak

# 应用新 README
mv credit-one/README_NEW.md credit-one/README.md

# 确认文档文件
ls -la credit-one/docs/
# 应包含: quickstart.md, configuration.md, faq.md
```

---

## 六、验收标准

### 6.1 README 验收

- [ ] 一句话定位准确，无夸大
- [ ] 核心能力 3 条，具体可验证
- [ ] Quickstart 三行命令可复制运行
- [ ] 输出工件说明清晰
- [ ] 文档导航表格完整

### 6.2 docs/quickstart.md 验收

- [ ] 总阅读时间约 10 分钟
- [ ] 步骤带时间预估
- [ ] 预期输出可复制验证
- [ ] 包含验证步骤
- [ ] 故障速查表覆盖常见问题

### 6.3 docs/configuration.md 验收

- [ ] 总阅读时间约 30 分钟
- [ ] 字段映射规范（表格）
- [ ] 常见失败点（现象/排查/解决）
- [ ] 验证清单可勾选

### 6.4 docs/faq.md 验收

- [ ] 按主题分类
- [ ] 覆盖 5+ 个常见问题
- [ ] 包含代码示例

---

## 七、文件清单

### 生成的文件

```
workspace/
├── fct/
│   ├── README_NEW.md              # 新 README（待替换）
│   ├── REFACTOR_CHECKLIST.md      # 修改清单
│   └── docs/
│       ├── quickstart.md          # 10 分钟指南
│       ├── configuration.md       # 30 分钟配置
│       └── faq.md                 # FAQ
├── nlp-factor/
│   ├── README_NEW.md              # 新 README（待替换）
│   ├── REFACTOR_CHECKLIST.md      # 修改清单
│   └── docs/
│       ├── quickstart.md          # 10 分钟指南
│       ├── configuration.md       # 30 分钟配置
│       └── faq.md                 # FAQ
└── credit-one/
    ├── README_NEW.md              # 新 README（待替换）
    ├── REFACTOR_CHECKLIST.md      # 修改清单
    └── docs/
        ├── quickstart.md          # 10 分钟指南
        ├── configuration.md       # 30 分钟配置
        └── faq.md                 # FAQ
```

---

## 八、下一步行动

1. **审查**: 由主代理审查修改内容
2. **确认**: 用户确认修改方案
3. **应用**: 执行落地命令替换 README
4. **验证**: 验证文档链接和格式正确
5. **提交**: 提交到 Git 仓库

---

*生成时间: 2026-02-08*
*生成者: Alpha (用户路径与文档产品化)*
