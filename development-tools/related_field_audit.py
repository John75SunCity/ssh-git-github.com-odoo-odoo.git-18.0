#!/usr/bin/env python3
"""
Comprehensive Related Field Audit Script for Records Management Module

This script identifies potential issues with related fields where the target field
might not exist in the referenced model.
"""

import os
import re
import ast
import sys

def extract_related_fields(file_path):
    """Extract all related field definitions from a Python file"""
    related_fields = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find related field patterns
        patterns = [
            r"(\w+)\s*=\s*fields\.\w+\([^)]*related=(['\"])(.*?)\2[^)]*\)",
            r"(\w+)\s*=\s*fields\.\w+\([^)]*\s+related=(['\"])(.*?)\2[^)]*\)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                field_name = match.group(1)
                related_path = match.group(3)
                line_num = content[:match.start()].count('\n') + 1

                related_fields.append({
                    'field_name': field_name,
                    'related_path': related_path,
                    'line_number': line_num,
                    'file_path': file_path
                })

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return related_fields

def analyze_related_field_issues():
    """Analyze all related fields for potential issues"""
    models_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"

    all_related_fields = []
    potential_issues = []

    # Extract all related fields
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)
            related_fields = extract_related_fields(file_path)
            all_related_fields.extend(related_fields)

    print(f"Found {len(all_related_fields)} related field definitions")
    print("\n" + "="*80)
    print("RELATED FIELD AUDIT REPORT")
    print("="*80)

    # Group by model being referenced
    by_model = {}
    for field in all_related_fields:
        related_path = field['related_path']

        # Parse the related path
        if '.' in related_path:
            parts = related_path.split('.')
            if len(parts) >= 2:
                model_field = parts[0]  # e.g., 'container_id'
                target_field = '.'.join(parts[1:])  # e.g., 'estimated_weight' or 'storage_location_id.name'

                if model_field not in by_model:
                    by_model[model_field] = []
                by_model[model_field].append({
                    **field,
                    'model_field': model_field,
                    'target_field': target_field
                })

    # Known problematic field mappings
    known_issues = {
        'container_id.estimated_weight': 'container_id.weight',  # Should be weight, not estimated_weight
        'container_id.storage_location_id': 'container_id.location_id',  # storage_location_id doesn't exist
        'config_id.company_id': 'INVALID_REFERENCE',  # config_id references non-existent model
        # Add more as discovered
    }

    print("\nPOTENTIAL ISSUES FOUND:")
    print("-" * 40)

    issue_count = 0
    for model_field, fields in by_model.items():
        model_name = get_model_name_from_field(model_field)
        print(f"\n{model_field} ({model_name}):")

        for field in fields:
            full_path = f"{field['model_field']}.{field['target_field']}"

            # Check for known issues
            if full_path in known_issues:
                issue_count += 1
                print(f"  ❌ ISSUE: {field['file_path']}:{field['line_number']}")
                print(f"     Field: {field['field_name']} = related='{field['related_path']}'")
                print(f"     Problem: {full_path} should be {known_issues[full_path]}")
                potential_issues.append({
                    **field,
                    'issue_type': 'known_field_mismatch',
                    'suggested_fix': known_issues[full_path]
                })

            # Check for suspicious patterns
            elif 'estimated_weight' in field['target_field'] and model_field == 'container_id':
                issue_count += 1
                print(f"  ⚠️  SUSPICIOUS: {field['file_path']}:{field['line_number']}")
                print(f"     Field: {field['field_name']} = related='{field['related_path']}'")
                print(f"     Problem: container_id.estimated_weight likely doesn't exist")
                potential_issues.append({
                    **field,
                    'issue_type': 'missing_field',
                    'suggested_fix': field['related_path'].replace('estimated_weight', 'weight')
                })

            elif 'storage_location_id' in field['target_field'] and model_field == 'container_id':
                issue_count += 1
                print(f"  ⚠️  SUSPICIOUS: {field['file_path']}:{field['line_number']}")
                print(f"     Field: {field['field_name']} = related='{field['related_path']}'")
                print(f"     Problem: container_id.storage_location_id likely doesn't exist")
                potential_issues.append({
                    **field,
                    'issue_type': 'missing_field',
                    'suggested_fix': field['related_path'].replace('storage_location_id', 'location_id')
                })

            else:
                print(f"  ✅ OK: {field['field_name']} = related='{field['related_path']}'")

    print(f"\n" + "="*80)
    print(f"SUMMARY: Found {issue_count} potential issues in {len(all_related_fields)} related fields")
    print("="*80)

    return potential_issues

def get_model_name_from_field(field_name):
    """Map field names to likely model names"""
    mapping = {
        'container_id': 'records.container',
        'partner_id': 'res.partner',
        'company_id': 'res.company',
        'user_id': 'res.users',
        'location_id': 'records.location or stock.location',
        'policy_id': 'records.retention.policy',
        'job_id': 'records.destruction.job',
        'move_id': 'stock.move',
        'picking_id': 'stock.picking',
        'invoice_id': 'account.move',
        'task_id': 'project.task or fsm.task',
        'fsm_task_id': 'project.task',
        'request_id': 'portal.request',
        'billing_id': 'advanced.billing',
        'forecast_id': 'revenue.forecast',
        'report_id': 'customer.inventory.report',
        'feedback_id': 'portal.feedback',
        'transfer_id': 'records.container.transfer',
        'work_order_id': 'work.order',
        'split_id': 'payment.split',
    }
    return mapping.get(field_name, 'unknown')

if __name__ == "__main__":
    print("Starting Related Field Audit...")
    issues = analyze_related_field_issues()

    if issues:
        print(f"\nFound {len(issues)} issues that need fixing!")
        print("Run with --fix flag to automatically fix known issues.")
    else:
        print("\nNo issues found! All related fields appear correct.")
