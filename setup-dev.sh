#!/bin/bash
# Development Environment Setup Script

echo "🚀 Setting up Odoo Development Environment..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "records_management" ]; then
    echo "❌ Error: Please run this script from the workspace root directory"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Check if PostgreSQL is available
echo "🔍 Checking PostgreSQL availability..."
if command -v psql >/dev/null 2>&1; then
    echo "✅ PostgreSQL client found"
else
    echo "⚠️  PostgreSQL client not found. You may need to install it or use external DB"
fi

# Create directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p addons
mkdir -p custom_addons
mkdir -p logs

# Set permissions for odoo user
echo "🔐 Setting file permissions..."
sudo chown -R odoo:odoo /workspace 2>/dev/null || true

# Run TypeScript compilation check
echo "🔍 Checking TypeScript compilation..."
if npx tsc --noEmit; then
    echo "✅ TypeScript compilation successful"
else
    echo "⚠️  TypeScript compilation has issues (check tsconfig.json)"
fi

# Run tests
echo "🧪 Running tests..."
if npm test; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure PostgreSQL connection in odoo.conf"
echo "   2. Run: odoo -c odoo.conf"
echo "   3. Open http://localhost:8069 in your browser"
echo "   4. Install your custom modules from Apps menu"
echo ""
echo "📚 Useful commands:"
echo "   - Start Odoo: odoo -c odoo.conf"
echo "   - Run tests: python -m pytest tests/"
echo "   - Build TypeScript: npx tsc"
echo "   - Lint Python: flake8 records_management/"
echo ""
