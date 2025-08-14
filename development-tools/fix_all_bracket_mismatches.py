#!/usr/bin/env python3
"""
Fix All Bracket Mismatches in Files
Systematically fixes { followed by ) patterns
"""

import os
import re

def fix_write_bracket_mismatches(content):
    """Fix write() method bracket mismatches specifically"""
    # Pattern: write( followed by { ... followed by )
    # Should be: write( followed by { ... followed by }
    
    # Find all write() calls with mismatched brackets
    pattern = r'(\.write\s*\(\s*)\{([^{}]*?)\}(\s*\))'
    
    # First pass: fix any } followed by ) patterns
    content = re.sub(pattern, r'\1{\2}\3', content)
    
    # Second pass: find { ... ) patterns and fix them
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for write() with opening {
        if 'write(' in line and '{' in line:
            # Look ahead to find the closing bracket
            brace_count = line.count('{') - line.count('}')
            j = i + 1
            
            # Find the matching closing
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                brace_count += next_line.count('{') - next_line.count('}')
                
                # If we find a ) where we expect a }
                if brace_count == 1 and next_line.strip() == ')':
                    lines[j] = next_line.replace(')', '}')
                elif brace_count == 1 and next_line.strip() == '))':
                    lines[j] = next_line.replace('))', '})')
                
                j += 1
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_bracket_mismatches(filepath):
    """Fix bracket mismatches in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix write() bracket mismatches
        content = fix_write_bracket_mismatches(content)
        
        # General bracket fixes
        # Fix any remaining ) where } is expected after {
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Look for lines with ) that should be }
            if line.strip() in [')', '))']:
                # Check previous lines for unmatched {
                brace_count = 0
                for j in range(i-1, max(i-10, -1), -1):  # Look back up to 10 lines
                    prev_line = lines[j]
                    brace_count += prev_line.count('{') - prev_line.count('}')
                    
                    if brace_count > 0:
                        # We have unmatched {, so change ) to }
                        if line.strip() == ')':
                            line = line.replace(')', '}')
                        elif line.strip() == '))':
                            line = line.replace('))', '})')
                        break
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed bracket mismatches"
        
        return False, "No bracket mismatches found"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function to fix all files with bracket mismatch errors"""
    # Files with known bracket mismatch errors
    error_files = [
        'document_retrieval_item.py',
        'portal_feedback_analytic.py',
        'naid_compliance_action_plan.py', 
        'naid_compliance_support_models.py',
        'barcode_product.py',
        'naid_risk_assessment.py',
        'base_rate.py',
        'records_location.py',
        'product_container_type.py',
        'records_customer_billing_profile.py',
        'approval_history.py',
        'naid_compliance_alert.py',
        'records_access_log.py',
        'portal_feedback.py',
        'records_billing_contact.py',
        'file_retrieval_work_order_item.py',
        'records_billing_profile.py'
    ]
    
    print("🔧 Fixing bracket mismatches in specific files...\n")
    
    fixed_count = 0
    
    for filename in error_files:
        filepath = f'records_management/models/{filename}'
        if os.path.exists(filepath):
            print(f"🔧 Processing {filename}...")
            success, message = fix_file_bracket_mismatches(filepath)
            if success:
                print(f"   ✅ {message}")
                fixed_count += 1
                
                # Test syntax after fixing
                try:
                    import py_compile
                    py_compile.compile(filepath, doraise=True)
                    print(f"   ✅ Syntax is now valid")
                except Exception as e:
                    print(f"   ⚠️  Still has syntax errors: {e}")
            else:
                print(f"   ⏭️  {message}")
        else:
            print(f"   ❌ File not found: {filename}")
    
    print(f"\n📊 Summary: Attempted to fix {len(error_files)} files, {fixed_count} were modified")

if __name__ == '__main__':
    main()
