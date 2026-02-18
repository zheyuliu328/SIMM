#!/bin/bash
# ============================================================
# AI Agent 容灾备份与恢复脚本
# 支持: OpenClaw / Claude Code / OpenCode / OpenViking
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="$HOME/.ai_agent_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ai_agent_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# 关键路径配置
declare -A PATHS=(
    ["openclaw_config"]="$HOME/.openclaw"
    ["openclaw_workspace"]="$HOME/.openclaw/agents/main/workspace"
    ["openviking_config"]="$HOME/.openviking"
    ["claude_skills"]="$HOME/.claude/skills"
    ["ai_skills"]="$HOME/Documents/AI_SKILLS"
    ["ollama_models"]="$HOME/.ollama"
    ["qmd_config"]="$HOME/.qmd"
)

# ==================== 函数定义 ====================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查路径是否存在
check_path() {
    local path=$1
    if [ -e "$path" ]; then
        echo "exists"
    else
        echo "missing"
    fi
}

# 获取目录大小
get_size() {
    local path=$1
    if [ -e "$path" ]; then
        du -sh "$path" 2>/dev/null | cut -f1
    else
        echo "N/A"
    fi
}

# ==================== 备份功能 ====================

backup_all() {
    log_info "开始备份 AI Agent 系统..."
    
    # 创建备份目录
    mkdir -p "$BACKUP_PATH"
    
    # 备份各组件
    for name in "${!PATHS[@]}"; do
        local path="${PATHS[$name]}"
        local status=$(check_path "$path")
        local size=$(get_size "$path")
        
        if [ "$status" = "exists" ]; then
            log_info "备份 $name ($size)..."
            
            # 使用 tar 备份，排除缓存和大文件
            tar czf "$BACKUP_PATH/${name}.tar.gz" \
                --exclude='*.log' \
                --exclude='node_modules' \
                --exclude='.venv' \
                --exclude='__pycache__' \
                --exclude='*.pyc' \
                -C "$(dirname "$path")" \
                "$(basename "$path")" 2>/dev/null || {
                log_warn "$name 备份失败，可能正在使用"
            }
        else
            log_warn "$name 不存在，跳过"
        fi
    done
    
    # 创建备份清单
    cat > "$BACKUP_PATH/backup_manifest.txt" <> EOF
AI Agent 备份清单
==================
备份时间: $(date)
备份名称: $BACKUP_NAME

包含组件:
EOF
    
    for name in "${!PATHS[@]}"; do
        local path="${PATHS[$name]}"
        local status=$(check_path "$path")
        local size=$(get_size "$path")
        echo "- $name: $status ($size)" >> "$BACKUP_PATH/backup_manifest.txt"
    done
    
    # 创建恢复脚本
    create_restore_script
    
    # 压缩整个备份
    log_info "压缩备份..."
    cd "$BACKUP_DIR"
    tar czf "${BACKUP_NAME}.final.tar.gz" "$BACKUP_NAME"
    rm -rf "$BACKUP_PATH"
    
    log_success "备份完成: $BACKUP_DIR/${BACKUP_NAME}.final.tar.gz"
    log_info "备份大小: $(du -sh "$BACKUP_DIR/${BACKUP_NAME}.final.tar.gz" | cut -f1)"
}

