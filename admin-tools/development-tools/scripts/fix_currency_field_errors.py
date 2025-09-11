#!/usr/bin/env python3
"""
Currency Field Error Fixer

This script specifically fixes currency_field reference errors by:
1. Finding Monetary fields with missing currency_field references
2. Adding the missing currency_id fields to models
3. Ensuring proper currency field setup

Fixes errors like: "Field records.container.insurance_value with unknown currency_field 'currency_id'"
"""

import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CurrencyFieldFixer:
    """Fix currency field reference errors in Odoo models."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.fixes_applied = []

    def find_monetary_fields_without_currency(self) -> dict:
        """Find all Monetary fields that reference missing currency fields."""
        files_with_issues = {}

        for file_path in self.root_path.rglob("*.py"):
            if "__pycache__" in file_path.parts:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                issues = self._analyze_file_for_currency_issues(content, file_path)
                if issues:
                    files_with_issues[file_path] = issues

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return files_with_issues

    def _analyze_file_for_currency_issues(self, content: str, file_path: Path) -> dict:
        """Analyze a single file for currency field issues."""
        issues = {
            'monetary_fields': [],
            'missing_currency_fields': set(),
            'has_currency_id': False
        }

        # Find all Monetary fields
        monetary_pattern = r'(\w+)\s*=\s*fields\.Monetary\s*\([^)]*currency_field\s*=\s*["\']([^"\']+)["\'][^)]*\)'
        matches = re.finditer(monetary_pattern, content, re.DOTALL)

        for match in matches:
            field_name = match.group(1)
            currency_field = match.group(2)

            issues['monetary_fields'].append({
                'field_name': field_name,
                'currency_field': currency_field,
                'full_match': match.group(0)
            })

            # Check if the referenced currency field exists
            if not self._field_exists_in_content(content, currency_field):
                issues['missing_currency_fields'].add(currency_field)

        # Check if currency_id field already exists
        issues['has_currency_id'] = self._field_exists_in_content(content, 'currency_id')

        # Only return issues if there are missing currency fields
        return issues if issues['missing_currency_fields'] else None

    def _field_exists_in_content(self, content: str, field_name: str) -> bool:
        """Check if a field is defined in the content."""
        field_pattern = rf'{field_name}\s*=\s*fields\.'
        return bool(re.search(field_pattern, content))

    def fix_currency_field_issues(self, files_with_issues: dict) -> int:
        """Fix currency field issues in the provided files."""
        fixes_count = 0

        for file_path, issues in files_with_issues.items():
            try:
                fixes_count += self._fix_file_currency_issues(file_path, issues)
            except Exception as e:
                logger.error(f"Error fixing {file_path}: {e}")

        return fixes_count

    def _fix_file_currency_issues(self, file_path: Path, issues: dict) -> int:
        """Fix currency issues in a single file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixes_count = 0

        # Add missing currency fields
        for currency_field in issues['missing_currency_fields']:
            if currency_field == 'currency_id' and not issues['has_currency_id']:
                content = self._add_currency_id_field(content, file_path)
                fixes_count += 1
                logger.info(f"✅ Added currency_id field to {file_path.name}")
            elif currency_field != 'currency_id':
                # For custom currency fields, add them too
                content = self._add_custom_currency_field(content, currency_field, file_path)
                fixes_count += 1
                logger.info(f"✅ Added {currency_field} field to {file_path.name}")

        # Write back the fixed content
        if fixes_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return fixes_count

    def _add_currency_id_field(self, content: str, file_path: Path) -> str:
        """Add currency_id field to the model."""
        currency_field_def = '''
    # ============================================================================
    # CURRENCY FIELD (AUTO-ADDED)
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
        help="Currency for monetary fields"
    )'''

        # Find the best place to insert the currency field
        return self._insert_field_in_content(content, currency_field_def, file_path)

    def _add_custom_currency_field(self, content: str, currency_field: str, file_path: Path) -> str:
        """Add a custom currency field to the model."""
        field_def = f'''
    {currency_field} = fields.Many2one(
        "res.currency",
        string="{currency_field.replace('_', ' ').title()}",
        default=lambda self: self.env.company.currency_id,
        help="Currency for {currency_field.replace('_', ' ')} calculations"
    )'''

        return self._insert_field_in_content(content, field_def, file_path)

    def _insert_field_in_content(self, content: str, field_def: str, file_path: Path) -> str:
        """Insert a field definition in the appropriate location."""

        # Strategy 1: After core identification fields
        core_pattern = r'(# ============================================================================\s*\n\s*# CORE [A-Z\s]*FIELDS?\s*\n\s*# ============================================================================[^#]*?)(\n\s*# ============================================================================)'
        match = re.search(core_pattern, content, re.DOTALL)

        if match:
            return content[:match.end(1)] + field_def + content[match.start(2):]

        # Strategy 2: After any field section
        field_section_pattern = r'(# ============================================================================\s*\n\s*# [A-Z\s]*FIELDS?\s*\n\s*# ============================================================================[^#]*?)(\n\s*# ============================================================================)'
        match = re.search(field_section_pattern, content, re.DOTALL)

        if match:
            return content[:match.end(1)] + field_def + content[match.start(2):]

        # Strategy 3: Before first method definition
        method_pattern = r'(\n\s*# ============================================================================\s*\n\s*# [A-Z\s]*METHODS?\s*\n\s*# ============================================================================)'
        match = re.search(method_pattern, content)

        if match:
            return content[:match.start()] + field_def + content[match.start():]

        # Strategy 4: Before first @api decorator
        api_pattern = r'(\n\s*@api\.)'
        match = re.search(api_pattern, content)

        if match:
            return content[:match.start()] + field_def + content[match.start():]

        # Strategy 5: Before class end (fallback)
        logger.warning(f"Using fallback insertion strategy for {file_path.name}")
        class_end_pattern = r'(\n\s*def\s+.*?\n(?:\s{4,}.*\n)*)'
        matches = list(re.finditer(class_end_pattern, content))

        if matches:
            # Insert before the last method
            last_match = matches[-1]
            return content[:last_match.start()] + field_def + content[last_match.start():]

        # Final fallback: append before last few lines
        lines = content.split('\n')
        insert_point = max(0, len(lines) - 5)
        lines.insert(insert_point, field_def)
        return '\n'.join(lines)

