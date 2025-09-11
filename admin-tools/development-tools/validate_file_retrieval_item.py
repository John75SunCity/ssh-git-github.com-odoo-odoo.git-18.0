#!/usr/bin/env python3
"""
File Retrieval Item Model Validation Script

This script validates the file.retrieval.item model structure and implementation
without requiring a full Odoo environment.
"""

import os
import sys
import ast
import re
from pathlib import Path

def validate_file_retrieval_item():
    """Validate the file.retrieval.item model implementation"""

    print("🔍 VALIDATING FILE RETRIEVAL ITEM MODEL")
    print("=" * 60)

    # Path to the model file
    model_file = Path("records_management/models/file_retrieval_item.py")

    if not model_file.exists():
        print(f"❌ Model file not found: {model_file}")
        return False

    print(f"✅ Found model file: {model_file}")

    # Read and parse the model file
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        print("✅ Python syntax is valid")

    except SyntaxError as e:
        print(f"❌ Syntax error in model file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading model file: {e}")
        return False

    # Analyze model structure
    analysis_results = analyze_model_structure(content, tree)

    # Print analysis results
    print_analysis_results(analysis_results)

    return True

def analyze_model_structure(content, tree):
    """Analyze the model structure and extract key information"""

    results = {
        'model_class_found': False,
        'model_name': None,
        'inherit_from': [],
        'fields': [],
        'methods': [],
        'compute_methods': [],
        'onchange_methods': [],
        'constraint_methods': [],
        'api_decorators': [],
        'imports': [],
        'estimated_pages_field': False,
        'required_fields': [],
        'selection_fields': [],
        'many2one_fields': [],
        'issues': [],
        'recommendations': []
    }

    # Extract imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                results['imports'].append(f"from {node.module} import {', '.join([alias.name for alias in node.names])}")
        elif isinstance(node, ast.Import):
            results['imports'].append(f"import {', '.join([alias.name for alias in node.names])}")

    # Find the main model class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if this is likely the main model class
            if any(base.id == 'Model' for base in node.bases if isinstance(base, ast.Name)):
                results['model_class_found'] = True

                # Extract model name and inheritance
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                if target.id == '_name' and isinstance(stmt.value, ast.Str):
                                    results['model_name'] = stmt.value.s
                                elif target.id == '_inherit' and isinstance(stmt.value, (ast.Str, ast.List)):
                                    if isinstance(stmt.value, ast.Str):
                                        results['inherit_from'].append(stmt.value.s)
                                    elif isinstance(stmt.value, ast.List):
                                        for elt in stmt.value.elts:
                                            if isinstance(elt, ast.Str):
                                                results['inherit_from'].append(elt.s)

                # Extract fields and methods
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                field_name = target.id
                                if isinstance(stmt.value, ast.Call):
                                    if isinstance(stmt.value.func, ast.Attribute):
                                        if stmt.value.func.attr in ['Char', 'Text', 'Integer', 'Float', 'Boolean',
                                                                   'Date', 'Datetime', 'Selection', 'Many2one',
                                                                   'One2many', 'Many2many', 'Binary', 'Html']:
                                            field_info = {
                                                'name': field_name,
                                                'type': stmt.value.func.attr,
                                                'required': False,
                                                'selection': None
                                            }

                                            # Check for field attributes
                                            for keyword in stmt.value.keywords:
                                                if keyword.arg == 'required' and isinstance(keyword.value, ast.Constant):
                                                    field_info['required'] = keyword.value.value
                                                elif keyword.arg == 'selection' and isinstance(keyword.value, ast.List):
                                                    field_info['selection'] = [
                                                        tuple(elt.elts[0].s if isinstance(elt.elts[0], ast.Str) else str(elt.elts[0].value),
                                                              elt.elts[1].s if isinstance(elt.elts[1], ast.Str) else str(elt.elts[1].value))
                                                        for elt in keyword.value.elts
                                                        if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2
                                                    ]

                                            results['fields'].append(field_info)

                                            # Track specific field types
                                            if field_name == 'estimated_pages':
                                                results['estimated_pages_field'] = True
                                            if field_info['required']:
                                                results['required_fields'].append(field_name)
                                            if field_info['type'] == 'Selection':
                                                results['selection_fields'].append(field_name)
                                            if field_info['type'] == 'Many2one':
                                                results['many2one_fields'].append(field_name)

                    elif isinstance(stmt, ast.FunctionDef):
                        method_name = stmt.name
                        results['methods'].append(method_name)

                        # Check for specific method types
                        for decorator in stmt.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                if decorator.attr == 'depends':
                                    results['compute_methods'].append(method_name)
                                    results['api_decorators'].append(f"@api.depends")
                                elif decorator.attr == 'onchange':
                                    results['onchange_methods'].append(method_name)
                                    results['api_decorators'].append(f"@api.onchange")
                                elif decorator.attr == 'constrains':
                                    results['constraint_methods'].append(method_name)
                                    results['api_decorators'].append(f"@api.constrains")

    # Check for common issues and provide recommendations
    check_model_issues(results)

    return results

