#!/bin/bash
# Archive old informational files and organize by date

ARCHIVE_DIR="docs/archived-info-$(date +%Y%m%d)"
mkdir -p "$ARCHIVE_DIR"

# Files that are outdated/superseded (move to archive)
ARCHIVE_FILES=(
    "BRANCH_SYNC_SUMMARY.md"
    "BRANCH_SYNC_SYSTEM.md"
    "CONTAINER_UX_IMPROVEMENTS_SUMMARY.md"
    "CONTEXTUAL_HELP_IMPLEMENTATION_PLAN.md"
    "CONTEXTUAL_HELP_MILESTONE_25PERCENT.md"
    "CONTEXTUAL_HELP_SUMMARY.md"
    "DELETE_STUDIO_CUSTOMIZATIONS_GUIDE.md"
    "DEPARTMENT_ACCESS_CONTROL_IMPLEMENTATION.md"
    "DEVELOPMENT_WORKFLOW.md"
    "HELP_MESSAGES_PROGRESS.md"
    "ODOO19_UPGRADE_SUMMARY.md"
    "PORTAL_SERVICE_ORDERING_SUMMARY.md"
    "PRIORITY_1_IMPLEMENTATION_COMPLETE.md"
    "PRIORITY_1_TESTING_CHECKLIST.md"
    "PRIORITY_1_UI_UPDATES.md"
    "STOCK_ARCHITECTURE_AUDIT.md"
    "URGENT_MODULE_UPGRADE_FIX.md"
)

# Current working files (keep at root with date suffix)
CURRENT_FILES=(
    "AGENTS.md"
    "DEPLOYMENT_READY_SUMMARY.md"
    "MANIFEST_FIX_VISUAL_GUIDE.md"
    "MANIFEST_LINE_BY_LINE_REFERENCE.md"
    "MANIFEST_RESTRUCTURING_SUMMARY.md"
    "NEXT_STEPS.md"
)

echo "📦 Archiving outdated informational files..."
for file in "${ARCHIVE_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "$ARCHIVE_DIR/"
        echo "  → Archived: $file"
    fi
done

echo ""
echo "📅 Adding datetime suffix to current files..."
DATETIME=$(date +%Y%m%d_%H%M%S)
for file in "${CURRENT_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Only rename if not already dated
        if [[ ! "$file" =~ _[0-9]{8}_ ]]; then
            BASENAME="${file%.md}"
            mv "$file" "${BASENAME}_${DATETIME}.md"
            echo "  → Renamed: $file → ${BASENAME}_${DATETIME}.md"
        fi
    fi
done

echo ""
echo "✅ Organization complete!"
echo "📂 Archived to: $ARCHIVE_DIR"
echo ""
echo "📄 Current working files (root):"
ls -1 *_[0-9]{8}_*.md 2>/dev/null || echo "   (will appear after rename)"