def main():
    """Main execution function."""
    logger.info("🔧 Currency Field Error Fixer")
    logger.info("=" * 50)

    root_path = Path("records_management")

    if not root_path.exists():
        logger.error(f"❌ Records Management module not found at {root_path}")
        return 1

    fixer = CurrencyFieldFixer(root_path)

    # Find issues
    logger.info("🔍 Scanning for currency field issues...")
    files_with_issues = fixer.find_monetary_fields_without_currency()

    if not files_with_issues:
        logger.info("✅ No currency field issues found!")
        return 0

    logger.info(f"📋 Found currency field issues in {len(files_with_issues)} files:")

    for file_path, issues in files_with_issues.items():
        logger.info(f"   📄 {file_path.name}: {len(issues['monetary_fields'])} Monetary fields, "
                   f"missing {len(issues['missing_currency_fields'])} currency fields")

    # Ask for confirmation
    response = input(f"\n🤔 Proceed to fix {len(files_with_issues)} files? (y/N): ")
    if response.lower() != 'y':
        logger.info("❌ Operation cancelled by user.")
        return 0

    # Apply fixes
    logger.info("\n🔧 Applying currency field fixes...")
    fixes_count = fixer.fix_currency_field_issues(files_with_issues)

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 CURRENCY FIELD FIXER SUMMARY")
    logger.info(f"Files processed: {len(files_with_issues)}")
    logger.info(f"Currency fields added: {fixes_count}")

    if fixes_count > 0:
        logger.info("\n🎉 Successfully added missing currency fields!")
        logger.info("💡 Run syntax validation to verify changes.")
    else:
        logger.info("\n⚠️  No currency fields were added.")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