# 创建恢复脚本
create_restore_script() {
    cat > "$BACKUP_PATH/restore.sh" <> 'EOF'
#!/bin/bash
# AI Agent 恢复脚本
# 使用方法: bash restore.sh

set -e

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔄 恢复 AI Agent 系统"
echo "===================="
echo ""

# 确认
read -p "确定要恢复吗? 这会覆盖现有配置! (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "取消恢复"
    exit 1
fi

# 恢复各组件
for archive in "$BACKUP_DIR"/*.tar.gz; do
    if [ -f "$archive" ]; then
        name=$(basename "$archive" .tar.gz)
        echo "恢复 $name..."
        tar xzf "$archive" -C "$HOME"
    fi
done

echo "✅ 恢复完成"
echo "请重启相关服务:"
echo "  - OpenClaw: openclaw gateway restart"
echo "  - Ollama: ollama serve &"
EOF
    chmod +x "$BACKUP_PATH/restore.sh"
}

# ==================== 健康检查 ====================

health_check() {
    log_info "运行健康检查..."
    
    local issues=0
    
    echo ""
    echo "组件状态检查:"
    echo "=============="
    
    # 检查 OpenClaw
    if command -v openclaw &> /dev/null; then
        local version=$(openclaw --version 2>&1 | head -1)
        log_success "OpenClaw: $version"
    else
        log_error "OpenClaw: 未安装"
        ((issues++))
    fi
    
    # 检查 Ollama
    if command -v ollama &> /dev/null; then
        if pgrep -x "ollama" > /dev/null; then
            log_success "Ollama: 运行中"
            log_info "  模型: $(ollama list 2>/dev/null | wc -l) 个"
        else
            log_warn "Ollama: 已安装但未运行"
            log_info "  启动命令: ollama serve &"
        fi
    else
        log_warn "Ollama: 未安装 (可选)"
    fi
    
    # 检查 OpenViking
    if python3 -c "import openviking" 2>/dev/null; then
        log_success "OpenViking: 已安装"
    else
        log_warn "OpenViking: 未安装 (可选)"
    fi
    
    # 检查配置
    echo ""
    echo "配置检查:"
    echo "========="
    
    for name in "${!PATHS[@]}"; do
        local path="${PATHS[$name]}"
        local status=$(check_path "$path")
        local size=$(get_size "$path")
        
        if [ "$status" = "exists" ]; then
            log_success "$name: 存在 ($size)"
        else
            log_warn "$name: 不存在"
        fi
    done
    
    # 检查端口冲突
    echo ""
    echo "端口检查:"
    echo "========="
    
    local ports=("18789" "18800" "18888" "11434")
    local port_names=("OpenClaw Gateway" "OpenClaw Browser" "OpenViking" "Ollama")
    
    for i in "${!ports[@]}"; do
        local port="${ports[$i]}"
        local name="${port_names[$i]}"
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_success "$name (端口 $port): 运行中"
        else
            log_warn "$name (端口 $port): 未运行"
        fi
    done
    
    echo ""
    if [ $issues -eq 0 ]; then
        log_success "健康检查通过!"
    else
        log_warn "发现 $issues 个问题"
    fi
    
    return $issues
}

# ==================== 自动修复 ====================

auto_fix() {
    log_info "尝试自动修复..."
    
    # 修复 Ollama 未运行
    if command -v ollama &> /dev/null && ! pgrep -x "ollama" > /dev/null; then
        log_info "启动 Ollama..."
        ollama serve &
        sleep 2
        if pgrep -x "ollama" > /dev/null; then
            log_success "Ollama 已启动"
        fi
    fi
    
    # 检查模型
    if command -v ollama &> /dev/null; then
        if ! ollama list | grep -q "nomic-embed-text"; then
            log_warn "缺少 nomic-embed-text 模型"
            log_info "下载命令: ollama pull nomic-embed-text"
        fi
    fi
    
    # 修复权限
    if [ -d "$HOME/.openclaw" ]; then
        chmod -R u+rw "$HOME/.openclaw" 2>/dev/null || true
    fi
    
    log_success "自动修复完成"
}

# ==================== 清理功能 ====================

cleanup() {
    log_info "清理临时文件..."
    
    # 清理旧的备份 (保留最近 10 个)
    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t *.final.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
        log_success "已清理旧备份 (保留最近 10 个)"
    fi
    
    # 清理日志
    if [ -d "$HOME/.openviking/logs" ]; then
        find "$HOME/.openviking/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        log_success "已清理 7 天前的日志"
    fi
    
    # 清理缓存
    if [ -d "$HOME/.openclaw/agents/main/workspace/.cache" ]; then
        rm -rf "$HOME/.openclaw/agents/main/workspace/.cache"/* 2>/dev/null || true
        log_success "已清理工作区缓存"
    fi
}

# ==================== 主菜单 ====================

show_menu() {
    echo ""
    echo "AI Agent 容灾管理系统"
    echo "====================="
    echo ""
    echo "1. 完整备份"
    echo "2. 健康检查"
    echo "3. 自动修复"
    echo "4. 清理临时文件"
    echo "5. 查看备份列表"
    echo "6. 退出"
    echo ""
}

# ==================== 主程序 ====================

main() {
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    if [ $# -eq 0 ]; then
        # 交互模式
        while true; do
            show_menu
            read -p "选择操作 (1-6): " choice
            
            case $choice in
                1) backup_all ;;
                2) health_check ;;
                3) auto_fix ;;
                4) cleanup ;;
                5) ls -lh "$BACKUP_DIR"/*.final.tar.gz 2>/dev/null || echo "暂无备份" ;;
                6) log_info "退出"; exit 0 ;;
                *) log_error "无效选择" ;;
            esac
            
            echo ""
            read -p "按回车继续..."
        done
    else
        # 命令行模式
        case $1 in
            backup) backup_all ;;
            check) health_check ;;
            fix) auto_fix ;;
            cleanup) cleanup ;;
            *) echo "用法: $0 [backup|check|fix|cleanup]" ;;
        esac
    fi
}

# 运行主程序
main "$@"
