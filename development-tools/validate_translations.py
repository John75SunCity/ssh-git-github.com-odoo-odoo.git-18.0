#!/usr/bin/env python3
"""
Translation Validation Script
===========================

Validates translation patterns and i18n compliance.
Checks for proper translation usage and consistency.

Features:
- Translation pattern validation
- i18n compliance checks
- Translation file validation
- String extraction verification
- Translation key consistency

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
import ast

class TranslationValidator:
    """Validates translation patterns and i18n compliance"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.translation_patterns: Dict[str, List[Tuple[str, int]]] = {}

    def validate_translations(self) -> bool:
        """Main validation function"""
        print("🌐 Validating Translation Patterns...")

        # Find and validate Python files
        self._validate_python_files()

        # Validate translation files
        self._validate_po_files()

        # Check for translation consistency
        self._validate_translation_consistency()

        # Validate translation extraction
        self._validate_translation_extraction()

        return len(self.errors) == 0

    def _validate_python_files(self) -> None:
        """Validate translation usage in Python files"""
        module_dir = self.workspace_root / "records_management"

        if not module_dir.exists():
            return

        for py_file in module_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                self._validate_file_translations(content, py_file)

            except Exception as e:
                self.warnings.append(f"Error reading {py_file}: {e}")

    def _validate_file_translations(self, content: str, file_path: Path) -> None:
        """Validate translation patterns in a single file"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for proper translation patterns
            self._validate_translation_pattern(line, line_num, file_path)

            # Check for hardcoded strings that should be translated
            self._validate_hardcoded_strings(line, line_num, file_path)

    def _validate_translation_pattern(self, line: str, line_num: int, file_path: Path) -> None:
        """Validate translation function usage"""
        # Pattern 1: _("string") - correct
        correct_pattern = r'_\(\s*[\'\"](.*?)[\'\"]\s*\)'
        matches = re.findall(correct_pattern, line)

        for match in matches:
            if match.strip():
                # Store for consistency checking
                if match not in self.translation_patterns:
                    self.translation_patterns[match] = []
                self.translation_patterns[match].append((str(file_path), line_num))

        # Pattern 2: _("string %s" % value) - incorrect, should be _("string %s", value)
        incorrect_pattern = r'_\(\s*[\'\"](.*?)[\'\"]\s*\)\s*%\s*[^,\)]'
        if re.search(incorrect_pattern, line):
            self.errors.append(f"{file_path}:{line_num}: Incorrect translation pattern - use _('text', value) instead of _('text') % value")

        # Pattern 3: _("string" % value) - also incorrect
        alt_incorrect_pattern = r'_\(\s*[\'\"](.*?)[\'\"]\s*%\s*'
        if re.search(alt_incorrect_pattern, line):
            self.errors.append(f"{file_path}:{line_num}: Incorrect translation pattern - use _('text', value) instead of _('text' % value)")

        # Pattern 4: Check for proper parameter usage
        proper_pattern = r'_\(\s*[\'\"](.*?)[\'\"]\s*,\s*[^)]+\)'
        proper_matches = re.findall(proper_pattern, line)
        for match in proper_matches:
            if '%' in match and '%(' not in match:  # Has % but not %( - likely incorrect
                self.warnings.append(f"{file_path}:{line_num}: Translation string contains % - verify parameter usage")

    def _validate_hardcoded_strings(self, line: str, line_num: int, file_path: Path) -> None:
        """Check for hardcoded user-facing strings that should be translated"""
        # Skip comments and imports
        line = line.strip()
        if line.startswith('#') or line.startswith('import') or line.startswith('from'):
            return

        # Look for string literals that might be user-facing
        string_pattern = r'[\'\"]([A-Z][^\'\"]*?)[\'\"]'
        matches = re.findall(string_pattern, line)

        for match in matches:
            # Skip if it's already translated
            if '_(' in line and match in line:
                continue

            # Skip common non-translatable strings
            skip_patterns = [
                'True', 'False', 'None',
                r'\d+',  # Numbers
                r'[a-z_]+',  # Lowercase identifiers
                r'[A-Z_]+',  # Constants
            ]

            should_skip = False
            for pattern in skip_patterns:
                if re.match(pattern, match):
                    should_skip = True
                    break

            if not should_skip and len(match) > 3:  # Only flag longer strings
                self.warnings.append(f"{file_path}:{line_num}: Potential hardcoded user string '{match}' - consider translating")

    def _validate_po_files(self) -> None:
        """Validate .po translation files"""
        i18n_dir = self.workspace_root / "records_management" / "i18n"

        if not i18n_dir.exists():
            self.warnings.append("No i18n directory found - translations may be missing")
            return

        for po_file in i18n_dir.glob("*.po"):
            try:
                self._validate_po_file(po_file)
            except Exception as e:
                self.errors.append(f"Error validating {po_file}: {e}")

    def _validate_po_file(self, po_file: Path) -> None:
        """Validate a single .po file"""
        try:
            with open(po_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for proper .po file structure
            if not content.startswith('#'):
                self.warnings.append(f"{po_file}: Missing .po file header")

            # Check for fuzzy translations
            fuzzy_count = content.count('#, fuzzy')
            if fuzzy_count > 0:
                self.warnings.append(f"{po_file}: {fuzzy_count} fuzzy translations need review")

            # Check for untranslated strings
            untranslated_pattern = r'msgid\s+"([^"]*)"\s+msgstr\s+""'
            untranslated = re.findall(untranslated_pattern, content)
            if untranslated:
                untranslated_filtered = [msg for msg in untranslated if msg.strip()]
                if untranslated_filtered:
                    self.warnings.append(f"{po_file}: {len(untranslated_filtered)} untranslated strings")

        except UnicodeDecodeError:
            self.errors.append(f"{po_file}: Invalid encoding (should be UTF-8)")

    def _validate_translation_consistency(self) -> None:
        """Validate translation key consistency"""
        # Check for duplicate translation keys
        for key, occurrences in self.translation_patterns.items():
            if len(occurrences) > 1:
                # This is normal - same string can be used in multiple places
                # But check if they're very similar
                files = set(loc[0] for loc in occurrences)
                if len(files) > 3:  # Used in many files
                    self.warnings.append(f"Translation key '{key}' used in {len(files)} files - consider if it should be more specific")

    def _validate_translation_extraction(self) -> None:
        """Validate that translations can be properly extracted"""
        # Check if there are Python files with translations but no i18n setup
        has_translations = len(self.translation_patterns) > 0
        i18n_dir = self.workspace_root / "records_management" / "i18n"
        has_i18n = i18n_dir.exists()

        if has_translations and not has_i18n:
            self.warnings.append("Module uses translations but has no i18n directory")

        # Check for babel configuration
        babel_cfg = self.workspace_root / "records_management" / "babel.cfg"
        if has_translations and not babel_cfg.exists():
            self.warnings.append("No babel.cfg found - translation extraction may not work properly")

    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n🌐 Translation Validation Report")
        print("=" * 50)

        if self.errors:
            print(f"❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All translation validations passed!")

        print(f"\n📈 Summary: {len(self.translation_patterns)} unique translation strings found")

        # Show most used translations
        if self.translation_patterns:
            most_used = sorted(self.translation_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            print(f"\n🔝 Most used translations:")
            for key, occurrences in most_used:
                print(f"  • '{key}' - used in {len(occurrences)} locations")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent.parent

    validator = TranslationValidator(workspace_root)

    try:
        success = validator.validate_translations()
        validator.print_report()

        if success:
            print("\n✅ Translation validation completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ Translation validation failed with {len(validator.errors)} errors")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Translation validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
