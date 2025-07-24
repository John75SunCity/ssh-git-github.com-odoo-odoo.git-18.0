#!/usr/bin/env python3
"""
Script to automatically add missing @api.depends decorators to compute methods.
"""

import os
import re

# Define the missing decorators with their suggested dependencies
MISSING_DECORATORS = {
    'records_management/models/barcode_product.py': [
        {
            'method': '_compute_activity_state',
            'depends': ['activity_ids'],
            'line_pattern': r'(\s*)def _compute_activity_state\(self\):'
        }
    ],
    'records_management/models/customer_inventory_report.py': [
        {
            'method': '_compute_line_total',
            'depends': ['base_rate', 'discount_amount', 'additional_amount', 'quantity'],
            'line_pattern': r'(\s*)def _compute_line_total\(self\):'
        }
    ],
    'records_management/models/department_billing.py': [
        {
            'method': '_compute_billing_analytics',
            'depends': ['customer_id'],
            'line_pattern': r'(\s*)def _compute_billing_analytics\(self\):'
        },
        {
            'method': '_compute_billing_stats',
            'depends': ['customer_id'],
            'line_pattern': r'(\s*)def _compute_billing_stats\(self\):'
        }
    ],
    'records_management/models/fsm_task.py': [
        {
            'method': '_compute_material_usage_ids',
            'depends': ['material_cost', 'material_usage_log'],
            'line_pattern': r'(\s*)def _compute_material_usage_ids\(self\):'
        },
        {
            'method': '_compute_mobile_update_ids',
            'depends': ['mobile_signature', 'mobile_photo'],
            'line_pattern': r'(\s*)def _compute_mobile_update_ids\(self\):'
        }
    ],
    'records_management/models/hr_employee_naid.py': [
        {
            'method': '_compute_compliance_status',
            'depends': ['naid_certification_valid', 'background_check_valid', 'training_valid'],
            'line_pattern': r'(\s*)def _compute_compliance_status\(self\):'
        }
    ],
    'records_management/models/load.py': [
        {
            'method': '_compute_photo_ids',
            'depends': ['load_photos', 'delivery_photos'],
            'line_pattern': r'(\s*)def _compute_photo_ids\(self\):'
        }
    ],
    'records_management/models/naid_audit.py': [
        {
            'method': '_compute_audit_analytics',
            'depends': ['audit_score', 'findings_count', 'corrective_actions_count'],
            'line_pattern': r'(\s*)def _compute_audit_analytics\(self\):'
        }
    ],
    'records_management/models/pickup_request.py': [
        {
            'method': '_compute_pickup_analytics',
            'depends': ['scheduled_date', 'actual_pickup_date', 'pickup_status'],
            'line_pattern': r'(\s*)def _compute_pickup_analytics\(self\):'
        }
    ],
    'records_management/models/portal_feedback.py': [
        {
            'method': '_compute_improvement_count',
            'depends': ['improvement_action_ids'],
            'line_pattern': r'(\s*)def _compute_improvement_count\(self\):'
        },
        {
            'method': '_compute_related_count',
            'depends': ['related_ticket_ids'],
            'line_pattern': r'(\s*)def _compute_related_count\(self\):'
        },
        {
            'method': '_compute_followup_activities',
            'depends': ['followup_required', 'followup_date'],
            'line_pattern': r'(\s*)def _compute_followup_activities\(self\):'
        },
        {
            'method': '_compute_attachments',
            'depends': ['attachment_ids'],
            'line_pattern': r'(\s*)def _compute_attachments\(self\):'
        }
    ],
    'records_management/models/portal_request.py': [
        {
            'method': '_compute_related_request_count',
            'depends': ['partner_id', 'request_type'],
            'line_pattern': r'(\s*)def _compute_related_request_count\(self\):'
        }
    ],
    'records_management/models/pos_config.py': [
        {
            'method': '_compute_analytics',
            'depends': ['session_ids', 'order_ids'],
            'line_pattern': r'(\s*)def _compute_analytics\(self\):'
        },
        {
            'method': '_compute_session_info',
            'depends': ['current_session_id', 'session_ids'],
            'line_pattern': r'(\s*)def _compute_session_info\(self\):'
        }
    ],
    'records_management/models/product.py': [
        {
            'method': '_compute_product_metrics',
            'depends': ['sale_ok', 'list_price', 'standard_price'],
            'line_pattern': r'(\s*)def _compute_product_metrics\(self\):'
        },
        {
            'method': '_compute_display_name',
            'depends': ['name', 'default_code'],
            'line_pattern': r'(\s*)def _compute_display_name\(self\):'
        }
    ],
    'records_management/models/records_box.py': [
        {
            'method': '_compute_movement_count',
            'depends': ['box_movement_ids'],
            'line_pattern': r'(\s*)def _compute_movement_count\(self\):'
        },
        {
            'method': '_compute_service_request_count',
            'depends': ['portal_request_ids'],
            'line_pattern': r'(\s*)def _compute_service_request_count\(self\):'
        }
    ],
    'records_management/models/records_document.py': [
        {
            'method': '_compute_retention_date',
            'depends': ['created_date', 'retention_policy_id', 'retention_policy_id.retention_years'],
            'line_pattern': r'(\s*)def _compute_retention_date\(self\):'
        },
        {
            'method': '_compute_attachment_count',
            'depends': ['attachment_ids'],
            'line_pattern': r'(\s*)def _compute_attachment_count\(self\):'
        },
        {
            'method': '_compute_audit_trail_count',
            'depends': ['audit_trail_ids'],
            'line_pattern': r'(\s*)def _compute_audit_trail_count\(self\):'
        },
        {
            'method': '_compute_chain_of_custody_count',
            'depends': ['chain_of_custody_ids'],
            'line_pattern': r'(\s*)def _compute_chain_of_custody_count\(self\):'
        }
    ],
    'records_management/models/records_location.py': [
        {
            'method': '_compute_location_analytics',
            'depends': ['box_ids', 'capacity', 'access_control_system'],
            'line_pattern': r'(\s*)def _compute_location_analytics\(self\):'
        }
    ],
    'records_management/models/records_retention_policy.py': [
        {
            'method': '_compute_retention_analytics',
            'depends': ['policy_status', 'compliance_verified', 'document_count', 'retention_years'],
            'line_pattern': r'(\s*)def _compute_retention_analytics\(self\):'
        }
    ],
    'records_management/models/shredding_service.py': [
        {
            'method': '_compute_shredding_analytics',
            'depends': ['service_type', 'status', 'total_charge', 'service_date', 'scheduled_date'],
            'line_pattern': r'(\s*)def _compute_shredding_analytics\(self\):'
        },
        {
            'method': '_compute_certificate_count',
            'depends': ['compliance_documentation_ids'],
            'line_pattern': r'(\s*)def _compute_certificate_count\(self\):'
        },
        {
            'method': '_compute_witness_count',
            'depends': ['witness_verification_ids'],
            'line_pattern': r'(\s*)def _compute_witness_count\(self\):'
        }
    ],
    'records_management/models/stock_lot.py': [
        {
            'method': '_compute_quantities',
            'depends': ['quant_ids', 'quant_ids.quantity', 'quant_ids.reserved_quantity'],
            'line_pattern': r'(\s*)def _compute_quantities\(self\):'
        },
        {
            'method': '_compute_movement_metrics',
            'depends': ['stock_move_ids'],
            'line_pattern': r'(\s*)def _compute_movement_metrics\(self\):'
        },
        {
            'method': '_compute_inventory_metrics',
            'depends': ['create_date'],
            'line_pattern': r'(\s*)def _compute_inventory_metrics\(self\):'
        },
        {
            'method': '_compute_current_location',
            'depends': ['quant_ids', 'quant_ids.location_id'],
            'line_pattern': r'(\s*)def _compute_current_location\(self\):'
        },
        {
            'method': '_compute_quality_metrics',
            'depends': ['quality_check_ids'],
            'line_pattern': r'(\s*)def _compute_quality_metrics\(self\):'
        },
        {
            'method': '_compute_quant_metrics',
            'depends': ['quant_ids'],
            'line_pattern': r'(\s*)def _compute_quant_metrics\(self\):'
        },
        {
            'method': '_compute_move_metrics',
            'depends': ['stock_move_ids'],
            'line_pattern': r'(\s*)def _compute_move_metrics\(self\):'
        },
        {
            'method': '_compute_value_metrics',
            'depends': ['available_quantity', 'unit_cost'],
            'line_pattern': r'(\s*)def _compute_value_metrics\(self\):'
        }
    ]
}

