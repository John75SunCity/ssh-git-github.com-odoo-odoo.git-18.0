#!/usr/bin/env python3
"""
Action Methods Ensure One Fixer

Script to add self.ensure_one() at the beginning of all action methods
that don't already have it, following Odoo best practices.
"""

import os
import re
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionMethodFixer:
    """Fix action methods to include self.ensure_one() at the beginning"""

    def __init__(self):
        self.files_processed = 0
        self.methods_fixed = 0
        self.errors = []

    def should_have_ensure_one(self, method_name, method_content):
        """Check if method should have ensure_one()"""
        # Action methods that should have ensure_one()
        action_patterns = [
            r'^action_',
            r'^button_',
            r'^confirm_',
            r'^cancel_',
            r'^approve_',
            r'^reject_',
            r'^complete_',
            r'^start_',
            r'^stop_',
            r'^submit_',
            r'^validate_',
            r'^process_',
            r'^execute_',
            r'^perform_',
            r'^update_',
            r'^generate_',
            r'^create_',
            r'^delete_',
            r'^archive_',
            r'^restore_'
        ]

        # Check if method name matches action patterns
        if not any(re.match(pattern, method_name) for pattern in action_patterns):
            return False

        # Skip if already has ensure_one()
        if 'self.ensure_one()' in method_content:
            return False

        # Skip if it's a @api.model method (doesn't work on recordsets)
        if '@api.model' in method_content:
            return False

        # Skip if it already loops through self (for item in self:)
        if re.search(r'for\s+\w+\s+in\s+self\s*:', method_content):
            return False

        # Skip if it has explicit multi-record handling
        if 'for record in self' in method_content or 'for item in self' in method_content:
            return False

        return True

    def extract_method_info(self, content):
        """Extract method information from Python content"""
        methods = []

        # Find all method definitions
        method_pattern = r'(def\s+(action_\w+|button_\w+|confirm_\w+|cancel_\w+|approve_\w+|reject_\w+|complete_\w+|start_\w+|stop_\w+|submit_\w+|validate_\w+|process_\w+|execute_\w+|perform_\w+|update_\w+|generate_\w+|create_\w+|delete_\w+|archive_\w+|restore_\w+)\s*\([^)]*\)\s*:)'

        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_start = match.start()
            method_name = match.group(2)

            # Find method end by looking for next method or class definition at same indentation
            lines = content[method_start:].split('\n')
            method_lines = [lines[0]]  # Include the def line
            base_indent = len(lines[0]) - len(lines[0].lstrip())

            for i, line in enumerate(lines[1:], 1):
                # Stop at next method/class at same or less indentation
                if line.strip() and len(line) - len(line.lstrip()) <= base_indent:
                    if re.match(r'\s*(def |class |@)', line):
                        break
                method_lines.append(line)

            method_content = '\n'.join(method_lines)

            methods.append({
                'name': method_name,
                'content': method_content,
                'start_pos': method_start,
                'def_line': match.group(1)
            })

        return methods

    def fix_method(self, method_info, content):
        """Fix a single method by adding ensure_one()"""
        method_content = method_info['content']

        if not self.should_have_ensure_one(method_info['name'], method_content):
            return content

        lines = method_content.split('\n')
        def_line = lines[0]

        # Find the insertion point (after def line and docstring)
        insertion_line = 1

        # Skip docstring if present
        for i, line in enumerate(lines[1:], 1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Find end of docstring
                quote_type = '"""' if stripped.startswith('"""') else "'''"
                if stripped.count(quote_type) >= 2:
                    # Single line docstring
                    insertion_line = i + 1
                    break
                else:
                    # Multi-line docstring - find closing
                    for j, next_line in enumerate(lines[i+1:], i+1):
                        if quote_type in next_line:
                            insertion_line = j + 1
                            break
                break
            elif stripped.startswith('#'):
                # Skip comments
                continue
            else:
                # Found first code line
                insertion_line = i
                break

        # Determine indentation from def line
        base_indent = len(def_line) - len(def_line.lstrip())
        method_indent = ' ' * (base_indent + 4)

        # Insert ensure_one() at the correct position
        ensure_one_line = f"{method_indent}self.ensure_one()"

        # Build new method content
        new_lines = lines[:insertion_line] + [ensure_one_line] + lines[insertion_line:]
        new_method_content = '\n'.join(new_lines)

        # Replace in full content
        old_method_start = method_info['start_pos']
        old_method_end = old_method_start + len(method_content)

        new_content = (content[:old_method_start] +
                      new_method_content +
                      content[old_method_end:])

        logger.info(f"  ✅ Fixed method: {method_info['name']}")
        self.methods_fixed += 1

        return new_content

    def fix_file(self, filepath):
        """Fix all action methods in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Skip if file doesn't contain action methods
            if not re.search(r'def\s+(action_|button_|confirm_|cancel_)', original_content):
                return

            content = original_content
            methods = self.extract_method_info(content)

            if not methods:
                return

            logger.info(f"📄 Processing {os.path.basename(filepath)} ({len(methods)} action methods found)")

            # Fix methods (in reverse order to maintain positions)
            for method_info in reversed(methods):
                content = self.fix_method(method_info, content)

            # Only write if content changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"  💾 Updated {os.path.basename(filepath)}")

            self.files_processed += 1

        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)

    def fix_all_files(self, base_path="records_management/models"):
        """Fix all Python files in the models directory"""
        logger.info("🔧 ACTION METHODS ENSURE_ONE() FIXER")
        logger.info("=" * 50)

        if not os.path.exists(base_path):
            logger.error(f"Path {base_path} does not exist")
            return

        python_files = []
        for filename in os.listdir(base_path):
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(base_path, filename)
                python_files.append(filepath)

        logger.info(f"Found {len(python_files)} Python files to process")

        for filepath in sorted(python_files):
            self.fix_file(filepath)

        logger.info("=" * 50)
        logger.info(f"🎯 SUMMARY:")
        logger.info(f"  • Files processed: {self.files_processed}")
        logger.info(f"  • Methods fixed: {self.methods_fixed}")
        logger.info(f"  • Errors: {len(self.errors)}")

        if self.errors:
            logger.info(f"\n❌ ERRORS:")
            for error in self.errors:
                logger.error(f"  • {error}")

        if self.methods_fixed > 0:
            logger.info(f"\n✅ Successfully added self.ensure_one() to {self.methods_fixed} action methods")
        else:
            logger.info(f"\n✅ All action methods already have proper ensure_one() calls")

def main():
    """Main execution function"""
    fixer = ActionMethodFixer()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
