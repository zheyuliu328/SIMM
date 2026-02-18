# Credit One 重构计划

## 目标
在 1.5 天内完成 Credit One、FCT、NLP 三个项目的业界标准重构

## 时间线 (2月8日全天)

### Phase 1: Credit One (8小时) - 2月8日 00:00-08:00
- [ ] 1.1 模型验证框架 (model_validation.py)
  - OOT (Out-of-Time) 验证
  - K-S 检验、CAP 曲线
  - 模型稳定性报告
- [ ] 1.2 评分卡校准文档 (scorecard_calibration.md)
  - PDO 完整推导
  - score-to-odds 映射表
  - 基准分数验证
- [ ] 1.3 PSI 监控增强 (psi_monitoring.py)
  - 标准阈值 0.1/0.25
  - 历史趋势日志
  - 预警机制
- [ ] 1.4 数据架构说明 (data_architecture.md)
  - 真实数据接入设计
  - 征信 API 接口规范
  - 数据流图
- [ ] 1.5 模型治理文档 (model_governance.md)
  - SR 11-7 三防线
  - 模型风险管理框架
  - 上线 checklist

### Phase 2: FCT (4小时) - 2月8日 08:00-12:00
- [ ] 2.1 Reconciliation Control Matrix
- [ ] 2.2 欺诈规则性能指标 (TP/FP/FN)
- [ ] 2.3 权限分离架构
- [ ] 2.4 真实 ERP 对接设计

### Phase 3: NLP (2小时) - 2月8日 12:00-14:00
- [ ] 3.1 IC 统计检验 (t-stat, p-value)
- [ ] 3.2 交易成本分析
- [ ] 3.3 数据说明文档

### Phase 4: 整合与测试 (4小时) - 2月8日 14:00-18:00
- [ ] 4.1 所有文档整合
- [ ] 4.2 README 更新
- [ ] 4.3 代码测试
- [ ] 4.4 Git 提交

### Phase 5: 面试准备 (2小时) - 2月8日 18:00-20:00
- [ ] 5.1 更新自我介绍 (强调项目迭代)
- [ ] 5.2 准备深挖问题应答
- [ ] 5.3 模拟面试

## 关键交付物

### Credit One
1. `model_validation.py` - 完整模型验证框架
2. `scorecard_calibration.md` - 评分卡校准推导
3. `psi_monitoring/` - PSI 历史日志
4. `data_architecture.md` - 数据架构设计
5. `model_governance.md` - 模型治理框架

### FCT
1. `reconciliation_matrix.md`
2. `fraud_rule_metrics.py`
3. `security_architecture.md`

### NLP
1. `statistical_tests.py`
2. `trading_cost_analysis.md`

## 面试强调点

"这个项目从原型迭代到生产就绪版本，我补充了："
- 完整的 OOT 验证和模型稳定性监控
- 符合 SR 11-7 的模型治理框架
- 真实数据接入架构设计
- 详细的校准文档和性能指标
