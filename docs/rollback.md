# 回滚与事故 SOP

## 文档信息
- **版本**: 1.0.0
- **日期**: 2026-02-08
- **适用范围**: fct, nlp-factor, credit-one

---

## 1. 回滚 SOP (Rollback SOP)

### 1.1 触发条件

立即启动回滚的情况：
- 生产数据损坏或丢失
- 模型预测结果异常（PD > 99% 或 < 0%）
- 系统性能严重下降（> 5分钟无响应）
- 安全事件（未授权访问、数据泄露）

### 1.2 数据库回滚

```bash
#!/bin/bash
# scripts/rollback_db.sh - 数据库回滚脚本

set -euo pipefail

DB_NAME="${1:-credit_risk.db}"
BACKUP_DIR="./backups"
TIMESTAMP="${2:-$(date +%Y%m%d_%H%M%S)}"

echo "[ROLLBACK] Starting database rollback..."
echo "[ROLLBACK] Target DB: $DB_NAME"
echo "[ROLLBACK] Backup timestamp: $TIMESTAMP"

# 1. 验证备份存在
BACKUP_FILE="$BACKUP_DIR/${DB_NAME%.db}_${TIMESTAMP}.db"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "[ERROR] Backup not found: $BACKUP_FILE"
    echo "[INFO] Available backups:"
    ls -la "$BACKUP_DIR"/*.db 2>/dev/null || echo "No backups found"
    exit 1
fi

# 2. 创建当前状态快照（用于可能的回滚回滚）
CURRENT_SNAPSHOT="$BACKUP_DIR/${DB_NAME%.db}_pre_rollback_$(date +%Y%m%d_%H%M%S).db"
cp "$DB_NAME" "$CURRENT_SNAPSHOT"
echo "[ROLLBACK] Current state saved to: $CURRENT_SNAPSHOT"

# 3. 停止相关服务
echo "[ROLLBACK] Stopping services..."
pkill -f "python main.py" || true
pkill -f "streamlit run" || true
sleep 2

# 4. 执行回滚
echo "[ROLLBACK] Restoring from backup..."
cp "$BACKUP_FILE" "$DB_NAME"

# 5. 验证回滚
echo "[ROLLBACK] Verifying database integrity..."
sqlite3 "$DB_NAME" "PRAGMA integrity_check;"
sqlite3 "$DB_NAME" "SELECT COUNT(*) FROM loan_staging;"

echo "[ROLLBACK] Database rollback completed successfully!"
echo "[ROLLBACK] Restored from: $BACKUP_FILE"
```

### 1.3 配置回滚

```bash
#!/bin/bash
# scripts/rollback_config.sh - 配置回滚脚本

set -euo pipefail

CONFIG_FILE="${1:-config/config.yaml}"
BACKUP_DIR="./backups/config"
VERSION="${2:-}"

echo "[ROLLBACK] Starting config rollback..."

if [[ -z "$VERSION" ]]; then
    # 列出可用版本
    echo "[INFO] Available config versions:"
    ls -la "$BACKUP_DIR"/config_*.yaml 2>/dev/null || echo "No backups found"
    exit 0
fi

BACKUP_FILE="$BACKUP_DIR/config_$VERSION.yaml"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "[ERROR] Config backup not found: $BACKUP_FILE"
    exit 1
fi

# 备份当前配置
cp "$CONFIG_FILE" "$BACKUP_DIR/config_$(date +%Y%m%d_%H%M%S).yaml"

# 回滚配置
cp "$BACKUP_FILE" "$CONFIG_FILE"
echo "[ROLLBACK] Config restored to version: $VERSION"
```

### 1.4 模型回滚

```bash
#!/bin/bash
# scripts/rollback_model.sh - 模型回滚脚本

set -euo pipefail

MODEL_DIR="./artifacts/models"
VERSION="${1:-}"

echo "[ROLLBACK] Starting model rollback..."

if [[ -z "$VERSION" ]]; then
    echo "[INFO] Available model versions:"
    ls -la "$MODEL_DIR"/model_*.pkl 2>/dev/null || echo "No models found"
    exit 0
fi

MODEL_FILE="$MODEL_DIR/model_$VERSION.pkl"
if [[ ! -f "$MODEL_FILE" ]]; then
    echo "[ERROR] Model not found: $MODEL_FILE"
    exit 1
fi

# 备份当前模型
cp "$MODEL_DIR/current_model.pkl" "$MODEL_DIR/model_$(date +%Y%m%d_%H%M%S).pkl" 2>/dev/null || true

# 回滚模型
cp "$MODEL_FILE" "$MODEL_DIR/current_model.pkl"
echo "[ROLLBACK] Model restored to version: $VERSION"
```

---

## 2. 事故响应 SOP (Incident SOP)

