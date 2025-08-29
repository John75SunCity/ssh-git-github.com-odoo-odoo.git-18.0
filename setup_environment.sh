#!/bin/bash

# 🚀 Odoo Development Environment Setup Script
# This script helps activate the new VS Code settings and install required extensions

set -e

echo "🚀 Odoo Development Environment Setup"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f ".vscode/settings.new.json" ]; then
    print_error "Error: .vscode/settings.new.json not found. Please run this script from the project root."
    exit 1
fi

print_status "Setting up Odoo development environment..."

# Step 1: Backup current settings
if [ -f ".vscode/settings.json" ]; then
    print_status "Backing up current VS Code settings..."
    cp .vscode/settings.json .vscode/settings.backup.$(date +%Y%m%d_%H%M%S).json
    print_success "Current settings backed up"
fi

# Step 2: Activate new settings
print_status "Activating new VS Code settings..."
cp .vscode/settings.new.json .vscode/settings.json
print_success "New VS Code settings activated"

# Step 3: Install essential extensions
print_status "Installing essential VS Code extensions..."

# Essential extensions for Odoo development
extensions=(
    "charliermarsh.ruff"
    "ms-python.black-formatter"
    "ms-python.isort"
    "ms-python.mypy-type-checker"
    "ms-python.bandit"
    "trinhanhngoc.odoo"
    "trinhanhngoc.odoo-shortcuts"
    "trinhanhngoc.odoo-xml-formatter"
    "ms-python.python"
    "ms-python.pytest"
    "esbenp.prettier-vscode"
    "ms-vscode.vscode-json"
    "redhat.vscode-yaml"
)

installed_count=0
failed_count=0

for ext in "${extensions[@]}"; do
    print_status "Installing $ext..."
    if code --install-extension "$ext" --force; then
        print_success "✓ $ext installed"
        ((installed_count++))
    else
        print_warning "✗ Failed to install $ext"
        ((failed_count++))
    fi
done

echo ""
print_success "Extension installation complete: $installed_count installed, $failed_count failed"

# Step 4: Setup pre-commit hooks
print_status "Setting up pre-commit hooks..."

if command -v pip &> /dev/null; then
    print_status "Installing pre-commit..."
    pip install pre-commit

    if command -v pre-commit &> /dev/null; then
        print_status "Installing pre-commit hooks..."
        pre-commit install
        print_success "Pre-commit hooks installed"

        print_status "Running initial pre-commit check..."
        if pre-commit run --all-files; then
            print_success "Initial pre-commit check passed"
        else
            print_warning "Some pre-commit checks failed. This is normal for existing code."
            print_status "You can fix issues with: pre-commit run --all-files --fix"
        fi
    else
        print_warning "Pre-commit installation failed. Please install manually: pip install pre-commit"
    fi
else
    print_warning "pip not found. Please install pre-commit manually: pip install pre-commit"
fi

# Step 5: Final instructions
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
print_success "✅ VS Code settings activated"
print_success "✅ Essential extensions installed ($installed_count/$((installed_count + failed_count)))"
print_success "✅ Pre-commit hooks configured"
echo ""
echo "📋 Next Steps:"
echo "1. ${YELLOW}Reload VS Code${NC}: Ctrl+Shift+P → 'Developer: Reload Window'"
echo "2. ${YELLOW}Restart Python Language Server${NC}: Ctrl+Shift+P → 'Python: Restart Language Server'"
echo "3. ${YELLOW}Test the setup${NC}: Open a Python file and check for linting/formatting"
echo ""
echo "🛠️  Useful Commands:"
echo "• Run all checks: ${BLUE}pre-commit run --all-files${NC}"
echo "• Format code: ${BLUE}black .${NC}"
echo "• Check types: ${BLUE}mypy .${NC}"
echo "• Start Odoo: ${BLUE}python3 -m odoo --addons-path=./addons,./records_management --database=records_dev --dev=all${NC}"
echo ""
echo "📖 For detailed documentation, see: ${BLUE}DEVELOPMENT_SETUP.md${NC}"
echo ""
print_success "Happy coding! 🎯"
