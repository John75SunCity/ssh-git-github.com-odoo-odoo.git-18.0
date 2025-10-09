#!/usr/bin/env python3
"""
Safe Odoo 19 Constraint Conversion Script
Converts deprecated models.Constraint to _sql_constraints format
"""

import os
import re
import ast
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def is_valid_python_syntax(content):
    """Check if Python code has valid syntax"""
    try:
        ast.parse(content)
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error: {e}")
        return False

def backup_file(filepath):
    """Create backup of file before modification"""
    backup_path = filepath + '.backup'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path

def convert_constraints_in_file(filepath):
    """
    Convert models.Constraint to _sql_constraints in a single file
    Returns: (success, modified, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Skip if no constraints found
        if 'models.Constraint' not in original_content:
            return True, False, None
            
        logger.info(f"Processing: {filepath}")
        
        # Create backup
        backup_path = backup_file(filepath)
        
        # Convert constraints line by line for safety
        lines = original_content.split('\n')
        modified_lines = []
        inside_constraint = False
        constraint_lines = []
        constraint_indent = 0
        
        for i, line in enumerate(lines):
            # Check for start of models.Constraint
            constraint_match = re.match(r'(\s*)models\.Constraint\(\s*$', line)
            if constraint_match:
                inside_constraint = True
                constraint_indent = len(constraint_match.group(1))
                constraint_lines = [line]
                continue
            
            # If inside constraint, collect lines until we find the closing
            if inside_constraint:
                constraint_lines.append(line)
                
                # Check for closing parenthesis at same indent level
                if line.strip() == '),' or line.strip() == ')':
                    # Process the complete constraint
                    constraint_text = '\n'.join(constraint_lines)
                    
                    # Extract constraint details using regex
                    sql_pattern = r"sql\s*=\s*['\"]([^'\"]+)['\"]"
                    message_pattern = r"message\s*=\s*['\"]([^'\"]+)['\"]"
                    
                    sql_match = re.search(sql_pattern, constraint_text)
                    message_match = re.search(message_pattern, constraint_text)
                    
                    if sql_match and message_match:
                        sql_constraint = sql_match.group(1)
                        message = message_match.group(1)
                        
                        # Generate constraint name from SQL
                        constraint_name = re.sub(r'[^a-z0-9_]', '_', sql_constraint.lower())
                        constraint_name = re.sub(r'_+', '_', constraint_name)[:50]
                        if not constraint_name.startswith('_'):
                            constraint_name = '_' + constraint_name
                        
                        # Create _sql_constraints entry
                        sql_constraints_line = f"{' ' * constraint_indent}('{constraint_name}', '{sql_constraint}', _('{message}')),"
                        
                        # Check if _sql_constraints already exists
                        has_sql_constraints = any('_sql_constraints' in l for l in modified_lines)
                        
                        if has_sql_constraints:
                            # Find and append to existing _sql_constraints
                            for j in range(len(modified_lines) - 1, -1, -1):
                                if '_sql_constraints = [' in modified_lines[j]:
                                    # Find the closing bracket
                                    for k in range(j + 1, len(modified_lines)):
                                        if modified_lines[k].strip() == ']':
                                            modified_lines.insert(k, sql_constraints_line)
                                            break
                                    break
                        else:
                            # Add new _sql_constraints
                            modified_lines.append(f"{' ' * constraint_indent}_sql_constraints = [")
                            modified_lines.append(sql_constraints_line)
                            modified_lines.append(f"{' ' * constraint_indent}]")
                    else:
                        logger.warning(f"Could not parse constraint in {filepath}")
                        # Keep original constraint if parsing fails
                        modified_lines.extend(constraint_lines)
                    
                    inside_constraint = False
                    constraint_lines = []
                    continue
            
            # Normal line processing
            if not inside_constraint:
                modified_lines.append(line)
        
        # Join modified content
        modified_content = '\n'.join(modified_lines)
        
        # Validate syntax before writing
        if not is_valid_python_syntax(modified_content):
            logger.error(f"Generated invalid syntax for {filepath}, keeping original")
            return False, False, "Invalid syntax generated"
        
        # Write modified content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logger.info(f"✅ Successfully converted constraints in {filepath}")
        return True, True, None
        
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")
        return False, False, str(e)

def main():
    """Main function to process all model files"""
    models_dir = 'records_management/models'
    
    if not os.path.exists(models_dir):
        logger.error(f"Models directory not found: {models_dir}")
        return
    
    total_files = 0
    modified_files = 0
    error_files = 0
    
    logger.info("Starting safe constraint conversion...")
    
    # Process all Python files
    for filename in sorted(os.listdir(models_dir)):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            total_files += 1
            
            success, modified, error = convert_constraints_in_file(filepath)
            
            if success:
                if modified:
                    modified_files += 1
            else:
                error_files += 1
                logger.error(f"Failed to process {filepath}: {error}")
    
    logger.info(f"\n=== CONVERSION SUMMARY ===")
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Files modified: {modified_files}")
    logger.info(f"Files with errors: {error_files}")
    
    if error_files == 0:
        logger.info("✅ All files processed successfully!")
        
        # Run syntax check
        logger.info("Running final syntax validation...")
        os.system("find records_management/models -name '*.py' -exec python3 -m py_compile {} \\; 2>&1 | head -5")
    else:
        logger.error("❌ Some files had errors. Check logs above.")

if __name__ == '__main__':
    main()
