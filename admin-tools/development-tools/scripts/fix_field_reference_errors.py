#!/usr/bin/env python3
"""
Field Reference Error Fixer

This script fixes two critical types of field reference errors in Odoo:
1. Fields with unknown comodel_name (Many2one/One2many references to non-existent models)
2. Fields with unknown currency_field (Monetary fields with missing currency_field references)

Usage: python fix_field_reference_errors.py
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FieldReferenceFixer:
    """Fix field reference errors in Odoo model files."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.model_registry = {}  # Map of model names to file paths
        self.fixes_applied = []
        self.unknown_comodels = set()
        self.missing_currency_fields = set()

        # Common comodel name corrections
        self.comodel_corrections = {
            'destruction.certificate': 'naid.certificate',
            'base.rates': 'base.rate',
            'customer.negotiated.rates': 'customer.negotiated.rate',
            'chain.of.custody': 'records.chain.of.custody',
            'document.search.attempt': 'records.document.search.attempt',
        }

    def scan_existing_models(self):
        """Scan all Python files to build a registry of existing models."""
        logger.info("🔍 Scanning existing models...")

        for file_path in self.root_path.rglob("*.py"):
            if "__pycache__" in file_path.parts:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for _name definitions
                name_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
                for model_name in name_matches:
                    self.model_registry[model_name] = file_path

            except Exception as e:
                logger.warning(f"Error scanning {file_path}: {e}")

        logger.info(f"📋 Found {len(self.model_registry)} models in registry")

    def find_field_reference_errors(self) -> List[Dict]:
        """Find all field reference errors in the codebase."""
        errors = []

        logger.info("🔍 Scanning for field reference errors...")

        for file_path in self.root_path.rglob("*.py"):
            if "__pycache__" in file_path.parts:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find unknown comodel references
                comodel_errors = self._find_comodel_errors(content, file_path)
                errors.extend(comodel_errors)

                # Find currency field errors
                currency_errors = self._find_currency_field_errors(content, file_path)
                errors.extend(currency_errors)

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return errors

    def _find_comodel_errors(self, content: str, file_path: Path) -> List[Dict]:
        """Find comodel reference errors in file content."""
        errors = []

        # Pattern for Many2one and One2many fields with comodel
        field_patterns = [
            r'fields\.Many2one\s*\(\s*["\']([^"\']+)["\']',
            r'fields\.One2many\s*\(\s*["\']([^"\']+)["\']',
            r'comodel_name\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in field_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                comodel_name = match.group(1)

                # Check if comodel exists or needs correction
                if comodel_name not in self.model_registry:
                    corrected_name = self.comodel_corrections.get(comodel_name)
                    if corrected_name and corrected_name in self.model_registry:
                        errors.append({
                            'type': 'unknown_comodel',
                            'file': file_path,
                            'original': comodel_name,
                            'corrected': corrected_name,
                            'line_content': self._get_line_content(content, match.start()),
                            'position': match.start()
                        })
                        self.unknown_comodels.add(comodel_name)
                    elif not corrected_name:
                        logger.warning(f"Unknown comodel '{comodel_name}' in {file_path}")
                        self.unknown_comodels.add(comodel_name)

        return errors

    def _find_currency_field_errors(self, content: str, file_path: Path) -> List[Dict]:
        """Find currency field reference errors in file content."""
        errors = []

        # Find Monetary fields
        monetary_pattern = r'(\w+)\s*=\s*fields\.Monetary\s*\([^)]*currency_field\s*=\s*["\']([^"\']+)["\'][^)]*\)'
        matches = re.finditer(monetary_pattern, content, re.DOTALL)

        for match in matches:
            field_name = match.group(1)
            currency_field = match.group(2)

            # Check if currency field exists in the same model
            if not self._currency_field_exists_in_model(content, currency_field):
                errors.append({
                    'type': 'missing_currency_field',
                    'file': file_path,
                    'field_name': field_name,
                    'currency_field': currency_field,
                    'line_content': self._get_line_content(content, match.start()),
                    'position': match.start()
                })
                self.missing_currency_fields.add(f"{file_path}:{currency_field}")

        return errors

    def _currency_field_exists_in_model(self, content: str, currency_field: str) -> bool:
        """Check if currency field exists in the model."""
        # Look for field definition
        field_pattern = rf'{currency_field}\s*=\s*fields\.'
        return bool(re.search(field_pattern, content))

    def _get_line_content(self, content: str, position: int) -> str:
        """Get the line content for a given position."""
        lines = content[:position].split('\n')
        return lines[-1] if lines else ""

    def fix_comodel_errors(self, errors: List[Dict]) -> int:
        """Fix comodel reference errors."""
        fixes_count = 0

        # Group errors by file
        files_to_fix = {}
        for error in errors:
            if error['type'] == 'unknown_comodel':
                file_path = error['file']
                if file_path not in files_to_fix:
                    files_to_fix[file_path] = []
                files_to_fix[file_path].append(error)

        for file_path, file_errors in files_to_fix.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Apply fixes in reverse order to maintain positions
                file_errors.sort(key=lambda x: x['position'], reverse=True)

                for error in file_errors:
                    original = error['original']
                    corrected = error['corrected']

                    # Replace the comodel name
                    content = content.replace(f'"{original}"', f'"{corrected}"')
                    content = content.replace(f"'{original}'", f"'{corrected}'")

                    fixes_count += 1
                    logger.info(f"✅ Fixed comodel: {original} → {corrected} in {file_path.name}")

                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            except Exception as e:
                logger.error(f"Error fixing {file_path}: {e}")

        return fixes_count

    def fix_currency_field_errors(self, errors: List[Dict]) -> int:
        """Fix currency field errors by adding missing currency_id fields."""
        fixes_count = 0

        # Group errors by file
        files_to_fix = {}
        for error in errors:
            if error['type'] == 'missing_currency_field':
                file_path = error['file']
                if file_path not in files_to_fix:
                    files_to_fix[file_path] = []
                files_to_fix[file_path].append(error)

        for file_path, file_errors in files_to_fix.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Collect unique currency fields to add
                currency_fields_to_add = set()
                for error in file_errors:
                    currency_fields_to_add.add(error['currency_field'])

                # Add missing currency fields
                for currency_field in currency_fields_to_add:
                    if currency_field == 'currency_id' and 'currency_id' not in content:
                        # Add currency_id field
                        currency_field_def = '''
    # ============================================================================
    # CURRENCY FIELD
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
        help="Currency for monetary fields"
    )'''

                        # Find a good place to insert (after core fields section)
                        insert_pattern = r'(# ============================================================================\s*\n\s*# [A-Z\s]+FIELDS?\s*\n\s*# ============================================================================)'

                        match = re.search(insert_pattern, content)
                        if match:
                            # Insert after the first field section
                            insert_pos = content.find('\n', match.end()) + 1
                            content = content[:insert_pos] + currency_field_def + '\n' + content[insert_pos:]
                        else:
                            # Fallback: insert before class end
                            last_method_match = re.search(r'\n(\s+def\s+\w+.*?\n(?:\s{4,}.*\n)*)', content[::-1])
                            if last_method_match:
                                insert_pos = len(content) - last_method_match.start()
                                content = content[:insert_pos] + currency_field_def + '\n' + content[insert_pos:]

                        fixes_count += 1
                        logger.info(f"✅ Added missing currency_id field in {file_path.name}")

                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            except Exception as e:
                logger.error(f"Error fixing currency fields in {file_path}: {e}")

        return fixes_count

    def generate_model_creation_suggestions(self) -> List[str]:
        """Generate suggestions for creating missing models."""
        suggestions = []

        missing_models = self.unknown_comodels - set(self.comodel_corrections.keys())

        for model_name in sorted(missing_models):
            if model_name not in self.model_registry:
                suggestions.append(f"""
# Create missing model: {model_name}
class {self._model_name_to_class_name(model_name)}(models.Model):
    _name = '{model_name}'
    _description = '{model_name.replace(".", " ").title()}'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
""")

        return suggestions

    def _model_name_to_class_name(self, model_name: str) -> str:
        """Convert model name to class name."""
        parts = model_name.split('.')
        return ''.join(word.capitalize() for word in parts)

    def run_fixes(self) -> Dict:
        """Run all fixes and return summary."""
        logger.info("🔧 Starting Field Reference Error Fixer")
        logger.info("=" * 50)

        # Scan existing models
        self.scan_existing_models()

        # Find all errors
        errors = self.find_field_reference_errors()

        if not errors:
            logger.info("✅ No field reference errors found!")
            return {'comodel_fixes': 0, 'currency_fixes': 0, 'total_errors': 0}

        logger.info(f"📋 Found {len(errors)} field reference errors")

        # Categorize errors
        comodel_errors = [e for e in errors if e['type'] == 'unknown_comodel']
        currency_errors = [e for e in errors if e['type'] == 'missing_currency_field']

        logger.info(f"   📄 Comodel errors: {len(comodel_errors)}")
        logger.info(f"   💰 Currency field errors: {len(currency_errors)}")

        # Apply fixes
        comodel_fixes = self.fix_comodel_errors(comodel_errors)
        currency_fixes = self.fix_currency_field_errors(currency_errors)

        # Generate suggestions for missing models
        suggestions = self.generate_model_creation_suggestions()
        if suggestions:
            logger.info(f"\n💡 Suggestions for missing models:")
            for suggestion in suggestions[:3]:  # Show first 3
                logger.info(suggestion)

        return {
            'comodel_fixes': comodel_fixes,
            'currency_fixes': currency_fixes,
            'total_errors': len(errors),
            'suggestions': suggestions
        }

def main():
    """Main execution function."""
    root_path = Path("records_management")

    if not root_path.exists():
        logger.error(f"❌ Records Management module not found at {root_path}")
        return 1

    fixer = FieldReferenceFixer(root_path)
    results = fixer.run_fixes()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 FIELD REFERENCE FIXER SUMMARY")
    logger.info(f"Comodel fixes applied: {results['comodel_fixes']}")
    logger.info(f"Currency field fixes applied: {results['currency_fixes']}")
    logger.info(f"Total errors found: {results['total_errors']}")

    if results['comodel_fixes'] > 0 or results['currency_fixes'] > 0:
        logger.info("\n🎉 Successfully applied fixes!")
        logger.info("💡 Run syntax validation to verify changes.")
    else:
        logger.info("\n⚠️  No fixes were applied.")

    if results.get('suggestions'):
        logger.info(f"\n📝 Generated {len(results['suggestions'])} model creation suggestions")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