def check_model_issues(results):
    """Check for common issues and provide recommendations"""

    # Check if estimated_pages field exists (required for our fix)
    if not results['estimated_pages_field']:
        results['issues'].append("Missing 'estimated_pages' field - required for compute method dependencies")
        results['recommendations'].append("Add: estimated_pages = fields.Integer(string='Estimated Pages', default=0)")

    # Check for required fields
    if not results['required_fields']:
        results['issues'].append("No required fields defined - consider adding validation")
        results['recommendations'].append("Add required=True to critical fields like 'name' or 'partner_id'")

    # Check for selection fields
    if len(results['selection_fields']) < 2:
        results['issues'].append("Few selection fields - consider adding status, priority, or type fields")
        results['recommendations'].append("Add Selection fields for better data categorization")

    # Check for compute methods
    if not results['compute_methods']:
        results['issues'].append("No compute methods found - consider adding calculated fields")
        results['recommendations'].append("Add @api.depends methods for dynamic field calculations")

    # Check for constraint methods
    if not results['constraint_methods']:
        results['issues'].append("No constraint methods found - consider adding validation")
        results['recommendations'].append("Add @api.constrains methods for data validation")

    # Check model inheritance
    if not results['inherit_from']:
        results['issues'].append("No inheritance detected - consider inheriting from mail mixins")
        results['recommendations'].append("Consider inheriting from ['mail.thread', 'mail.activity.mixin']")

def print_analysis_results(results):
    """Print the analysis results in a formatted way"""

    print("\n📊 MODEL ANALYSIS RESULTS")
    print("=" * 60)

    # Basic information
    print(f"🏷️  Model Name: {results['model_name'] or 'Not found'}")
    print(f"📦 Inherits From: {', '.join(results['inherit_from']) or 'None'}")
    print(f"🔧 Total Fields: {len(results['fields'])}")
    print(f"⚙️  Total Methods: {len(results['methods'])}")

    # Field breakdown
    print(f"\n📋 FIELD BREAKDOWN:")
    print(f"   - Required Fields: {len(results['required_fields'])} ({', '.join(results['required_fields'])})")
    print(f"   - Selection Fields: {len(results['selection_fields'])} ({', '.join(results['selection_fields'])})")
    print(f"   - Many2one Fields: {len(results['many2one_fields'])} ({', '.join(results['many2one_fields'])})")
    print(f"   - Estimated Pages Field: {'✅ Found' if results['estimated_pages_field'] else '❌ Missing'}")

    # Method breakdown
    print(f"\n🔧 METHOD BREAKDOWN:")
    print(f"   - Compute Methods: {len(results['compute_methods'])} ({', '.join(results['compute_methods'])})")
    print(f"   - Onchange Methods: {len(results['onchange_methods'])} ({', '.join(results['onchange_methods'])})")
    print(f"   - Constraint Methods: {len(results['constraint_methods'])} ({', '.join(results['constraint_methods'])})")

    # All fields list
    if results['fields']:
        print(f"\n📝 ALL FIELDS:")
        for field in results['fields']:
            required_str = " (required)" if field['required'] else ""
            selection_str = f" - choices: {len(field['selection'])}" if field['selection'] else ""
            print(f"   - {field['name']}: {field['type']}{required_str}{selection_str}")

    # Issues and recommendations
    if results['issues']:
        print(f"\n⚠️  ISSUES FOUND:")
        for issue in results['issues']:
            print(f"   - {issue}")

    if results['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for recommendation in results['recommendations']:
            print(f"   - {recommendation}")

    # Summary
    print(f"\n📈 SUMMARY:")
    if results['model_class_found']:
        print("✅ Model class structure is valid")
    else:
        print("❌ Model class structure issues detected")

    if results['estimated_pages_field']:
        print("✅ Critical 'estimated_pages' field is present")
    else:
        print("❌ Missing critical 'estimated_pages' field")

    issue_count = len(results['issues'])
    if issue_count == 0:
        print("✅ No major issues detected")
    else:
        print(f"⚠️  {issue_count} issues need attention")

def main():
    """Main execution function"""

    # Change to the correct directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    print("🚀 FILE RETRIEVAL ITEM MODEL VALIDATOR")
    print("=" * 60)
    print(f"📁 Working Directory: {os.getcwd()}")

    success = validate_file_retrieval_item()

    if success:
        print("\n🎉 Validation completed successfully!")
        return 0
    else:
        print("\n❌ Validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
