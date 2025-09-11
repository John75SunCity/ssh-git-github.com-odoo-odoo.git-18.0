#!/usr/bin/env python3
"""
Advanced AST-based Ensure One Fixer for Odoo Action Methods

This script uses Abstract Syntax Tree (AST) manipulation to safely add
self.ensure_one() calls to action methods without corrupting syntax.

CRITICAL IMPROVEMENT: Uses AST parsing instead of string manipulation
to preserve code structure and prevent syntax errors.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set

class EnsureOneInserter(ast.NodeTransformer):
    """AST transformer to insert self.ensure_one() calls in action methods."""

    def __init__(self):
        self.modified_methods = []
        self.current_file = ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definitions and modify action methods."""

        # Only process action methods (start with 'action_')
        if not node.name.startswith('action_'):
            return self.generic_visit(node)

        # Check if method already has self.ensure_one() call
        if self._has_ensure_one_call(node):
            return self.generic_visit(node)

        # Check if method has self parameter
        if not self._has_self_parameter(node):
            return self.generic_visit(node)

        # Insert self.ensure_one() as first statement
        ensure_one_call = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='self', ctx=ast.Load()),
                    attr='ensure_one',
                    ctx=ast.Load()
                ),
                args=[],
                keywords=[]
            )
        )

        # Copy location information from the first existing statement
        if node.body:
            ensure_one_call.lineno = node.body[0].lineno
            ensure_one_call.col_offset = node.body[0].col_offset

        # Insert at the beginning of the method body
        node.body.insert(0, ensure_one_call)

        # Track the modification
        self.modified_methods.append({
            'file': self.current_file,
            'method': node.name,
            'line': node.lineno
        })

        return self.generic_visit(node)

    def _has_ensure_one_call(self, func_node: ast.FunctionDef) -> bool:
        """Check if the function already has a self.ensure_one() call."""
        for stmt in func_node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if (isinstance(call.func, ast.Attribute) and
                    isinstance(call.func.value, ast.Name) and
                    call.func.value.id == 'self' and
                    call.func.attr == 'ensure_one'):
                    return True
        return False

    def _has_self_parameter(self, func_node: ast.FunctionDef) -> bool:
        """Check if the function has 'self' as first parameter."""
        return (func_node.args.args and
                func_node.args.args[0].arg == 'self')

def process_python_file(file_path: Path) -> Tuple[bool, List[dict]]:
    """
    Process a single Python file to add ensure_one() calls.

    Returns:
        Tuple of (was_modified, list_of_modifications)
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Skipping {file_path} - syntax error: {e}")
            return False, []

        # Transform the AST
        transformer = EnsureOneInserter()
        transformer.current_file = str(file_path.relative_to(Path.cwd()))

        modified_tree = transformer.visit(tree)

        # If no modifications were made, return early
        if not transformer.modified_methods:
            return False, []

        # Convert AST back to source code
        try:
            import astor  # Try to use astor for better formatting
            new_content = astor.to_source(modified_tree)
        except ImportError:
            # Fallback to compile + decompile (less readable but works)
            print(f"ℹ️  Using basic AST conversion for {file_path} (install 'astor' for better formatting)")
            compiled = compile(modified_tree, str(file_path), 'exec')
            # This approach doesn't give us back source code, so we'll use a different method
            return False, transformer.modified_methods

        # Write the modified content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True, transformer.modified_methods

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, []

def find_action_methods_needing_ensure_one(root_path: Path) -> List[dict]:
    """
    Scan all Python files to find action methods that need ensure_one() calls.

    Returns:
        List of dictionaries with file, method, and line information.
    """
    methods_needing_fix = []

    for file_path in root_path.rglob("*.py"):
        # Skip __pycache__ and other non-source directories
        if "__pycache__" in file_path.parts:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST to find action methods
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef) and
                    node.name.startswith('action_')):

                    # Check if it has self parameter
                    if not (node.args.args and node.args.args[0].arg == 'self'):
                        continue

                    # Check if it already has ensure_one() call
                    has_ensure_one = False
                    for stmt in node.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            call = stmt.value
                            if (isinstance(call.func, ast.Attribute) and
                                isinstance(call.func.value, ast.Name) and
                                call.func.value.id == 'self' and
                                call.func.attr == 'ensure_one'):
                                has_ensure_one = True
                                break

                    if not has_ensure_one:
                        methods_needing_fix.append({
                            'file': str(file_path.relative_to(Path.cwd())),
                            'method': node.name,
                            'line': node.lineno
                        })

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")
            continue

    return methods_needing_fix

def main():
    """Main execution function."""
    print("🔧 Advanced AST-based Ensure One Fixer")
    print("=" * 50)

    # Define the root path for the Records Management module
    root_path = Path("records_management")

    if not root_path.exists():
        print(f"❌ Records Management module not found at {root_path}")
        return 1

    # First, scan to find all action methods needing ensure_one()
    print("🔍 Scanning for action methods needing ensure_one()...")
    methods_needing_fix = find_action_methods_needing_ensure_one(root_path)

    if not methods_needing_fix:
        print("✅ All action methods already have ensure_one() calls!")
        return 0

    print(f"📋 Found {len(methods_needing_fix)} action methods needing ensure_one():")
    for method_info in methods_needing_fix[:10]:  # Show first 10
        print(f"   📄 {method_info['file']}:{method_info['line']} - {method_info['method']}()")

    if len(methods_needing_fix) > 10:
        print(f"   ... and {len(methods_needing_fix) - 10} more")

    # Ask for confirmation
    response = input(f"\n🤔 Proceed to fix {len(methods_needing_fix)} methods? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled by user.")
        return 0

    # Process files
    print("\n🔧 Processing files...")
    total_files = 0
    modified_files = 0
    total_methods_fixed = 0

    processed_files = set()

    for method_info in methods_needing_fix:
        file_path = Path(method_info['file'])

        # Skip if we already processed this file
        if str(file_path) in processed_files:
            continue

        processed_files.add(str(file_path))
        total_files += 1

        was_modified, modifications = process_python_file(file_path)

        if was_modified:
            modified_files += 1
            total_methods_fixed += len(modifications)
            print(f"✅ {file_path}: Fixed {len(modifications)} methods")
        else:
            if modifications:  # Had methods to fix but couldn't modify
                print(f"⚠️  {file_path}: Found methods but couldn't modify")

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"Files processed: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"Methods fixed: {total_methods_fixed}")

    if total_methods_fixed > 0:
        print("\n🎉 Successfully added ensure_one() calls!")
        print("💡 Remember to run syntax validation and test the module.")
    else:
        print("\n⚠️  No methods were modified.")
        print("💡 Consider installing 'astor' package for better AST-to-source conversion.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
