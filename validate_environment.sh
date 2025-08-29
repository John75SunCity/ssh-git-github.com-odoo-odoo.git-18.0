#!/bin/bash

# 🔍 Odoo Development Environment Validation Script
# This script validates that the development environment is properly configured

set -e

# Add Python user bin to PATH
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

echo "🔍 Odoo Development Environment Validation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
passed=0
failed=0
warnings=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((passed++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((failed++))
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((warnings++))
}

# Check if we're in the right directory
if [ ! -f ".vscode/settings.json" ]; then
    print_fail "VS Code settings.json not found"
    exit 1
fi

print_status "Validating development environment..."

# Check VS Code settings
print_status "Checking VS Code settings..."
if grep -q '"ruff.enable": true' .vscode/settings.json; then
    print_success "Ruff linting enabled"
else
    print_warning "Ruff linting not found in settings"
fi

if grep -q '"python.formatting.provider": "black"' .vscode/settings.json; then
    print_success "Black formatter configured"
else
    print_warning "Black formatter not found in settings"
fi

if grep -q '"python.sortImports.args"' .vscode/settings.json; then
    print_success "isort configured"
else
    print_warning "isort not found in settings"
fi

# Check Python tools installation
print_status "Checking Python tools..."

if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 found: $python_version"
else
    print_fail "Python 3 not found"
fi

if command -v ruff &> /dev/null; then
    ruff_version=$(ruff --version 2>&1 | awk '{print $2}')
    print_success "Ruff installed: $ruff_version"
else
    print_fail "Ruff not installed"
fi

if command -v black &> /dev/null; then
    black_version=$(black --version 2>&1 | head -n1 | awk '{print $2}')
    print_success "Black installed: $black_version"
else
    print_fail "Black not installed"
fi

if command -v isort &> /dev/null; then
    isort_version=$(isort --version 2>&1 | head -n1 | awk '{print $2}')
    print_success "isort installed: $isort_version"
else
    print_fail "isort not installed"
fi

if command -v mypy &> /dev/null; then
    mypy_version=$(mypy --version 2>&1 | awk '{print $2}')
    print_success "mypy installed: $mypy_version"
else
    print_fail "mypy not installed"
fi

if command -v bandit &> /dev/null; then
    bandit_version=$(bandit --version 2>&1 | head -n1 | awk '{print $2}')
    print_success "bandit installed: $bandit_version"
else
    print_fail "bandit not installed"
fi

# Check pre-commit
print_status "Checking pre-commit setup..."

if command -v pre-commit &> /dev/null; then
    pre_commit_version=$(pre-commit --version 2>&1 | awk '{print $2}')
    print_success "pre-commit installed: $pre_commit_version"

    if [ -f ".pre-commit-config.yaml" ]; then
        print_success "pre-commit config file exists"
    else
        print_fail "pre-commit config file missing"
    fi

    if [ -f ".git/hooks/pre-commit" ]; then
        print_success "pre-commit hooks installed"
    else
        print_warning "pre-commit hooks not installed (run: pre-commit install)"
    fi
else
    print_fail "pre-commit not installed"
fi

# Check project files
print_status "Checking project configuration..."

if [ -f "pyproject.toml" ]; then
    print_success "pyproject.toml exists"
else
    print_fail "pyproject.toml missing"
fi

if [ -d "records_management" ]; then
    print_success "records_management module exists"
else
    print_fail "records_management module missing"
fi

# Test basic functionality
print_status "Testing basic functionality..."

# Test ruff if available
if command -v ruff &> /dev/null; then
    if ruff check --select F401 --quiet pyproject.toml &> /dev/null; then
        print_success "Ruff basic functionality working"
    else
        print_warning "Ruff basic functionality test failed"
    fi
fi

# Test black if available
if command -v black &> /dev/null; then
    if black --check --quiet pyproject.toml &> /dev/null; then
        print_success "Black basic functionality working"
    else
        print_warning "Black basic functionality test failed"
    fi
fi

# Summary
echo ""
echo "📊 Validation Summary"
echo "===================="
echo "✅ Passed: $passed"
echo "❌ Failed: $failed"
echo "⚠️  Warnings: $warnings"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 Environment validation successful!${NC}"
    echo ""
    echo "🚀 You're ready to start developing!"
    echo "   • Use VS Code with the configured settings"
    echo "   • Run pre-commit checks before committing"
    echo "   • Format code with Black and lint with Ruff"
else
    echo -e "${RED}⚠️  Some issues found. Please fix them for optimal development experience.${NC}"
    echo ""
    echo "🔧 Quick fixes:"
    if ! command -v ruff &> /dev/null; then
        echo "   • Install Ruff: pip install ruff"
    fi
    if ! command -v black &> /dev/null; then
        echo "   • Install Black: pip install black"
    fi
    if ! command -v pre-commit &> /dev/null; then
        echo "   • Install pre-commit: pip install pre-commit"
    fi
    echo "   • Run setup again: ./setup_environment.sh"
fi

echo ""
echo "📖 For detailed setup instructions, see: DEVELOPMENT_SETUP.md"
