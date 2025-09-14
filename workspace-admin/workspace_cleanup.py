#!/usr/bin/env python3
"""
Workspace Cleanup Script - Organize all scripts and backups into appropriate folders
"""

import os
import shutil
from pathlib import Path

def cleanup_workspace():
    """Clean up workspace by organizing files into appropriate directories"""

    workspace_root = Path(".")
    moved_files = []
    created_dirs = []

    print("🧹 WORKSPACE CLEANUP - ORGANIZING FILES")
    print("=" * 50)

    # Define target directories and ensure they exist
    directories_to_create = [
        "development-tools/cleanup-scripts",
        "development-tools/mass-fix-tools",
        "development-tools/analysis-reports",
        "development-tools/validation-tools",
        "backup/model-backups",
        "backup/script-backups",
        "backup/reports-archive",
        "workspace-admin/summaries"
    ]

    for dir_path in directories_to_create:
        full_path = workspace_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"📁 Created directory: {dir_path}")

    # Define file organization rules
    file_moves = [
        # Mass fix and repair tools
        {
            "files": [
                "analyze_mass_fix_damage.py",
                "restore_working_files.py",
                "surgical_mass_fix_repair.py",
                "restore_corrupted_files.py"
            ],
            "target": "development-tools/mass-fix-tools",
            "description": "Mass fix analysis and repair tools"
        },

        # Cleanup and validation scripts
        {
            "files": [
                "clean_html.py",
                "clean_remaining_emojis.py",
                "final_emoji_cleanup.py",
                "remove_html_entities.py",
                "field_validator.py"
            ],
            "target": "development-tools/cleanup-scripts",
            "description": "Data cleanup and validation scripts"
        },

        # Fix scripts
        {
            "files": [
                "fix_all_data_wrappers.py",
                "fix_data_wrappers.py",
                "fix_emojis.py",
                "fix_missing_quotes.py",
                "fix_quotes.py",
                "fix_syntax_errors.py",
                "fix_xml_comprehensive.py",
                "fix_xml_indentation.py"
            ],
            "target": "development-tools/validation-tools",
            "description": "Automated fix and validation tools"
        },

        # Reports and logs
        {
            "files": [
                "auto_fix_results.log",
                "mass_validation_report_no_autofixes.txt",
                "mass_view_validation_report.txt",
                "temp_validation_output.txt"
            ],
            "target": "backup/reports-archive",
            "description": "Validation reports and logs"
        },

        # Summary documents
        {
            "files": [
                "MASS_VALIDATION_SUMMARY.md",
                "MENU_FIX_SUMMARY.md",
                "PICKUP_ROUTE_FIX_SUMMARY.md",
                "WORKSPACE_ORGANIZATION_SUMMARY.md"
            ],
            "target": "workspace-admin/summaries",
            "description": "Project summaries and documentation"
        }
    ]

    # Execute file moves
    for move_group in file_moves:
        print(f"\n📦 Moving {move_group['description']}...")
        target_dir = workspace_root / move_group['target']

        for filename in move_group['files']:
            source_file = workspace_root / filename
            target_file = target_dir / filename

            if source_file.exists():
                try:
                    shutil.move(str(source_file), str(target_file))
                    moved_files.append(f"{filename} → {move_group['target']}")
                    print(f"  ✅ Moved: {filename}")
                except Exception as e:
                    print(f"  ❌ Error moving {filename}: {e}")
            else:
                print(f"  ⚠️  Not found: {filename}")

    # Move current cleanup script to appropriate location
    cleanup_script = workspace_root / "workspace_cleanup.py"
    if cleanup_script.exists():
        target_cleanup = workspace_root / "workspace-admin" / "workspace_cleanup.py"
        try:
            shutil.move(str(cleanup_script), str(target_cleanup))
            moved_files.append("workspace_cleanup.py → workspace-admin")
            print(f"\n🔧 Moved cleanup script to workspace-admin")
        except Exception as e:
            print(f"❌ Error moving cleanup script: {e}")

    # Clean up broken backup files in views directory
    views_dir = workspace_root / "records_management" / "views"
    broken_backups = list(views_dir.glob("*.broken_backup"))

    if broken_backups:
        print(f"\n🗂️  Moving {len(broken_backups)} broken backup files...")
        broken_backup_dir = workspace_root / "backup" / "broken-views-backup"
        broken_backup_dir.mkdir(exist_ok=True)

        for backup_file in broken_backups:
            try:
                target_backup = broken_backup_dir / backup_file.name
                shutil.move(str(backup_file), str(target_backup))
                print(f"  ✅ Moved: {backup_file.name}")
            except Exception as e:
                print(f"  ❌ Error moving {backup_file.name}: {e}")

    print(f"\n📊 CLEANUP SUMMARY")
    print("=" * 50)
    print(f"Directories created: {len(created_dirs)}")
    print(f"Files moved: {len(moved_files)}")
    print(f"Broken backups relocated: {len(broken_backups)}")

    if moved_files:
        print(f"\n📁 Files organized:")
        for move in moved_files:
            print(f"  • {move}")

    print(f"\n🎯 WORKSPACE NOW ORGANIZED:")
    print("  📁 development-tools/")
    print("    ├── cleanup-scripts/     (data cleanup tools)")
    print("    ├── mass-fix-tools/      (mass fix analysis & repair)")
    print("    ├── validation-tools/    (automated fixes)")
    print("    └── analysis-reports/    (existing analysis tools)")
    print("  📁 backup/")
    print("    ├── broken-views-backup/ (corrupted files from mass fix)")
    print("    ├── reports-archive/     (validation logs)")
    print("    └── views_backup_20250913/ (working file backups)")
    print("  📁 workspace-admin/")
    print("    └── summaries/           (project documentation)")

    return len(moved_files), len(created_dirs)

if __name__ == "__main__":
    try:
        files_moved, dirs_created = cleanup_workspace()
        print(f"\n✅ Workspace cleanup completed successfully!")
        print(f"Organized {files_moved} files into {dirs_created} new directories.")
        print(f"\n🎉 Your workspace is now clean and organized!")
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
