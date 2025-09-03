#!/usr/bin/env python3
"""
Fix Translation Pattern Consistency

This script fixes inconsistent translation patterns in the Records Management module.
It converts patterns like:
  OLD: _('Text %s') % value
  NEW: _('Text %s', value)

This ensures consistency with Odoo's recommended translation practices.
"""

import os
import re
from pathlib import Path
from typing import List


class TranslationFixer:
    """Fix translation pattern inconsistencies"""

    def __init__(self, module_path: Path):
        self.module_path = module_path
        self.fixed_files: List[str] = []

    def fix_translation_patterns(self) -> None:
        """Fix all translation pattern inconsistencies"""
        print("🔧 Fixing translation pattern consistency...")

        # Find all Python files
        python_files = list(self.module_path.glob("**/*.py"))

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                # Pattern to match: _("Text %s") % value
                # This regex looks for translation calls followed by % formatting
                pattern = r'_\(\s*["\'][^"\'%]*%[^"\'%]*["\']\s*\)\s*%\s*([^%\n]+)'

                def replace_match(match):
                    # Extract the translation part and the formatting part
                    translation_part = match.group(0).split(') %')[0] + ')'
                    formatting_part = match.group(0).split(') %')[1]

                    # Remove the % and reconstruct as proper format
                    # Convert _("Text %s") % value → _("Text %s", value)
                    if formatting_part.strip():
                        return f"{translation_part[:-1]}, {formatting_part.strip()})"
                    else:
                        return match.group(0)  # No change if no formatting part

                # Apply the fix
                new_content = re.sub(pattern, replace_match, content)

                # Only write if content changed
                if new_content != original_content:
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    self.fixed_files.append(str(py_file))
                    print(f"  ✅ Fixed: {py_file.name}")

            except Exception as e:
                print(f"  ❌ Error processing {py_file.name}: {str(e)}")

    def print_summary(self) -> None:
        """Print summary of fixes"""
        if self.fixed_files:
            print("\n📊 TRANSLATION PATTERN FIXES COMPLETED")
            print(f"   Files fixed: {len(self.fixed_files)}")
            print("\n   Pattern changed:")
            print("   ❌ OLD: _('Text %s') % value")
            print("   ✅ NEW: _('Text %s', value)")
            print("\n   Fixed files:")
            for file in self.fixed_files:
                print(f"     - {Path(file).name}")
        else:
            print("\n📊 No translation pattern fixes needed")


def main():
    """Main function"""
    # Find the module path
    current_dir = Path(__file__).parent.parent
    module_path = current_dir / "records_management"

    if not module_path.exists():
        print(f"❌ Error: Module directory {module_path} does not exist")
        return 1

    # Fix translation patterns
    fixer = TranslationFixer(module_path)
    fixer.fix_translation_patterns()
    fixer.print_summary()

    return 0


if __name__ == "__main__":
    exit(main())