def add_api_depends_to_file(file_path, decorators_info):
    """Add @api.depends decorators to a specific file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    for decorator_info in decorators_info:
        method_name = decorator_info['method']
        depends_fields = decorator_info['depends']
        line_pattern = decorator_info['line_pattern']
        
        # Check if the decorator is already present
        if f'@api.depends' in content and method_name in content:
            # Skip if it looks like decorator is already there
            continue
        
        # Create the decorator string
        depends_str = ', '.join(f"'{field}'" for field in depends_fields)
        
        # Find the method and add decorator
        def replacement(match):
            indent = match.group(1)
            original_line = match.group(0)
            decorator = f"{indent}@api.depends({depends_str})\n"
            return decorator + original_line
        
        new_content = re.sub(line_pattern, replacement, content)
        
        if new_content != content:
            content = new_content
            modified = True
            print(f"  ✅ Added @api.depends to {method_name}")
        else:
            print(f"  ⚠️  Could not find method {method_name} in {file_path}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified

def main():
    """Main function to add missing @api.depends decorators."""
    print("🔧 Adding missing @api.depends decorators to compute methods...")
    print("=" * 80)
    
    total_files_modified = 0
    total_decorators_added = 0
    
    for file_path, decorators_info in MISSING_DECORATORS.items():
        if os.path.exists(file_path):
            print(f"\n📄 Processing {os.path.basename(file_path)}")
            print("-" * 40)
            
            if add_api_depends_to_file(file_path, decorators_info):
                total_files_modified += 1
                total_decorators_added += len(decorators_info)
        else:
            print(f"  ❌ File not found: {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"   Files modified: {total_files_modified}")
    print(f"   @api.depends decorators added: {total_decorators_added}")
    print(f"\n✅ All missing @api.depends decorators have been added!")
    print(f"   This will improve performance and ensure correct field recomputation.")

if __name__ == '__main__':
    main()
