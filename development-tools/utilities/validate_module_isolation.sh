#!/bin/bash
# ============================================================================
# RECORDS MANAGEMENT MODULE ISOLATION VALIDATOR
# ============================================================================
# This script validates that ONLY records_management is recognized as a module

echo "🔍 VALIDATING MODULE ISOLATION..."
echo "=================================="

echo ""
echo "✅ ACTIVE MODULES (Should only be records_management):"
echo "------------------------------------------------------"
find . -name "__manifest__.py" | while read manifest; do
    echo "📦 FOUND: $manifest"
    echo "   NAME: $(grep -A1 "'name'" "$manifest" | tail -1 | sed "s/.*['\"]\\([^'\"]*\\)['\"].*/\\1/")"
    echo ""
done

echo ""
echo "🚫 DISABLED MODULES (These should be .disabled):"
echo "------------------------------------------------"
find . -name "__manifest__.py.disabled" | while read disabled; do
    echo "❌ DISABLED: $disabled"
done

echo ""
echo "🔧 ACTIVE __init__.py FILES (Should only be in records_management/):"
echo "-------------------------------------------------------------------"
find . -name "__init__.py" | while read init; do
    if [[ $init == *"records_management"* ]] && [[ $init != *"backup"* ]]; then
        echo "✅ ACTIVE: $init"
    else
        echo "⚠️  OTHER: $init (should be disabled if in development-tools)"
    fi
done

echo ""
echo "🚫 DISABLED __init__.py FILES:"
echo "-----------------------------"
find . -name "__init__.py.disabled" | head -5 | while read disabled; do
    echo "❌ DISABLED: $disabled"
done
if [ $(find . -name "__init__.py.disabled" | wc -l) -gt 5 ]; then
    echo "   ... and $(( $(find . -name "__init__.py.disabled" | wc -l) - 5 )) more"
fi

echo ""
echo "📁 DIRECTORY STRUCTURE CHECK:"
echo "-----------------------------"
echo "Active module: $(ls -la records_management/__manifest__.py 2>/dev/null && echo "✅ PRESENT" || echo "❌ MISSING")"
echo "Backup isolated: $(ls -la development-tools/records_management_backup*/__manifest__.py.disabled 2>/dev/null && echo "✅ DISABLED" || echo "❌ STILL ACTIVE")"

echo ""
echo "🎯 ISOLATION STATUS:"
echo "===================="
active_manifests=$(find . -name "__manifest__.py" | wc -l)
if [ $active_manifests -eq 1 ]; then
    echo "✅ PERFECT ISOLATION: Only 1 active module manifest found"
    echo "🚀 Database will ONLY load records_management module"
else
    echo "⚠️  WARNING: $active_manifests active manifests found"
    echo "🔧 Additional cleanup may be needed"
fi

echo ""
echo "Module isolation validation complete!"
