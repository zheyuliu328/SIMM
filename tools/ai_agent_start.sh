#!/bin/bash
# ============================================================
# 统一 AI Agent 启动脚本
# 启动所有服务并确保它们协同工作
# ============================================================

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     统一 AI Agent 系统启动器          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# ==================== 函数 ====================

check_service() {
    local name=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name (端口 $port)"
        return 0
    else
        echo -e "${RED}✗${NC} $name (端口 $port)"
        return 1
    fi
}

start_ollama() {
    echo -e "${YELLOW}▶${NC} 启动 Ollama..."
    
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}✗${NC} Ollama 未安装"
        echo "   运行: bash ~/.openclaw/agents/main/workspace/tools/install_ollama.sh"
        return 1
    fi
    
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama 已在运行"
    else
        ollama serve > ~/.ollama.log 2>&1 &
        sleep 2
        if pgrep -x "ollama" > /dev/null; then
            echo -e "${GREEN}✓${NC} Ollama 已启动"
        else
            echo -e "${RED}✗${NC} Ollama 启动失败"
            return 1
        fi
    fi
    
    # 检查模型
    echo "   检查模型..."
    if ollama list | grep -q "nomic-embed-text"; then
        echo -e "${GREEN}  ✓${NC} nomic-embed-text 已安装"
    else
        echo -e "${YELLOW}  !${NC} nomic-embed-text 未安装"
        echo "   运行: ollama pull nomic-embed-text"
    fi
    
    if ollama list | grep -q "llava"; then
        echo -e "${GREEN}  ✓${NC} llava 已安装"
    else
        echo -e "${YELLOW}  !${NC} llava 未安装 (可选)"
    fi
}

start_openclaw() {
    echo -e "${YELLOW}▶${NC} 启动 OpenClaw..."
    
    if ! command -v openclaw &> /dev/null; then
        echo -e "${RED}✗${NC} OpenClaw 未安装"
        return 1
    fi
    
    # 检查 Gateway
    if check_service "OpenClaw Gateway" "18789"; then
        echo -e "${GREEN}✓${NC} OpenClaw Gateway 已在运行"
    else
        echo "   启动 Gateway..."
        openclaw gateway start
        sleep 2
        if check_service "OpenClaw Gateway" "18789"; then
            echo -e "${GREEN}✓${NC} OpenClaw Gateway 已启动"
        else
            echo -e "${RED}✗${NC} OpenClaw Gateway 启动失败"
            return 1
        fi
    fi
    
    # 检查 Browser
    echo "   检查 Browser..."
    if check_service "OpenClaw Browser" "18800"; then
        echo -e "${GREEN}  ✓${NC} Browser 已运行"
    else
        echo -e "${YELLOW}  !${NC} Browser 未运行 (可选)"
        echo "   运行: openclaw browser start"
    fi
}

check_openviking() {
    echo -e "${YELLOW}▶${NC} 检查 OpenViking..."
    
    if python3 -c "import openviking" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} OpenViking Python 包已安装"
        
        # 测试连接
        if curl -s http://localhost:18888/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} OpenViking 服务已运行"
        else
            echo -e "${YELLOW}!${NC} OpenViking 服务未运行"
            echo "   (OpenViking 通常作为库使用，不需要常驻服务)"
        fi
    else
        echo -e "${YELLOW}!${NC} OpenViking 未安装"
        echo "   运行: pip install openviking"
    fi
}

check_qmd() {
    echo -e "${YELLOW}▶${NC} 检查 qmd..."
    
    if command -v qmd &> /dev/null; then
        echo -e "${GREEN}✓${NC} qmd 已安装"
        echo "   位置: $(which qmd)"
        echo "   说明: qmd 用于文档索引，与 OpenViking 互补"
        echo "   保留建议: ✅ 保留，不要删除"
    else
        echo -e "${YELLOW}!${NC} qmd 未安装 (可选)"
    fi
}

show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo "系统状态检查"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    check_service "OpenClaw Gateway" "18789"
    check_service "OpenClaw Browser" "18800"
    check_service "OpenViking" "18888"
    check_service "Ollama" "11434"
}

# ==================== 主程序 ====================

case "${1:-start}" in
    start)
        echo "启动所有服务..."
        echo ""
        
        start_ollama
        echo ""
        
        start_openclaw
        echo ""
        
        check_openviking
        echo ""
        
        check_qmd
        echo ""
        
        show_status
        echo ""
        
        echo -e "${GREEN}✓${NC} 启动流程完成！"
        echo ""
        echo "常用命令:"
        echo "  openclaw browser open URL     # 打开网页"
        echo "  python tools/viking_memory.py stats  # 查看记忆状态"
        echo "  bash tools/ai_agent_disaster_recovery.sh check  # 健康检查"
        ;;
    
    stop)
        echo "停止服务..."
        
        echo "停止 Ollama..."
        pkill -f "ollama serve" 2>/dev/null || true
        
        echo "停止 OpenClaw Browser..."
        openclaw browser stop 2>/dev/null || true
        
        echo "停止 OpenClaw Gateway..."
        openclaw gateway stop 2>/dev/null || true
        
        echo -e "${GREEN}✓${NC} 服务已停止"
        ;;
    
    status)
        show_status
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    *)
        echo "用法: $0 [start|stop|status|restart]"
        echo ""
        echo "命令:"
        echo "  start   - 启动所有服务 (默认)"
        echo "  stop    - 停止所有服务"
        echo "  status  - 查看服务状态"
        echo "  restart - 重启所有服务"
        exit 1
        ;;
esac
