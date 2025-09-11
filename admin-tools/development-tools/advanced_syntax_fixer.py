#!/usr/bin/env python3
"""
Advanced Syntax Fixer for Records Management Module
Handles complex syntax errors including bracket mismatches, unterminated strings, etc.
"""

import os
import re
import ast

class AdvancedSyntaxFixer:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.fixes_applied = []
        self.files_fixed = 0
        
    def fix_bracket_mismatches(self, content):
        """Fix bracket and parenthesis mismatches"""
        fixes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Fix closing parenthesis ']' does not match opening parenthesis '('
            # Look for patterns like (...] and convert to (...)
            if ']' in line and '(' in line and '[' not in line:
                # Find opening parenthesis and ensure proper closing
                line = re.sub(r'\(\s*([^[\]()]*)\s*\]', r'(\1)', line)
                
            # Fix closing parenthesis ')' does not match opening parenthesis '['
            # Look for patterns like [...) and convert to [...]
            if ')' in line and '[' in line and '(' not in line:
                line = re.sub(r'\[\s*([^[\]()]*)\s*\)', r'[\1]', line)
                
            # Fix complex mismatches with multiple brackets
            if '(' in line and ']' in line and line.count('(') != line.count(')'):
                # Replace ] with ) if we have unmatched (
                open_count = line.count('(')
                close_paren_count = line.count(')')
                close_bracket_count = line.count(']')
                
                if open_count > close_paren_count and close_bracket_count > 0:
                    # Replace last ] with )
                    line = re.sub(r'\](?=[^]]*$)', ')', line)
            
            # Fix list definitions that end with ) instead of ]
            # Pattern: [..., ..., ...)
            line = re.sub(r'(\[[^\[\]]*),\s*\)', r'\1]', line)
            
            if line != original_line:
                lines[i] = line
                fixes.append(f"Fixed bracket mismatch at line {i+1}: {original_line.strip()[:50]}...")
        
        return '\n'.join(lines), fixes
    
    def fix_unterminated_strings(self, content):
        """Fix unterminated string literals"""
        fixes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            original_line = line
            
            # Fix unterminated single quotes in string assignments
            if 'string=' in line and line.count("'") % 2 != 0:
                if not line.strip().endswith("'"):
                    line = line + "'"
                    fixes.append(f"Added missing quote at line {i+1}")
            
            # Fix unterminated double quotes in string assignments
            if 'string=' in line and line.count('"') % 2 != 0:
                if not line.strip().endswith('"'):
                    line = line + '"'
                    fixes.append(f"Added missing quote at line {i+1}")
            
            # Fix specific unterminated triple quotes
            if '"""' in line:
                triple_count = line.count('"""')
                if triple_count == 1:
                    # Check if it's at the start or end
                    if line.strip().startswith('"""') and not line.strip().endswith('"""'):
                        line = line + '"""'
                        fixes.append(f"Completed triple quote at line {i+1}")
                    elif '"""' in line and not line.strip().startswith('"""'):
                        # Check if previous lines have opening triple quotes
                        if i > 0 and '"""' in lines[i-1]:
                            line = line + '"""'
                            fixes.append(f"Completed triple quote at line {i+1}")
            
            lines[i] = line
        
        return '\n'.join(lines), fixes
    
    def fix_function_definition_issues(self, content):
        """Fix function definition and closing issues"""
        fixes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Fix '(' was never closed - look for function definitions
            if 'def ' in line and '(' in line and line.count('(') > line.count(')'):
                # Add missing closing parenthesis before colon
                if ':' in line:
                    line = re.sub(r'([^:]+):(.*)$', r'\1):\2', line)
                else:
                    line = line + '):'
                fixes.append(f"Fixed unclosed function definition at line {i+1}")
                lines[i] = line
                
            # Fix field definitions with unclosed parentheses
            if 'fields.' in line and '(' in line and line.count('(') > line.count(')'):
                # Look ahead to see if the next line contains closing
                if i + 1 < len(lines) and ')' not in lines[i + 1]:
                    line = line + ')'
                    fixes.append(f"Fixed unclosed field definition at line {i+1}")
                    lines[i] = line
        
        return '\n'.join(lines), fixes
    
    def fix_comma_issues(self, content):
        """Fix missing commas and syntax issues"""
        fixes = []
        
        # Fix missing commas in field definitions with specific patterns
        patterns = [
            # Missing comma before tracking
            (r'(\))\s+(tracking=)', r'\1, \2'),
            # Missing comma before required
            (r'(\))\s+(required=)', r'\1, \2'),
            # Missing comma before string
            (r'(\))\s+(string=)', r'\1, \2'),
            # Missing comma before readonly
            (r'(\))\s+(readonly=)', r'\1, \2'),
            # Missing comma before help
            (r'(\))\s+(help=)', r'\1, \2'),
            # Missing comma before default
            (r'(\))\s+(default=)', r'\1, \2'),
            # Missing comma between field parameters
            (r'(True|False)\s+(string=)', r'\1, \2'),
            (r'(True|False)\s+(help=)', r'\1, \2'),
            (r'(True|False)\s+(tracking=)', r'\1, \2'),
            (r'(True|False)\s+(required=)', r'\1, \2'),
            (r'(True|False)\s+(readonly=)', r'\1, \2'),
        ]
        
        for pattern, replacement in patterns:
            old_content = content
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                fixes.append(f"Fixed missing comma: {pattern}")
        
        return content, fixes
    
    def fix_invalid_syntax_patterns(self, content):
        """Fix various invalid syntax patterns"""
        fixes = []
        
        # Fix selection field syntax errors
        content = re.sub(r'selection=\[\s*\(\s*([^,]+),\s*([^)]+)\s*\)', r'selection=[(\1, \2)]', content)
        
        # Fix domain syntax
        content = re.sub(r'domain=\[\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\s*\)', r'domain=[(\1, \2, \3)]', content)
        
        # Fix context syntax
        content = re.sub(r"context=\{\s*'([^']+)':\s*([^}]+)\s*\}", r"context={'\1': \2}", content)
        
        if content != content:
            fixes.append("Fixed various syntax patterns")
        
        return content, fixes
    
    def validate_and_fix_file(self, filepath):
        """Validate and fix a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            all_fixes = []
            
            # Apply fixes in order of complexity
            content, fixes = self.fix_comma_issues(content)
            all_fixes.extend(fixes)
            
            content, fixes = self.fix_bracket_mismatches(content)
            all_fixes.extend(fixes)
            
            content, fixes = self.fix_unterminated_strings(content)
            all_fixes.extend(fixes)
            
            content, fixes = self.fix_function_definition_issues(content)
            all_fixes.extend(fixes)
            
            content, fixes = self.fix_invalid_syntax_patterns(content)
            all_fixes.extend(fixes)
            
            # Try to validate syntax
            try:
                ast.parse(content)
                is_valid = True
                error = None
            except SyntaxError as e:
                is_valid = False
                error = str(e)
            
            if all_fixes:
                # Write the fixed content even if syntax is still invalid
                # This allows for iterative fixing
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.files_fixed += 1
                self.fixes_applied.extend([f"{os.path.basename(filepath)}: {fix}" for fix in all_fixes])
                
                if is_valid:
                    print(f"✅ Fixed {filepath}: {len(all_fixes)} fixes applied - SYNTAX VALID")
                else:
                    print(f"⚠️ Fixed {filepath}: {len(all_fixes)} fixes applied - Still invalid: {error}")
                return True
            else:
                if is_valid:
                    print(f"✅ {filepath}: Already valid")
                else:
                    print(f"❌ {filepath}: No fixes applied - Syntax error: {error}")
                return is_valid
                
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return False
    
    def fix_all_files(self):
        """Fix all Python files with errors"""
        # List of files that had errors from the previous scan
        error_files = [
            'bin_key_history.py', 'stock_lot_attribute_value.py', 'transitory_item.py',
            'field_label_customization.py', 'revenue_forecaster.py', 'naid_compliance_action_plan.py',
            'scan_retrieval_item.py', 'service_item.py', 'stock_lot_attribute.py',
            'document_retrieval_work_order.py', 'records_billing_line.py', 'shredding_certificate.py',
            'document_search_attempt.py', 'shredding_service_log.py', 'records_location.py',
            'shredding_team.py', 'paper_bale_recycling.py', 'portal_feedback_escalation.py',
            'approval_history.py', 'paper_load_shipment.py', 'fsm_task.py', 'visitor.py',
            'portal_request.py', 'shredding_service.py', 'work_order_shredding.py',
            'unlock_service_history.py', 'paper_bale_source_document.py', 'records_access_log.py',
            'document_retrieval_team.py', 'portal_feedback_action.py', 'records_billing_contact.py',
            'temp_inventory.py', 'records_survey_user_input.py', 'unlock_service_part.py',
            'visitor_pos_wizard.py', 'shred_bin.py', 'signed_document.py',
            'records_department_billing_contact.py', 'pickup_request.py', 'naid_certificate.py',
            'records_document_type.py', 'file_retrieval_work_order_item.py',
            'records_container_movement.py', 'transitory_field_config.py', 'records_department.py',
            'records_policy_version.py'
        ]
        
        print(f"🔧 Advanced Syntax Fixer - Processing {len(error_files)} files with errors...")
        
        for filename in error_files:
            filepath = os.path.join(self.models_dir, filename)
            if os.path.exists(filepath):
                self.validate_and_fix_file(filepath)
        
        print(f"\n📊 Summary:")
        print(f"   Files processed: {len(error_files)}")
        print(f"   Files modified: {self.files_fixed}")
        print(f"   Total fixes applied: {len(self.fixes_applied)}")
        
        if self.fixes_applied:
            print(f"\n🔧 Sample fixes applied:")
            for fix in self.fixes_applied[:10]:
                print(f"   - {fix}")
            if len(self.fixes_applied) > 10:
                print(f"   ... and {len(self.fixes_applied) - 10} more fixes")

def main():
    fixer = AdvancedSyntaxFixer()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
