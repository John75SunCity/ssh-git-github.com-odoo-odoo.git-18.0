#!/usr/bin/env python3
"""
Fix Mail Thread Field Conflicts
Removes conflicting field definitions that should be provided by mail.thread and mail.activity.mixin
"""

import os
import re
import glob

def fix_mail_thread_conflicts():
    """Remove conflicting mail.thread field definitions from all model files"""
    
    # Pattern to match problematic field definitions
    patterns_to_remove = [
        # Activity fields
        r'\s*activity_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        
        # Message follower fields  
        r'\s*message_follower_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        
        # Message fields
        r'\s*message_ids\s*=\s*fields\.One2many\([^)]*compute[^)]*\)[^#]*(?:#.*)?$',
        
        # Related compute methods that should not exist for mail.thread models
        r'\s*@api\.depends\(\)\s*\n\s*def\s+_compute_activity_ids\(self\):.*?(?=\n\s*@|\n\s*def|\n\s*class|\nclass|\Z)',
        r'\s*@api\.depends\(\)\s*\n\s*def\s+_compute_message_followers?\(self\):.*?(?=\n\s*@|\n\s*def|\n\s*class|\nclass|\Z)',
        r'\s*@api\.depends\(\)\s*\n\s*def\s+_compute_message_ids\(self\):.*?(?=\n\s*@|\n\s*def|\n\s*class|\nclass|\Z)',
    ]
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    
    # Get all Python files in models directory
    model_files = glob.glob(os.path.join(models_dir, "*.py"))
    
    total_fixes = 0
    
    for file_path in model_files:
        if os.path.basename(file_path) == "__init__.py":
            continue
            
        print(f"Checking {os.path.basename(file_path)}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has mail.thread inheritance
            if ('_inherit = [' in content and 'mail.thread' in content) or ('_inherit = ' in content and 'mail.thread' in content):
                original_content = content
                
                # Apply each pattern
                for pattern in patterns_to_remove:
                    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
                
                # Clean up extra blank lines
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                # Only write if changes were made
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    fixes_made = len(original_content) - len(content)
                    total_fixes += 1
                    print(f"  ✅ Fixed {os.path.basename(file_path)} (removed {fixes_made} characters)")
                else:
                    print(f"  ⚪ No conflicts found in {os.path.basename(file_path)}")
            else:
                print(f"  ⏭️ Skipping {os.path.basename(file_path)} (no mail.thread inheritance)")
                
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
    
    print(f"\n🎯 Fixed {total_fixes} files with mail.thread conflicts")
    print("\n🔧 These fields are now provided automatically by mail.thread and mail.activity.mixin:")
    print("   - activity_ids")
    print("   - message_follower_ids") 
    print("   - message_ids")
    print("\n⚠️  Note: This should resolve the KeyError: 'res_id' issue during module installation")

if __name__ == "__main__":
    fix_mail_thread_conflicts()
