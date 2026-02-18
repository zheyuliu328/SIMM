#!/bin/bash
# 安全改造一键安装脚本
# 为 fct, nlp-factor, credit-one 三个项目安装安全组件

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Security Hardening Installation Script"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo "[1/5] Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
    fi
    
    if ! command -v gitleaks &> /dev/null; then
        echo -e "${YELLOW}Warning: gitleaks not found. Will try to install.${NC}"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing dependencies: ${missing_deps[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Dependencies check passed${NC}"
}

# 安装 gitleaks
install_gitleaks() {
    if command -v gitleaks &> /dev/null; then
        echo -e "${GREEN}✓ gitleaks already installed${NC}"
        return
    fi
    
    echo "Installing gitleaks..."
    
    if command -v brew &> /dev/null; then
        brew install gitleaks
    elif command -v go &> /dev/null; then
        go install github.com/gitleaks/gitleaks/v8@latest
    else
        # 下载预编译二进制
        local version="8.18.2"
        local os=$(uname -s | tr '[:upper:]' '[:lower:]')
        local arch=$(uname -m)
        
        case "$arch" in
            x86_64) arch="x64" ;;
            arm64|aarch64) arch="arm64" ;;
        esac
        
        local url="https://github.com/gitleaks/gitleaks/releases/download/v${version}/gitleaks_${version}_${os}_${arch}.tar.gz"
        
        curl -sfL "$url" | tar -xz -C /tmp
        sudo mv /tmp/gitleaks /usr/local/bin/ 2>/dev/null || mv /tmp/gitleaks "$HOME/.local/bin/" 2>/dev/null || echo "Please move /tmp/gitleaks to your PATH"
    fi
    
    echo -e "${GREEN}✓ gitleaks installed${NC}"
}

# 安装 pre-commit
install_precommit() {
    echo "Installing pre-commit..."
    pip3 install pre-commit bandit safety
    echo -e "${GREEN}✓ pre-commit installed${NC}"
}

# 创建工具模块
create_utils() {
    echo ""
    echo "[2/5] Creating utility modules..."
    
    local projects=("fct" "nlp-factor" "credit-one")
    
    for project in "${projects[@]}"; do
        local utils_dir="$ROOT_DIR/$project/src/utils"
        mkdir -p "$utils_dir"
        
        # 复制工具模块
        cp "$ROOT_DIR/src/utils/guardrails.py" "$utils_dir/" 2>/dev/null || echo "Source guardrails.py not found, skipping..."
        cp "$ROOT_DIR/src/utils/secrets.py" "$utils_dir/" 2>/dev/null || echo "Source secrets.py not found, skipping..."
        cp "$ROOT_DIR/src/utils/data_boundary.py" "$utils_dir/" 2>/dev/null || echo "Source data_boundary.py not found, skipping..."
        
        # 添加 __init__.py
        touch "$utils_dir/__init__.py"
        
        echo -e "${GREEN}✓ Created utils for $project${NC}"
    done
}

# 配置 gitleaks
configure_gitleaks() {
    echo ""
    echo "[3/5] Configuring gitleaks..."
    
    local projects=("fct" "nlp-factor" "credit-one")
    
    for project in "${projects[@]}"; do
        local project_dir="$ROOT_DIR/$project"
        
        if [ -f "$ROOT_DIR/.gitleaks.toml" ]; then
            cp "$ROOT_DIR/.gitleaks.toml" "$project_dir/"
            echo -e "${GREEN}✓ Configured gitleaks for $project${NC}"
        else
            echo -e "${YELLOW}Warning: Root .gitleaks.toml not found${NC}"
        fi
    done
}

# 配置 pre-commit
configure_precommit() {
    echo ""
    echo "[4/5] Configuring pre-commit..."
    
    local projects=("fct" "nlp-factor" "credit-one")
    
    for project in "${projects[@]}"; do
        local project_dir="$ROOT_DIR/$project"
        
        if [ -d "$project_dir/.git" ]; then
            cd "$project_dir"
            
            # 创建 .pre-commit-config.yaml
            cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
  
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
EOF
            
            # 安装 pre-commit hooks
            pre-commit install
            
            echo -e "${GREEN}✓ Configured pre-commit for $project${NC}"
        else
            echo -e "${YELLOW}Warning: $project is not a git repository${NC}"
        fi
    done
    
    cd "$ROOT_DIR"
}

# 创建环境文件模板
create_env_templates() {
    echo ""
    echo "[5/5] Creating environment templates..."
    
    # NLP-Factor .env.example
    cat > "$ROOT_DIR/nlp-factor/.env.example" << 'EOF'
# Event Registry API Key
# 获取地址: https://eventregistry.org/
ER_API_KEY=your_api_key_here

# 注意: 复制此文件为 .env 并填入真实值
# .env 文件已添加到 .gitignore，不会被提交
EOF
    
    # Credit-One .env.example
    cat > "$ROOT_DIR/credit-one/.env.example" << 'EOF'
# Kaggle API Credentials
# 获取地址: https://www.kaggle.com/settings/account
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key

# 注意: 复制此文件为 .env 并填入真实值
# .env 文件已添加到 .gitignore，不会被提交
EOF
    
    echo -e "${GREEN}✓ Created .env.example templates${NC}"
}

# 更新 .gitignore
update_gitignore() {
    echo "Updating .gitignore files..."
    
    local gitignore_content='
# Secrets
.env
.env.local
.env.*.local
*.pem
*.key

# Logs
logs/
*.log

# Backups
backups/

# Database
*.db
*.db-journal
'
    
    local projects=("fct" "nlp-factor" "credit-one")
    
    for project in "${projects[@]}"; do
        local gitignore_file="$ROOT_DIR/$project/.gitignore"
        
        if [ -f "$gitignore_file" ]; then
            # 追加内容（如果不存在）
            if ! grep -q "^# Secrets$" "$gitignore_file" 2>/dev/null; then
                echo "" >> "$gitignore_file"
                echo "$gitignore_content" >> "$gitignore_file"
                echo -e "${GREEN}✓ Updated .gitignore for $project${NC}"
            fi
        else
            echo "$gitignore_content" > "$gitignore_file"
            echo -e "${GREEN}✓ Created .gitignore for $project${NC}"
        fi
    done
}

# 主函数
main() {
    check_dependencies
    install_gitleaks
    install_precommit
    create_utils
    configure_gitleaks
    configure_precommit
    create_env_templates
    update_gitignore
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Security hardening installation completed!${NC}"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Review SECURITY_CHECKLIST.md in each project"
    echo "2. Copy .env.example to .env and fill in your secrets"
    echo "3. Run 'gitleaks detect --source . --verbose' to verify"
    echo "4. Run 'pre-commit run --all-files' to test hooks"
    echo ""
    echo "For questions, see docs/threat_model.md and docs/rollback.md"
}

# 执行
main "$@"
