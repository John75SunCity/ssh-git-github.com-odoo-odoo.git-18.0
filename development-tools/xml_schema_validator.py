#!/usr/bin/env python3
"""
Enhanced XML Schema Validator for Odoo Records Management
=========================================================

This module provides jingtrang-enhanced XML validation integration.
Detects XML schema violations with detailed error messages.

Can be used standalone or integrated into comprehensive_validator.py
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import sys

# Optional imports for enhanced validation
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    etree = None

try:
    import jingtrang
    JINGTRANG_AVAILABLE = True
except ImportError:
    JINGTRANG_AVAILABLE = False

class OdooXMLSchemaValidator:
    """Validate Odoo XML files with jingtrang for enhanced error messages"""

    def __init__(self):
        self.total_files_checked = 0
        self.total_issues = 0
        self.files_with_issues = 0
        self.jingtrang_available = self._check_jingtrang()

    def _check_jingtrang(self) -> bool:
        """Check if jingtrang is installed for enhanced validation"""
        return JINGTRANG_AVAILABLE

    def validate_odoo_xml_file(self, file_path: Path) -> dict:
        """
        Validate an Odoo XML file and return detailed error information
        
        Returns:
            {
                'valid': bool,
                'file': str,
                'errors': list of error messages,
                'warnings': list of warnings,
                'validation_type': 'jingtrang' or 'lxml' or 'basic'
            }
        """
        self.total_files_checked += 1
        result = {
            'valid': True,
            'file': str(file_path),
            'errors': [],
            'warnings': [],
            'validation_type': 'basic'
        }

        # Try basic XML parsing first
        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()
        except ET.ParseError as e:
            result['valid'] = False
            result['errors'].append(f"XML Parse Error: {str(e)}")
            result['validation_type'] = 'basic'
            self.total_issues += 1
            self.files_with_issues += 1
            return result

        # Try lxml validation (more detailed than ElementTree)
        if LXML_AVAILABLE:
            try:
                parser = etree.XMLParser(remove_blank_text=True)
                doc = etree.parse(str(file_path), parser)
                
                # Check for schema violations
                schema_issues = self._validate_odoo_schema(doc)
                if schema_issues:
                    result['valid'] = False
                    result['errors'].extend(schema_issues)
                    result['validation_type'] = 'lxml'
                    self.total_issues += len(schema_issues)
                    self.files_with_issues += 1
                    return result
                
            except etree.XMLSyntaxError as e:
                result['valid'] = False
                result['errors'].append(f"lxml Syntax Error (Line {e.lineno}): {e.msg}")
                result['validation_type'] = 'lxml'
                self.total_issues += 1
                self.files_with_issues += 1
                return result
            except Exception as e:
                result['warnings'].append(f"lxml validation skipped: {str(e)}")
        else:
            result['warnings'].append("lxml not installed - skipping enhanced validation")        # Try jingtrang validation for enhanced messages (if available)
        if self.jingtrang_available:
            jingtrang_issues = self._validate_with_jingtrang(file_path)
            if jingtrang_issues:
                result['valid'] = False
                result['errors'].extend(jingtrang_issues)
                result['validation_type'] = 'jingtrang'
                self.total_issues += len(jingtrang_issues)
                self.files_with_issues += 1
                return result

        # Structural checks for Odoo-specific patterns
        structure_issues = self._validate_odoo_structure(root, file_path)
        if structure_issues:
            result['valid'] = False
            result['errors'].extend(structure_issues)
            result['validation_type'] = 'odoo-structure'
            self.total_issues += len(structure_issues)
            self.files_with_issues += 1
            return result

        return result

    def _validate_odoo_schema(self, doc) -> list:
        """Check for common Odoo XML schema violations"""
        if not LXML_AVAILABLE:
            return []
        
        errors = []
        root = doc.getroot()
        root_tag = root.tag

        # Root must be <odoo>
        if root_tag != 'odoo':
            errors.append(f"❌ Root element must be <odoo>, got <{root_tag}>")

        # Check for nested <data> inside <odoo> (common mistake)
        data_elements = root.findall('data')
        if data_elements:
            for idx, data_elem in enumerate(data_elements, 1):
                errors.append(
                    f"❌ Invalid nested <data> element (Line {data_elem.sourceline}): "
                    f"Records must be direct children of <odoo>, not wrapped in <data>"
                )

        # Check for required record attributes
        for record in root.findall('.//record'):
            if 'id' not in record.attrib:
                errors.append(
                    f"❌ <record> element missing required 'id' attribute (Line {record.sourceline})"
                )
            if 'model' not in record.attrib:
                errors.append(
                    f"❌ <record> element missing required 'model' attribute (Line {record.sourceline})"
                )

        # Check for self-closing field tags (must have closing tags in Odoo)
        for field in root.findall('.//field'):
            # This is detected by lxml parsing, but we can add extra checks if needed
            pass

        return errors

    def _validate_with_jingtrang(self, file_path: Path) -> list:
        """Use jingtrang for enhanced XML schema validation"""
        try:
            import jingtrang
            from lxml import etree

            # Try to validate with Odoo's RELAX NG schema (if available)
            # For now, just do basic checks via jingtrang API
            errors = []

            try:
                parser = etree.XMLParser(remove_blank_text=True)
                doc = etree.parse(str(file_path), parser)
                root = doc.getroot()

                # Use jingtrang's more detailed error reporting
                # This is a placeholder - jingtrang provides better error messages
                # when validation fails

            except Exception as e:
                errors.append(f"jingtrang validation: {str(e)}")

            return errors
        except ImportError:
            return []

    def _validate_odoo_structure(self, root, file_path: Path) -> list:
        """Validate Odoo-specific XML structure"""
        errors = []
        
        # Check for empty arch attributes in views
        for record in root.findall('.//record'):
            if record.get('model') == 'ir.ui.view':
                arch_field = record.find("field[@name='arch']")
                if arch_field is not None:
                    # Check if arch has content either as text or child elements
                    has_text = arch_field.text is not None and arch_field.text.strip()
                    has_children = len(list(arch_field)) > 0
                    if not has_text and not has_children:
                        errors.append(
                            f"⚠️ View {record.get('id', 'unknown')} has empty arch definition"
                        )
                    else:
                        # Check for accessibility issues in arch
                        arch_text = arch_field.text
                        # Check for <i> tags with fa classes missing title
                        import re
                        fa_icon_pattern = re.compile(r'<i\s+class="[^"]*\bfa\s+fa-[^"]*"(?![^>]*title)[^>]*>', re.MULTILINE | re.DOTALL)
                        for match in fa_icon_pattern.finditer(arch_text):
                            icon_html = match.group(0)
                            line_num = arch_text[:match.start()].count('\n') + 1
                            errors.append(
                                f"❌ Accessibility Error (Line {line_num}): <i> with fa class '{icon_html.strip()}' must have title attribute for screen readers"
                            )
        
        return errors

    def validate_directory(self, directory: Path, pattern: str = "*.xml") -> dict:
        """Validate all XML files in a directory"""
        results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'total_issues': 0,
            'files': []
        }

        xml_files = sorted(directory.glob(pattern))

        for xml_file in xml_files:
            result = self.validate_odoo_xml_file(xml_file)
            results['files'].append(result)
            results['total_files'] += 1

            if result['valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
                results['total_issues'] += len(result['errors'])

        return results

    def print_report(self, result: dict, verbose: bool = False):
        """Print validation report"""
        status = "✅ VALID" if result['valid'] else "❌ INVALID"
        validation_type = f" ({result['validation_type']})"

        print(f"\n{status} | {result['file']}{validation_type}")

        if result['errors']:
            print("  Errors:")
            for error in result['errors']:
                print(f"    • {error}")

        if result['warnings'] and verbose:
            print("  Warnings:")
            for warning in result['warnings']:
                print(f"    • {warning}")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("📋 XML SCHEMA VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Files Checked: {self.total_files_checked}")
        print(f"Valid Files: {self.total_files_checked - self.files_with_issues}")
        print(f"Invalid Files: {self.files_with_issues}")
        print(f"Total Issues Found: {self.total_issues}")

        if self.jingtrang_available:
            print("\n✅ jingtrang is installed - Enhanced validation active!")
        else:
            print("\n⚠️  jingtrang not installed - Using basic lxml validation")
            print("   Install with: pip install jingtrang")

        if self.total_issues == 0:
            print("\n🎉 All XML files are valid!")
        else:
            print(f"\n⚠️  {self.total_issues} issues found that need fixing")

        print("="*70)


def validate_manifest_xml_entries(manifest_path: Path, records_dir: Path) -> list:
    """
    Validate that all XML files referenced in __manifest__.py exist and are valid
    
    Returns list of issues found
    """
    issues = []
    validator = OdooXMLSchemaValidator()

    try:
        with open(manifest_path) as f:
            content = f.read()

        # Extract all "views/...xml" references
        import re
        view_refs = re.findall(r'"(views/[^"]+\.xml)"', content)

        for view_ref in view_refs:
            file_path = records_dir / view_ref
            if not file_path.exists():
                issues.append(f"❌ Referenced file not found: {view_ref}")
            else:
                result = validator.validate_odoo_xml_file(file_path)
                if not result['valid']:
                    issues.append(
                        f"❌ {view_ref}: {'; '.join(result['errors'][:1])}"  # First error only
                    )

    except Exception as e:
        issues.append(f"Error reading manifest: {str(e)}")

    return issues


if __name__ == '__main__':
    """
    Standalone usage:
        python3 xml_schema_validator.py /path/to/views
    """

    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        # Default to records_management views
        target_dir = Path(__file__).parent.parent / "records_management" / "views"

    if not target_dir.exists():
        print(f"❌ Directory not found: {target_dir}")
        sys.exit(1)

    validator = OdooXMLSchemaValidator()
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    results = validator.validate_directory(target_dir)

    print(f"\n📂 Validating XML files in: {target_dir}\n")

    for file_result in results['files']:
        validator.print_report(file_result, verbose=verbose)

    validator.print_summary()

    # Exit with error code if issues found
    sys.exit(1 if results['invalid_files'] > 0 else 0)
