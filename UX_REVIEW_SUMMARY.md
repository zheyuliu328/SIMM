# 三项目用户体验审查汇总

**审查者**: Alpha (用户体验与文档产品化)  
**审查日期**: 2026-02-08  
**项目**: Credit One / FCT / NLP Factor

---

## 📊 快速对比

| 维度 | Credit One | FCT | NLP Factor |
|------|------------|-----|------------|
| **3分钟上手** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **10分钟跑通** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **30分钟真实数据** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **文档完整性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **上手难度** | 低 | 中 | 中 |

---

## 🚀 3分钟上手路径对比

### Credit One (最简单)
```bash
pip install -r requirements.txt
python model_validation.py  # 或 streamlit run app.py
```
- ✅ 无需外部数据，合成数据开箱即用
- ✅ 输出直观（AUC/PSI 指标）
- ⚠️ 依赖 XGBoost，可能安装失败

### FCT (中等)
```bash
pip install -r requirements.txt
python scripts/setup_project.py  # 自动下载数据
python main.py
```
- ✅ 自动数据下载（Kaggle）
- ⚠️ 需要 Kaggle 认证或手动下载
- ⚠️ 初始化步骤较多

### NLP Factor (中等)
```bash
pip install -r requirements.txt
bash run.sh  # 自动检测 Demo/Production 模式
```
- ✅ 一键脚本，自动检测模式
- ⚠️ 真实数据需要 API Key
- ⚠️ 模型下载（Transformers）耗时

---

## 🎯 10分钟跑通对比

| 项目 | 核心输出 | 理解难度 | 关键概念 |
|------|----------|----------|----------|
| **Credit One** | 模型验证报告 + Streamlit 界面 | ⭐⭐ | AUC, PSI, SHAP |
| **FCT** | 审计报告 + 对账结果 | ⭐⭐⭐ | Orphan Records, 欺诈检测 |
| **NLP Factor** | IC 分析 + 分位数回测 | ⭐⭐⭐⭐ | Rank IC, 均值回归, 因子验证 |

### 最易混淆概念
- **Credit One**: PSI (Population Stability Index) 阈值 0.25
- **FCT**: Orphan Records (孤儿记录) 识别逻辑
- **NLP Factor**: 负 IC 表示均值回归信号（反直觉）

---

## 📊 30分钟真实数据接入对比

### 配置复杂度

| 项目 | 配置步骤 | 外部依赖 | 难度 |
|------|----------|----------|------|
| **Credit One** | 修改 SQL 映射 + 数据加载逻辑 | 百行/央行征信 | ⭐⭐⭐⭐ |
| **FCT** | ERP 连接配置 + 字段映射 | SAP/Oracle ERP | ⭐⭐⭐⭐⭐ |
| **NLP Factor** | API Key 配置 + 股票池设置 | EventRegistry API | ⭐⭐⭐ |

### 真实数据接入建议

**Credit One**:
- 需要金融数据合规授权
- 建议先使用公开数据集（如 LendingClub）测试

**FCT**:
- ERP 集成需要企业 IT 配合
- 建议先用 CSV 文件模拟 ERP 数据

**NLP Factor**:
- API Key 获取最简单（免费注册）
- 注意请求频率限制

---

## ❓ FAQ 高频问题汇总

### 跨项目共性问题

| 问题 | 影响项目 | 根本原因 | 统一解决方案 |
|------|----------|----------|--------------|
| Python 版本过低 | 全部 | 依赖要求 3.8+ | 统一要求 Python 3.9+ |
| 依赖安装失败 | 全部 | 编译依赖缺失 | 提供 conda environment.yml |
| 中文字符乱码 | FCT, NLP | 编码问题 | 统一使用 UTF-8 |

### 项目特有问题

**Credit One**:
- Q: SHAP 图空白 → A: 安装 matplotlib
- Q: 实时股价加载失败 → A: 使用本地缓存

**FCT**:
- Q: Kaggle 下载失败 → A: 手动下载数据
- Q: 对账不匹配 → A: 检查字段映射

**NLP Factor**:
- Q: API Key 无效 → A: 检查 .env 格式
- Q: 负 IC 解释 → A: 均值回归策略

---

## 🚧 上手阻断点汇总

### P0 (阻断性) - 需立即修复

| 项目 | 问题 | 建议修复 |
|------|------|----------|
| Credit One | XGBoost 安装失败 (Mac M1) | 提供 `--no-binary` 安装命令 |
| FCT | Kaggle 认证复杂 | 提供手动下载指引 |
| NLP Factor | torch 体积过大 | 提供 CPU-only 安装选项 |

### P1 (高优先级) - 影响体验

| 项目 | 问题 | 建议修复 |
|------|------|----------|
| Credit One | Streamlit 端口冲突 | 自动检测可用端口 |
| FCT | 数据库权限问题 | 添加权限检查脚本 |
| NLP Factor | API 限流无提示 | 添加速率限制警告 |

### P2 (中优先级) - 优化体验

| 项目 | 问题 | 建议修复 |
|------|------|----------|
| Credit One | 合成数据与真实差异大 | 添加数据分布对比 |
| FCT | 时区处理不一致 | 统一 UTC 时间戳 |
| NLP Factor | 回测周期短 | 提供历史数据下载 |

---

## 📸 截图计划汇总

### 必截图 (P0)

| 项目 | 截图位置 | 用途 |
|------|----------|------|
| Credit One | Streamlit 主界面 | README 展示 |
| Credit One | SHAP 解释图 | 模型可解释性 |
| FCT | 审计报告总览 | 对账结果展示 |
| FCT | 孤儿记录列表 | 核心功能展示 |
| NLP Factor | IC 时间序列 | 因子有效性 |
| NLP Factor | 分位数回测 | 策略收益 |

### 选截图 (P1/P2)

| 项目 | 截图位置 | 用途 |
|------|----------|------|
| Credit One | 压力测试界面 | 高级功能 |
| FCT | RBAC 权限矩阵 | 安全架构 |
| NLP Factor | 风格相关性热力图 | 因子独立性 |

---

## 🎯 改进建议

### 短期 (1-2周)

1. **统一入口脚本**
   - 三个项目都提供 `run.sh` / `run.bat`
   - 自动检测环境并给出提示

2. **Docker 化**
   - 提供 Dockerfile 解决依赖问题
   - 特别针对 XGBoost/torch 安装困难

3. **示例数据增强**
   - Credit One: 提供 LendingClub 示例
   - FCT: 提供 CSV 导入模板
   - NLP Factor: 提供离线新闻样本

### 中期 (1-2月)

1. **交互式教程**
   - Jupyter Notebook 分步教程
   - 每个关键概念配代码示例

2. **视频演示**
   - 3分钟上手视频
   - 真实数据接入演示

3. **在线 Demo**
   - Streamlit Cloud 部署 Credit One
   - 静态报告展示 FCT/NLP

---

## 📁 产出文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| Credit One UX Guide | `credit-one/UX_GUIDE.md` | 完整用户体验文档 |
| FCT UX Guide | `fct/UX_GUIDE.md` | 完整用户体验文档 |
| NLP Factor UX Guide | `nlp-factor/UX_GUIDE.md` | 完整用户体验文档 |
| 审查汇总 | `UX_REVIEW_SUMMARY.md` | 本文档 |

---

**审查结论**: 三个项目文档基础良好，Credit One 上手最简单，FCT 企业级功能最完整，NLP Factor 研究属性最强。建议优先解决 P0 阻断点，统一提供 Docker 镜像降低上手门槛。
