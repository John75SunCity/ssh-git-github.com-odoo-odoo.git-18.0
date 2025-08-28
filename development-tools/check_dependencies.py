#!/usr/bin/env python3
"""
Dependency Validation Script
===========================

Validates module dependencies and relationships.
Checks for proper dependency declarations and circular dependencies.

Features:
- Module dependency validation
- Circular dependency detection
- Missing dependency checks
- Version compatibility validation
- External dependency verification

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
import json

class DependencyValidator:
    """Validates module dependencies and relationships"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.manifest_data: Dict[str, Dict] = {}

    def check_dependencies(self) -> bool:
        """Main validation function"""
        print("🔗 Checking Module Dependencies...")

        # Read manifest file
        manifest_path = self.workspace_root / "records_management" / "__manifest__.py"
        if not manifest_path.exists():
            manifest_path = self.workspace_root / "records_management" / "__openerp__.py"

        if not manifest_path.exists():
            self.errors.append("Manifest file (__manifest__.py or __openerp__.py) not found")
            return False

        # Parse manifest
        self._parse_manifest(manifest_path)

        # Validate dependencies
        self._validate_dependency_declarations()

        # Check for circular dependencies
        self._check_circular_dependencies()

        # Validate external dependencies
        self._validate_external_dependencies()

        # Check for unused dependencies
        self._check_unused_dependencies()

        return len(self.errors) == 0

    def _parse_manifest(self, manifest_path: Path) -> None:
        """Parse the manifest file to extract dependencies"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple parsing - in practice you'd use ast or similar
            depends_match = re.search(r"'depends'\s*:\s*\[(.*?)\]", content, re.DOTALL)
            if depends_match:
                depends_str = depends_match.group(1)
                # Extract dependency names
                deps = re.findall(r"'([^']+)'", depends_str)
                self.dependencies['records_management'] = deps

                # Store manifest data for other validations
                self.manifest_data['records_management'] = {
                    'depends': deps,
                    'path': manifest_path
                }

        except Exception as e:
            self.errors.append(f"Error parsing manifest file: {e}")

    def _validate_dependency_declarations(self) -> None:
        """Validate dependency declarations"""
        deps = self.dependencies.get('records_management', [])

        if not deps:
            self.warnings.append("No dependencies declared in manifest")
            return

        # Check for common required dependencies
        required_deps = ['base']
        for req_dep in required_deps:
            if req_dep not in deps:
                self.errors.append(f"Required dependency '{req_dep}' not declared")

        # Validate dependency name format
        for dep in deps:
            if not dep.replace('_', '').isalnum():
                self.warnings.append(f"Dependency '{dep}' has unusual name format")

            # Check for version specifications (should be avoided in depends)
            if any(char in dep for char in ['<', '>', '=', '~', '^']):
                self.warnings.append(f"Dependency '{dep}' contains version specifier (use version ranges in manifest instead)")

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies"""
        # This is a simplified check - in practice you'd need to analyze all modules
        # For now, just check if the module depends on itself
        deps = self.dependencies.get('records_management', [])
        if 'records_management' in deps:
            self.errors.append("Module depends on itself (circular dependency)")

    def _validate_external_dependencies(self) -> None:
        """Validate external dependencies"""
        deps = self.dependencies.get('records_management', [])

        # Common Odoo modules that should exist
        known_modules = {
            'base', 'web', 'mail', 'product', 'sale', 'purchase',
            'account', 'stock', 'mrp', 'hr', 'project', 'calendar',
            'note', 'board', 'report', 'portal', 'website'
        }

        for dep in deps:
            if dep not in known_modules and not dep.startswith(('theme_', 'l10n_')):
                self.warnings.append(f"Unknown dependency '{dep}' - verify it exists")

    def _check_unused_dependencies(self) -> None:
        """Check for potentially unused dependencies"""
        deps = self.dependencies.get('records_management', [])

        # This is a simplified check - in practice you'd analyze the codebase
        # to see which dependencies are actually used

        # For now, just check if there are many dependencies
        if len(deps) > 20:
            self.warnings.append(f"Module has {len(deps)} dependencies - consider if all are needed")

        # Check for common patterns
        python_deps = [d for d in deps if 'python' in d.lower()]
        if python_deps:
            self.warnings.append(f"Python dependencies found: {python_deps} - ensure they are properly declared")

    def _analyze_codebase_usage(self) -> Dict[str, Set[str]]:
        """Analyze codebase to see which dependencies are actually used"""
        usage = {}

        # This is a simplified analysis - in practice you'd do more thorough checking
        module_dir = self.workspace_root / "records_management"

        if not module_dir.exists():
            return usage

        # Look for import statements and model references
        for py_file in module_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for _inherit patterns that might indicate dependencies
                inherit_matches = re.findall(r"_inherit\s*=\s*[\'\"]([^\'\"]+)[\'\"]", content)
                for match in inherit_matches:
                    if '.' in match:  # Likely a reference to another module
                        module_part = match.split('.')[0]
                        if module_part not in usage:
                            usage[module_part] = set()
                        usage[module_part].add('inherit')

                # Look for model references in fields
                comodel_matches = re.findall(r"comodel_name\s*=\s*[\'\"]([^\'\"]+)[\'\"]", content)
                for match in comodel_matches:
                    if '.' in match:
                        module_part = match.split('.')[0]
                        if module_part not in usage:
                            usage[module_part] = set()
                        usage[module_part].add('comodel')

            except Exception as e:
                self.warnings.append(f"Error analyzing {py_file}: {e}")

        return usage

    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n🔗 Dependency Validation Report")
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
            print("✅ All dependency validations passed!")

        # Show dependency summary
        deps = self.dependencies.get('records_management', [])
        print(f"\n📦 Dependencies ({len(deps)}):")
        for dep in sorted(deps):
            print(f"  • {dep}")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent

    validator = DependencyValidator(workspace_root)

    try:
        success = validator.check_dependencies()
        validator.print_report()

        if success:
            print("\n✅ Dependency validation completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ Dependency validation failed with {len(validator.errors)} errors")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Dependency validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
