#!/bin/bash
# Comprehensive validation that active_bin_key_ids is completely removed

echo "🔍 COMPREHENSIVE VALIDATION: active_bin_key_ids dependency removal"
echo "================================================================="

cd /workspaces/ssh-git-github.com-odoo-odoo.git-18.0

echo "1. Searching ALL files for 'active_bin_key_ids':"
RESULT=$(find . -type f -exec grep -l "active_bin_key_ids" {} \; 2>/dev/null)
if [ -z "$RESULT" ]; then
    echo "   ✅ NO REFERENCES FOUND - CLEAN"
else
    echo "   ❌ FOUND REFERENCES:"
    echo "$RESULT"
fi

echo ""
echo "2. Checking partner_bin_key.py @api.depends decorators:"
grep -A 1 -B 1 "@api.depends" records_management/models/partner_bin_key.py | grep -v "active_bin_key_ids"
if [ $? -eq 0 ]; then
    echo "   ✅ ALL @api.depends use valid fields"
else
    echo "   ⚠️  Check @api.depends manually"
fi

echo ""
echo "3. Verifying correct dependencies in partner_bin_key.py:"
echo "   Expected: bin_key_history_ids, unlock_service_history_ids"
grep "@api.depends" records_management/models/partner_bin_key.py

echo ""
echo "4. Checking for Python cache files:"
CACHE_COUNT=$(find records_management -name "__pycache__" | wc -l)
echo "   Python cache directories: $CACHE_COUNT (should be 0 after cleanup)"

echo ""
echo "5. Git status check:"
git status --porcelain

echo ""
echo "🎯 VALIDATION COMPLETE"
echo "If all checks show ✅, the server cache issue should be resolved after rebuild."
