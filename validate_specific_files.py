#!/usr/bin/env python3
"""
Validate specific view files from manifest selection
"""

from comprehensive_action_validator import ComprehensiveActionValidator
import os

def main():
    # Files from the user's selection
    files_to_validate = [
        "records_management/views/records_security_audit_views.xml",
        "records_management/views/records_series_views.xml",
        "records_management/views/records_service_type_views.xml",
        "records_management/views/records_storage_department_user_views.xml",
        "records_management/views/records_survey_user_input_views.xml",
        "records_management/views/records_tag_category_views.xml",
        "records_management/views/records_tag_views.xml",
        "records_management/views/records_usage_tracking_views.xml",
        "records_management/views/reference_views.xml",
        "records_management/views/revenue_analytic_views.xml",
        "records_management/views/revenue_forecast_line_views.xml",
        "records_management/views/revenue_forecast_views.xml",
        "records_management/views/revenue_forecaster_views.xml",
        "records_management/views/rm_module_configurator_views.xml",
        "records_management/views/service_item_views.xml",
        "records_management/views/shred_model_bin_views.xml",
        "records_management/views/shredding_certificate_views.xml",
        "records_management/views/shredding_hard_drive_views.xml",
        "records_management/views/shredding_inventory_batch_views.xml",
        "records_management/views/shredding_service_bin_views.xml",
        "records_management/views/shredding_service_event_views.xml",
        "records_management/views/shredding_service_photo_views.xml",
        "records_management/views/shredding_service_views.xml",
        "records_management/views/shredding_team_views.xml",
        "records_management/views/stock_lot_views.xml",
        "records_management/views/survey_feedback_theme_views.xml",
        "records_management/views/survey_improvement_action_views.xml",
        "records_management/views/temp_inventory_views.xml",
        "records_management/views/work_order_coordinator_views.xml",
        "records_management/views/workflow_visualization_manager_views.xml",
        "records_management/views/records_container_views.xml",
        "records_management/views/records_container_field_label_helper_views.xml",
        "records_management/views/records_billing_config_views.xml",
        "records_management/views/portal_request_views.xml",
    ]
    
    validator = ComprehensiveActionValidator()
    
    print("🔍 VALIDATING SPECIFIC VIEW FILES FROM MANIFEST")
    print("=" * 60)
    
    validated_files = 0
    total_issues = 0
    file_issues = {}
    
    for file_path in files_to_validate:
        if os.path.exists(file_path):
            print(f"📄 Validating: {file_path}")
            initial_issues = len(validator.issues_found)
            
            try:
                validator.validate_xml_file(file_path)
                file_specific_issues = len(validator.issues_found) - initial_issues
                
                if file_specific_issues > 0:
                    file_issues[file_path] = file_specific_issues
                    print(f"   ⚠️  Found {file_specific_issues} issues")
                else:
                    print(f"   ✅ No issues found")
                    
                validated_files += 1
                
            except Exception as e:
                print(f"   ❌ Error validating: {e}")
        else:
            print(f"📄 ⚠️  File not found: {file_path}")
    
    total_issues = len(validator.issues_found)
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"📁 Files validated: {validated_files}/{len(files_to_validate)}")
    print(f"🐛 Total issues found: {total_issues}")
    
    if file_issues:
        print(f"\n🔥 FILES WITH ISSUES:")
        for file_path, issue_count in file_issues.items():
            short_name = file_path.split('/')[-1]
            print(f"   📄 {short_name}: {issue_count} issues")
    
    if validator.issues_found:
        print(f"\n📋 DETAILED ISSUES:")
        
        # Group issues by type
        by_type = {}
        for issue in validator.issues_found:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        for issue_type, issues in by_type.items():
            print(f"\n❌ {issue_type.replace('_', ' ').title()}: {len(issues)}")
            for i, issue in enumerate(issues[:5]):  # Show first 5 of each type
                file_name = issue.get('file', 'unknown')
                if '/' in file_name:
                    file_name = file_name.split('/')[-1]
                
                print(f"   {i+1}. 📄 {file_name}")
                if 'field' in issue:
                    print(f"      🔧 Field: {issue['field']}")
                if 'model' in issue:
                    print(f"      📊 Model: {issue['model']}")
                if 'message' in issue:
                    print(f"      💡 {issue['message']}")
                elif 'reason' in issue:
                    print(f"      💡 {issue['reason']}")
                if 'alternative' in issue:
                    print(f"      🔧 Fix: {issue['alternative']}")
                if 'suggestion' in issue:
                    print(f"      💭 {issue['suggestion']}")
                print()
            
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more {issue_type} issues")
    
    if total_issues == 0:
        print("🎉 All specified files passed validation!")
    else:
        print(f"\n⚠️  Found {total_issues} issues that should be addressed")
    
    print("\n✅ Specific file validation complete!")

if __name__ == "__main__":
    main()
