#!/bin/sh
# pre-commit hook for security scanning
# Install: cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

echo "=========================================="
echo "Running pre-commit security checks..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gitleaks is installed
if ! command -v gitleaks &> /dev/null; then
    echo "${YELLOW}Warning: gitleaks is not installed. Installing...${NC}"
    
    # Try to install gitleaks
    if command -v brew &> /dev/null; then
        brew install gitleaks
    elif command -v go &> /dev/null; then
        go install github.com/gitleaks/gitleaks/v8@latest
    else
        echo "${RED}Error: Cannot install gitleaks automatically.${NC}"
        echo "Please install manually: https://github.com/gitleaks/gitleaks"
        exit 1
    fi
fi

# Run gitleaks detect
echo ""
echo "[1/3] Running gitleaks detect..."
if gitleaks detect --source . --config .gitleaks.toml --verbose; then
    echo "${GREEN}✓ No secrets detected${NC}"
else
    echo "${RED}✗ Secrets detected! Commit aborted.${NC}"
    echo ""
    echo "To bypass (not recommended): git commit --no-verify"
    exit 1
fi

# Check for hardcoded secrets in staged files
echo ""
echo "[2/3] Checking staged files for hardcoded secrets..."

# Patterns to check
PATTERNS="password|secret|api_key|apikey|token|private_key"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -n "$STAGED_FILES" ]; then
    # Check Python files
    PY_FILES=$(echo "$STAGED_FILES" | grep '\.py$' || true)
    if [ -n "$PY_FILES" ]; then
        MATCHES=$(git diff --cached --name-only --diff-filter=ACM | xargs grep -i -E "$PATTERNS" 2>/dev/null || true)
        if [ -n "$MATCHES" ]; then
            echo "${YELLOW}Warning: Potential secrets found in staged files:${NC}"
            echo "$MATCHES"
            echo ""
            echo "Please review and ensure no real secrets are committed."
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

echo "${GREEN}✓ Staged files check passed${NC}"

# Run basic linting if available
echo ""
echo "[3/3] Running basic linting..."

if command -v ruff &> /dev/null; then
    if ruff check . --select E,W,F; then
        echo "${GREEN}✓ Ruff check passed${NC}"
    else
        echo "${YELLOW}Warning: Ruff found issues${NC}"
    fi
else
    echo "${YELLOW}Skipping ruff (not installed)${NC}"
fi

echo ""
echo "=========================================="
echo "${GREEN}All pre-commit checks passed!${NC}"
echo "=========================================="