### 2.1 事故分级

| 级别 | 定义 | 响应时间 | 通知范围 |
|------|------|----------|----------|
| P0 - Critical | 生产环境不可用 / 数据丢失 | 15 分钟 | 全员 + 管理层 |
| P1 - High | 核心功能受损 / 安全风险 | 1 小时 | 团队负责人 |
| P2 - Medium | 非核心功能异常 | 4 小时 | 相关开发人员 |
| P3 - Low | 轻微问题 / 优化建议 | 24 小时 | 问题跟踪系统 |

### 2.2 响应流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 发现    │───▶│ 定级    │───▶│ 止损    │───▶│ 修复    │───▶│ 复盘    │
│ Detect  │    │ Triage  │    │ Contain │    │ Fix     │    │ Review  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  监控告警      影响评估      启动回滚       验证修复       文档更新
  用户反馈      分级判定      隔离问题       回归测试       流程改进
```

### 2.3 止损检查清单

```bash
# incident_response.sh - 事故响应检查清单

echo "=== 事故响应检查清单 ==="
echo ""

echo "[ ] 1. 确认事故范围和影响"
echo "    - 受影响的用户数量"
echo "    - 受影响的数据范围"
echo "    - 受影响的功能模块"
echo ""

echo "[ ] 2. 启动止损措施"
echo "    - 停止相关服务: pkill -f 'python main.py'"
echo "    - 禁用危险功能: export DISABLE_RISKY_OPS=1"
echo "    - 切换到只读模式: export READONLY_MODE=1"
echo ""

echo "[ ] 3. 保护现场"
echo "    - 保存日志: cp logs/app.log backups/incident_$(date +%Y%m%d_%H%M%S).log"
echo "    - 保存数据库状态: cp *.db backups/"
echo "    - 记录当前进程: ps aux > backups/processes_$(date +%Y%m%d_%H%M%S).txt"
echo ""

echo "[ ] 4. 通知相关人员"
echo "    - P0: 立即电话通知"
echo "    - P1: Slack/钉钉通知"
echo "    - P2/P3: 工单系统记录"
echo ""

echo "[ ] 5. 评估是否需要回滚"
echo "    - 数据是否损坏？"
echo "    - 服务是否可用？"
echo "    - 回滚是否能解决问题？"
echo ""
```

### 2.4 事故报告模板

```markdown
# 事故报告

## 基本信息
- **事故编号**: INC-YYYYMMDD-XXX
- **发现时间**: YYYY-MM-DD HH:MM
- **定级**: P0/P1/P2/P3
- **报告人**: 

## 事故描述
### 现象
[描述观察到的异常现象]

### 影响范围
- 受影响服务:
- 受影响用户:
- 受影响数据:

## 时间线
| 时间 | 事件 |
|------|------|
| HH:MM | 事故发生 |
| HH:MM | 监控告警 |
| HH:MM | 开始响应 |
| HH:MM | 止损完成 |
| HH:MM | 修复完成 |
| HH:MM | 服务恢复 |

## 根因分析
[详细描述事故的根本原因]

## 修复措施
[描述采取的修复措施]

## 预防措施
- [ ] 改进 1
- [ ] 改进 2

## 经验教训
[总结经验教训]
```

---

## 3. 备份策略

### 3.1 自动备份配置

```python
# src/utils/backup.py
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

class BackupManager:
    """自动备份管理器"""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def backup_database(self, db_path: str) -> str:
        """备份数据库"""
        db_path = Path(db_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{db_path.stem}_{timestamp}{db_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # 先执行 SQLite 备份命令确保一致性
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA wal_checkpoint;")
        conn.close()
        
        shutil.copy2(db_path, backup_path)
        return str(backup_path)
    
    def list_backups(self, prefix: str = "") -> list:
        """列出备份文件"""
        pattern = f"{prefix}*.db" if prefix else "*.db"
        return sorted(self.backup_dir.glob(pattern), reverse=True)
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份，保留最近 N 个"""
        backups = self.list_backups()
        for old_backup in backups[keep_count:]:
            old_backup.unlink()
            print(f"[CLEANUP] Removed old backup: {old_backup}")
```

### 3.2 备份保留策略

| 备份类型 | 保留数量 | 保留时间 |
|----------|----------|----------|
| 数据库 | 最近 10 个 | 30 天 |
| 配置 | 最近 20 个 | 90 天 |
| 模型 | 最近 5 个 | 永久 |
| 日志 | 最近 30 个 | 7 天 |

---

## 4. 演练计划

### 4.1 月度演练
- 数据库回滚演练
- 配置回滚演练
- 事故响应流程演练

### 4.2 季度演练
- 完整灾难恢复演练
- 跨团队协作演练
- 外部依赖故障演练
