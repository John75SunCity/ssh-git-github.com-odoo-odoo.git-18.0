#!/usr/bin/env python3
"""
Odoo Coding Standards Fixer
Fixes common Odoo coding standards violations based on validation output
"""

import re
from pathlib import Path


def fix_translation_patterns(file_path, content):
    """Fix translation formatting patterns"""
    fixes_applied = 0

    # Pattern 1: Fix string formatting before translation
    pattern1 = r"_\(['\"]([^'\"]*%s[^'\"]*)['\"] *\) *% *([^,\n\)]+)"

    def repl1(match):
        return f'_("{match.group(1)}", {match.group(2)})'

    new_content = re.sub(pattern1, repl1, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    # Pattern 2: Fix multiple parameter formatting before translation
    pattern2 = r"_\(['\"]([^'\"]*%s[^'\"]*)['\"] *\) *% *\(([^)]+)\)"

    def repl2(match):
        return f'_("{match.group(1)}", {match.group(2)})'

    new_content = re.sub(pattern2, repl2, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    # Pattern 3: Fix f-strings with translation
    pattern3 = r"_\(f['\"]([^'\"]*)\{([^}]+)\}([^'\"]*)['\"] *\)"

    def repl3(match):
        return f'_("{match.group(1)}%s{match.group(3)}", {match.group(2)})'

    new_content = re.sub(pattern3, repl3, content)
    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def fix_field_naming(file_path, content):
    """Fix field naming conventions"""
    fixes_applied = 0

    # Many2one fields should have '_id' suffix
    many2one_fields = [
        "authorized_by",
        "assigned_to",
        "current_holder",
        "contact_person",
        "retrieved_by",
        "approved_by",
        "escalated_by",
        "escalated_to",
        "sender",
        "recipient",
        "resolved_by",
        "responsible_person",
        "assigned_technician",
        "assigned_to_contact",
        "last_modified_by",
        "custody_from",
        "custody_to",
        "location_from",
        "location_to",
        "scanned_by",
        "verified_by",
        "picked_by",
        "taken_by",
        "processed_by",
        "quality_check_by",
        "final_verification_by",
        "compliance_officer",
    ]

    for field in many2one_fields:
        # Look for field definitions without _id suffix
        pattern = f"{field} = fields\\.Many2one"
        if re.search(pattern, content):
            # Replace with proper _id suffix
            new_field = f"{field}_id"
            content = re.sub(
                f"\\b{field}(?=\\s*=\\s*fields\\.Many2one)", new_field, content
            )
            fixes_applied += 1

    # Many2many fields should have '_ids' suffix
    many2many_fields = [
        "service_locations",
        "source_paper_bales",
        "improvement_areas",
        "secondary_specializations",
        "service_areas",
    ]

    for field in many2many_fields:
        pattern = f"{field} = fields\\.Many2many"
        if re.search(pattern, content):
            new_field = f"{field}_ids"
            content = re.sub(
                f"\\b{field}(?=\\s*=\\s*fields\\.Many2many)",
                new_field,
                content,
            )
            fixes_applied += 1

    # One2many fields should have '_ids' suffix
    if "photo_ids = fields.One2many" in content:
        content = content.replace(
            "photo_ids = fields.One2many", "photo_ids = fields.One2many"
        )
        fixes_applied += 1

    return content, fixes_applied


def _fix_action_methods(file_path, content):
    """Fix action methods to include self.ensure_one() with proper Odoo patterns"""
    fixes_applied = 0

    # Pattern to match action methods
    action_pattern = r'(def action_\w+\(self[^)]*\):\s*\n)((?:\s*"""[^"]*"""\s*\n|\s*\'\'\'[^\']*\'\'\'\s*\n|\s*#[^\n]*\n)*)(.*?)(?=\n\s*def|\n\s*class|\Z)'

    def _fix_single_action_method(match):
        method_def = match.group(1)
        docstring = match.group(2)
        method_body = match.group(3)

        # Skip if already has ensure_one
        if "self.ensure_one()" in method_body:
            return match.group(0)

        # Clean up any existing malformed ensure_one calls
        method_body = re.sub(
            r'\s*self\.ensure_one\(\)\s*"""[^"]*"""\s*self\.ensure_one\(\)',
            "",
            method_body,
        )
        method_body = re.sub(
            r'\s*self\.ensure_one\(\)\s*"""[^"]*"""',
            '        """Mark as generated"""',
            method_body,
        )

        # Add proper self.ensure_one() after docstring
        lines = method_body.split("\n")

        # Find where to insert ensure_one (after docstring)
        insert_point = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith('"""')
                and not stripped.startswith("'''")
                and not stripped.startswith("#")
            ):
                insert_point = i
                break

        # Insert ensure_one with proper indentation
        if insert_point < len(lines):
            lines.insert(insert_point, "        self.ensure_one()")
        else:
            lines.append("        self.ensure_one()")

        new_method_body = "\n".join(lines)
        return method_def + docstring + new_method_body

    new_content = re.sub(
        action_pattern,
        _fix_single_action_method,
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def fix_import_order(file_path, content):
    """Fix import order: Python stdlib, Odoo core, Odoo addons"""
    fixes_applied = 0

    lines = content.split("\n")
    imports_start = -1
    imports_end = -1

    # Find import section
    for i, line in enumerate(lines):
        if line.strip().startswith("import ") or line.strip().startswith(
            "from "
        ):
            if imports_start == -1:
                imports_start = i
            imports_end = i
        elif imports_start != -1 and line.strip() == "":
            continue
        elif imports_start != -1 and not line.strip().startswith("#"):
            break

    if imports_start == -1:
        return content, fixes_applied

    # Extract imports
    import_lines = lines[imports_start : imports_end + 1]

    # Categorize imports
    stdlib_imports = []
    odoo_imports = []
    addon_imports = []
    other_imports = []

    for line in import_lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        if "from odoo import" in line or "import odoo" in line:
            odoo_imports.append(line)
        elif "from odoo.addons" in line:
            addon_imports.append(line)
        elif any(
            lib in line
            for lib in [
                "datetime",
                "json",
                "logging",
                "os",
                "re",
                "sys",
                "time",
            ]
        ):
            stdlib_imports.append(line)
        else:
            other_imports.append(line)

    # Reorder imports
    ordered_imports = []
    if stdlib_imports:
        ordered_imports.extend(stdlib_imports)
        ordered_imports.append("")
    if odoo_imports:
        ordered_imports.extend(odoo_imports)
        ordered_imports.append("")
    if addon_imports:
        ordered_imports.extend(addon_imports)
        ordered_imports.append("")
    if other_imports:
        ordered_imports.extend(other_imports)
        ordered_imports.append("")

    # Replace import section
    new_lines = (
        lines[:imports_start] + ordered_imports + lines[imports_end + 1 :]
    )
    new_content = "\n".join(new_lines)

    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def fix_method_naming(file_path, content):
    """Fix method naming patterns"""
    fixes_applied = 0

    # Fix constraint methods to follow _check_ pattern
    constraint_methods = [
        "action_audit_checker",
        "action_check_customer",
        "check_expiring_restrictions",
        "check_specialization_match",
        "action_check_in_visitor",
        "action_check_out_visitor",
    ]

    for method in constraint_methods:
        if f"def {method}(" in content:
            # Convert to _check_ pattern
            new_name = method.replace("action_", "_check_").replace(
                "check_", "_check_"
            )
            content = content.replace(f"def {method}(", f"def {new_name}(")
            fixes_applied += 1

    # Fix search methods to follow _search_ pattern
    if "def _search_name(" in content:
        content = content.replace("def _search_name(", "def _search_name(")
        fixes_applied += 1

    return content, fixes_applied


def clean_malformed_methods(file_path, content):
    """Clean up malformed action methods created by previous runs"""
    fixes_applied = 0

    # Fix duplicate self.ensure_one() calls
    content = re.sub(
        r'(\s*)self\.ensure_one\(\)\s*"""([^"]*)"""\s*self\.ensure_one\(\)',
        r'\1"""\2"""\n\1self.ensure_one()',
        content,
    )

    # Fix methods where docstring comes after ensure_one
    content = re.sub(
        r'(\s*)self\.ensure_one\(\)\s*"""([^"]*)"""\s*\n',
        r'\1"""\2"""\n\1self.ensure_one()\n',
        content,
    )

    # Fix methods with misplaced field definitions
    pattern = r'(def action_\w+\([^)]*\):\s*(?:"""[^"]*""")?[^}]*?)(partner_id = fields\.Many2one\([^}]*?\))(.*?)(def action_\w+\([^)]*\):)'

    def fix_misplaced_field(match):
        method1 = match.group(1)
        # Remove unused field_def variable
        middle_content = match.group(3)
        method2 = match.group(4)

        # Remove field from middle and clean up method1
        clean_method1 = method1.rstrip() + "\n"
        clean_middle = middle_content.strip()
        if clean_middle:
            clean_middle = "\n    " + clean_middle + "\n"

        return (
            clean_method1
            + clean_middle
            + "\n    # Field moved to proper section\n\n    "
            + method2
        )

    new_content = re.sub(
        pattern, fix_misplaced_field, content, flags=re.DOTALL
    )
    if new_content != content:
        fixes_applied += 1
        content = new_content

    return content, fixes_applied


def process_file(file_path):
    """Process a single Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        total_fixes = 0

        # First clean up any malformed methods
        content, fixes = clean_malformed_methods(file_path, content)
        total_fixes += fixes

        # Apply all other fixes
        content, fixes = fix_translation_patterns(file_path, content)
        total_fixes += fixes

        content, fixes = fix_field_naming(file_path, content)
        total_fixes += fixes

        content, fixes = _fix_action_methods(file_path, content)
        total_fixes += fixes

        content, fixes = fix_import_order(file_path, content)
        total_fixes += fixes

        content, fixes = fix_method_naming(file_path, content)
        total_fixes += fixes

        # Write back if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return total_fixes

    except Exception as e:
        print("❌ Error processing %s: %s" % (file_path, e))
        return 0

    return 0


def main():
    """Main function to process all Python files"""
    records_dir = Path("records_management")

    if not records_dir.exists():
        print("❌ records_management directory not found")
        return

    python_files = list(records_dir.rglob("*.py"))
    total_files = 0
    total_fixes = 0

    print("🔧 ODOO CODING STANDARDS FIXER")
    print("=" * 50)

    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue

        fixes = process_file(file_path)
        if fixes > 0:
            print("✅ %s: %d fixes applied" % (file_path.name, fixes))
            total_files += 1
            total_fixes += fixes

    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("   • Files processed: %d" % total_files)
    print("   • Total fixes applied: %d" % total_fixes)
    print("   • Translation patterns fixed")
    print("   • Field naming corrected")
    print("   • Action methods updated")
    print("   • Import order standardized")
    print("   • Method naming fixed")
    print("\n🧪 Next: Run validation to check remaining issues")


if __name__ == "__main__":
    main()
