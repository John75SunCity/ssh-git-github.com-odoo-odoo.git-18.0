#!/usr/bin/env python3
"""
Fix Mail Thread Field Duplication Issue

This script removes redundant mail.thread field definitions from models that
inherit from ['mail.thread', 'mail.activity.mixin'] since these fields are
automatically provided by the framework.

Removes:
- activity_ids = fields.One2many("mail.activity", ...)
- message_follower_ids = fields.One2many("mail.followers", ...)
- message_ids = fields.One2many("mail.message", ...)
- Any associated compute methods with @api.depends("id")
"""

import os
import re
import glob


def fix_mail_thread_fields():
    """Fix all models with redundant mail.thread field definitions"""

    model_files = glob.glob("records_management/models/*.py")
    fixed_files = []

    for file_path in model_files:
        if file_path.endswith("__init__.py"):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Check if model inherits from mail.thread
            if (
                '_inherit = ["mail.thread"' not in content
                and "_inherit = ['mail.thread'" not in content
            ):
                continue

            # Remove redundant field definitions
            patterns_to_remove = [
                # Activity fields
                r'\s*activity_ids\s*=\s*fields\.One2many\([^)]*"mail\.activity"[^)]*\)[^,]*,?\s*\n',
                # Message follower fields
                r'\s*message_follower_ids\s*=\s*fields\.One2many\([^)]*"mail\.followers"[^)]*\)[^,]*,?\s*\n',
                # Message fields
                r'\s*message_ids\s*=\s*fields\.One2many\([^)]*"mail\.message"[^)]*\)[^,]*,?\s*\n',
            ]

            # Remove field definitions
            for pattern in patterns_to_remove:
                content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)

            # Remove compute methods that depend on 'id'
            compute_pattern = r'(\s*)@api\.depends\("id"\)\s*\n\s*def\s+_compute_(?:activity_ids|message_follower_ids|message_ids)\(self\):.*?(?=\n\s*(?:@|def|#\s*=|class|\Z))'
            content = re.sub(
                compute_pattern,
                r"\1# Mail framework fields provided by mail.thread inheritance\n",
                content,
                flags=re.MULTILINE | re.DOTALL,
            )

            # Clean up extra newlines
            content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(file_path)
                print(f"✅ Fixed: {file_path}")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    print(f"\n🎯 Summary: Fixed {len(fixed_files)} files")
    for file_path in fixed_files:
        print(f"   - {file_path}")

    return fixed_files


if __name__ == "__main__":
    print("🔧 Fixing Mail Thread Field Duplication Issues...")
    fix_mail_thread_fields()
    print("✅ Mail Thread field cleanup complete!")
