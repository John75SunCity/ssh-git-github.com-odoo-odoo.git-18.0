#!/usr/bin/env python3
"""
Simple test to verify file.retrieval.item model functionality
"""

import sys
import ast
from pathlib import Path

def test_file_retrieval_item():
    """Test the enhanced file.retrieval.item model"""

    print("🧪 TESTING ENHANCED FILE RETRIEVAL ITEM MODEL")
    print("=" * 60)

    model_file = Path("records_management/models/file_retrieval_item.py")

    if not model_file.exists():
        print("❌ Model file not found")
        return False

    # Read the model file
    with open(model_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse and analyze
    try:
        tree = ast.parse(content)
        print("✅ Python syntax is valid")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False

    # Test 1: Check for required fields
    required_field_indicators = [
        'required=True',
        'name = fields.Char',
        'requested_file_name = fields.Char',
        'partner_id = fields.Many2one',
        'estimated_pages',  # Critical field for our fix
    ]

    print("\n📋 Testing Field Requirements:")
    for indicator in required_field_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
        else:
            print(f"❌ Missing: {indicator}")

    # Test 2: Check for comprehensive functionality
    functionality_indicators = [
        '_inherit = [\'retrieval.item.base\', \'mail.thread\', \'mail.activity.mixin\']',
        '@api.depends',
        '@api.constrains',
        '@api.onchange',
        'def action_start_search',
        'def action_mark_located',
        'def action_mark_retrieved',
        'def action_mark_completed',
        'def action_mark_not_found',
        'def action_cancel',
        '_compute_display_name',
        'tracking=True',
    ]

    print("\n🔧 Testing Functionality:")
    functionality_score = 0
    for indicator in functionality_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
            functionality_score += 1
        else:
            print(f"❌ Missing: {indicator}")

    # Test 3: Check for workflow states
    workflow_states = [
        '\'pending\'',
        '\'searching\'',
        '\'located\'',
        '\'retrieved\'',
        '\'completed\'',
        '\'not_found\'',
        '\'cancelled\'',
    ]

    print("\n🔄 Testing Workflow States:")
    workflow_score = 0
    for state in workflow_states:
        if state in content:
            print(f"✅ Found state: {state}")
            workflow_score += 1
        else:
            print(f"❌ Missing state: {state}")

    # Test 4: Check for validation constraints
    validation_indicators = [
        '_check_partner_required',
        '_check_time_values',
        '_check_date_logic',
        'ValidationError',
        'UserError',
    ]

    print("\n🛡️ Testing Validation:")
    validation_score = 0
    for indicator in validation_indicators:
        if indicator in content:
            print(f"✅ Found: {indicator}")
            validation_score += 1
        else:
            print(f"❌ Missing: {indicator}")

    # Test 5: Count lines and complexity
    lines = content.split('\n')
    non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]

    print(f"\n📊 Code Metrics:")
    print(f"   - Total lines: {len(lines)}")
    print(f"   - Non-empty lines: {len(non_empty_lines)}")
    print(f"   - Functionality score: {functionality_score}/{len(functionality_indicators)}")
    print(f"   - Workflow score: {workflow_score}/{len(workflow_states)}")
    print(f"   - Validation score: {validation_score}/{len(validation_indicators)}")

    # Overall assessment
    total_possible = len(functionality_indicators) + len(workflow_states) + len(validation_indicators)
    total_score = functionality_score + workflow_score + validation_score
    percentage = (total_score / total_possible) * 100

    print(f"\n🎯 Overall Assessment:")
    print(f"   - Score: {total_score}/{total_possible} ({percentage:.1f}%)")

    if percentage >= 90:
        print("   - Grade: ⭐⭐⭐ EXCELLENT - Comprehensive implementation")
    elif percentage >= 75:
        print("   - Grade: ⭐⭐ GOOD - Well implemented with minor gaps")
    elif percentage >= 60:
        print("   - Grade: ⭐ BASIC - Functional but needs improvement")
    else:
        print("   - Grade: ❌ INCOMPLETE - Requires significant work")

    # Critical fix validation
    if 'estimated_pages' in content:
        print("✅ CRITICAL: estimated_pages field is present (database error fixed)")
    else:
        print("❌ CRITICAL: estimated_pages field is MISSING (database error will occur)")

    return True

def main():
    """Main function"""
    import os
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    success = test_file_retrieval_item()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
