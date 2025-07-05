#!/usr/bin/env python3
import os
import glob
from pathlib import Path

def count_lines_in_file(file_path):
    """Count lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def analyze_module(module_path):
    """Analyze the records_management module"""
    if not os.path.exists(module_path):
        print(f"Module path not found: {module_path}")
        return

    print("🔍 RECORDS MANAGEMENT MODULE - CODE ANALYSIS")
    print("=" * 60)
    
    # File extensions to analyze
    extensions = {
        '*.py': '🐍 Python',
        '*.xml': '📄 XML',
        '*.csv': '📋 CSV',
        '*.js': '💻 JavaScript',
        '*.scss': '🎨 SCSS',
        '*.css': '🎨 CSS',
        '*.md': '📖 Markdown'
    }
    
    total_files = 0
    total_lines = 0
    file_stats = {}
    
    for pattern, description in extensions.items():
        files = list(Path(module_path).rglob(pattern))
        if files:
            file_count = len(files)
            line_count = sum(count_lines_in_file(f) for f in files)
            file_stats[description] = {
                'files': file_count,
                'lines': line_count,
                'files_list': files
            }
            total_files += file_count
            total_lines += line_count
    
    # Print summary
    print(f"📁 TOTAL FILES: {total_files}")
    print(f"📏 TOTAL LINES: {total_lines:,}")
    print()
    
    # Print by file type
    print("📊 BREAKDOWN BY FILE TYPE:")
    print("-" * 40)
    for description, stats in file_stats.items():
        print(f"{description}: {stats['files']} files, {stats['lines']:,} lines")
    
    print()
    print("📂 DETAILED FILE BREAKDOWN:")
    print("-" * 60)
    
    # Show individual files
    for description, stats in file_stats.items():
        if stats['files'] > 0:
            print(f"\n{description} FILES:")
            for file_path in sorted(stats['files_list']):
                lines = count_lines_in_file(file_path)
                relative_path = os.path.relpath(file_path, module_path)
                print(f"  📄 {relative_path}: {lines:,} lines")
    
    # Find largest files
    print("\n🏆 TOP 10 LARGEST FILES:")
    print("-" * 40)
    all_files = []
    for stats in file_stats.values():
        for file_path in stats['files_list']:
            lines = count_lines_in_file(file_path)
            relative_path = os.path.relpath(file_path, module_path)
            all_files.append((relative_path, lines))
    
    # Sort by line count and show top 10
    all_files.sort(key=lambda x: x[1], reverse=True)
    for i, (file_path, lines) in enumerate(all_files[:10], 1):
        print(f"  {i:2d}. {file_path}: {lines:,} lines")

if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/records_management"
    analyze_module(module_path)
