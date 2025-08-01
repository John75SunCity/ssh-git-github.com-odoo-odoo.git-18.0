# !/bin/bash

# Current Tools - Most Important Validation Scripts

# These are the actively used tools for module validation and deployment

echo "🔧 CURRENT VALIDATION TOOLS"
echo "=" * 50

echo "1. Module Validation (comprehensive syntax check):"
echo "   python development-tools/current-tools/module_validation.py"

echo "2. Field Analysis (check @api.depends):"
echo "   python development-tools/current-tools/analyze_api_depends.py"

echo "3. Comprehensive Field Analysis:"
echo "   python development-tools/current-tools/comprehensive_field_analysis.py"

echo "4. Quick Deployment Check:"
echo "   python development-tools/current-tools/quick_deployment_check.py"

echo "5. Deep Deployment Analysis:"
echo "   python development-tools/current-tools/deep_deployment_analysis.py"

echo ""
echo "📋 Quick Validation Sequence:"
echo "python development-tools/current-tools/module_validation.py"
echo "python development-tools/current-tools/analyze_api_depends.py"
echo "python development-tools/current-tools/quick_deployment_check.py"
