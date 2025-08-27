#!/usr/bin/env python3
"""
Records Management - Models and Views Analysis
Generate a comprehensive report of all models and their corresponding view files,
ordered from smallest to largest model files.
"""

import os
import re
import subprocess
from pathlib import Path

def get_model_data():
    """Extract model information from Python files"""
    models_data = []
    models_dir = Path("records_management/models")

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            # Get line count
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())

            # Extract model name
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            model_name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            model_name = model_name_match.group(1) if model_name_match else "N/A"

            # Extract model description
            desc_match = re.search(r"_description\s*=\s*['\"]([^'\"]+)['\"]", content)
            description = desc_match.group(1) if desc_match else "No description"

            models_data.append({
                'filename': py_file.name,
                'model_name': model_name,
                'description': description,
                'lines': lines,
                'size_kb': py_file.stat().st_size / 1024
            })

        except Exception as e:
            print(f"Error processing {py_file}: {e}")
            continue

    return sorted(models_data, key=lambda x: x['lines'])

def get_view_files():
    """Get all view files and their corresponding models"""
    views_data = {}
    views_dir = Path("records_management/views")

    for xml_file in views_dir.glob("*views.xml"):
        # Extract potential model name from filename
        base_name = xml_file.stem.replace('_views', '')
        potential_model = base_name.replace('_', '.')

        try:
            # Look for actual model references in the XML
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all model references
            model_refs = re.findall(r'<field name="model">([^<]+)</field>', content)
            model_refs.extend(re.findall(r'<field name="res_model">([^<]+)</field>', content))

            # Get unique model references
            actual_models = list(set(model_refs))

            views_data[xml_file.name] = {
                'filename': xml_file.name,
                'potential_model': potential_model,
                'actual_models': actual_models,
                'lines': len(open(xml_file, 'r').readlines()),
                'size_kb': xml_file.stat().st_size / 1024
            }

        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            continue

    return views_data

def match_models_to_views(models_data, views_data):
    """Match models to their corresponding view files"""
    matched_data = []

    for model in models_data:
        model_name = model['model_name']
        matched_views = []

        # Find matching view files
        for view_file, view_info in views_data.items():
            if (model_name in view_info['actual_models'] or
                model_name == view_info['potential_model']):
                matched_views.append({
                    'filename': view_file,
                    'lines': view_info['lines'],
                    'size_kb': view_info['size_kb']
                })

        matched_data.append({
            **model,
            'view_files': matched_views,
            'view_count': len(matched_views)
        })

    return matched_data

def generate_report(matched_data):
    """Generate a comprehensive report"""
    print("=" * 100)
    print("📊 RECORDS MANAGEMENT - MODELS AND VIEWS ANALYSIS")
    print("=" * 100)
    print()

    # Summary statistics
    total_models = len(matched_data)
    total_model_lines = sum(m['lines'] for m in matched_data)
    total_view_files = sum(m['view_count'] for m in matched_data)
    total_view_lines = sum(sum(v['lines'] for v in m['view_files']) for m in matched_data)

    print(f"📈 SUMMARY STATISTICS:")
    print(f"  • Total Models: {total_models}")
    print(f"  • Total Model Lines: {total_model_lines:,}")
    print(f"  • Total View Files: {total_view_files}")
    print(f"  • Total View Lines: {total_view_lines:,}")
    print(f"  • Average Model Size: {total_model_lines / total_models:.1f} lines")
    print()

    # Size categories
    small_models = [m for m in matched_data if m['lines'] <= 50]
    medium_models = [m for m in matched_data if 50 < m['lines'] <= 200]
    large_models = [m for m in matched_data if m['lines'] > 200]

    print(f"📊 SIZE DISTRIBUTION:")
    print(f"  • Small Models (≤50 lines): {len(small_models)} ({len(small_models)/total_models*100:.1f}%)")
    print(f"  • Medium Models (51-200 lines): {len(medium_models)} ({len(medium_models)/total_models*100:.1f}%)")
    print(f"  • Large Models (>200 lines): {len(large_models)} ({len(large_models)/total_models*100:.1f}%)")
    print()

    # Detailed listing
    print("=" * 100)
    print("📋 DETAILED MODEL LISTING (Ordered by Size - Smallest to Largest)")
    print("=" * 100)

    for i, model in enumerate(matched_data, 1):
        size_indicator = "🟢" if model['lines'] <= 50 else "🟡" if model['lines'] <= 200 else "🔴"

        print(f"\n{i:3d}. {size_indicator} {model['model_name']}")
        print(f"     📁 File: {model['filename']}")
        print(f"     📏 Size: {model['lines']} lines ({model['size_kb']:.1f} KB)")
        print(f"     📝 Description: {model['description']}")
        print(f"     🎨 View Files ({model['view_count']}):")

        if model['view_files']:
            for view in sorted(model['view_files'], key=lambda x: x['lines']):
                print(f"         • {view['filename']} ({view['lines']} lines, {view['size_kb']:.1f} KB)")
        else:
            print(f"         ❌ No matching view files found")

        if i % 10 == 0:  # Add separator every 10 models
            print("     " + "-" * 80)

    print("\n" + "=" * 100)
    print("🏆 TOP 10 LARGEST MODELS:")
    print("=" * 100)

    largest_models = sorted(matched_data, key=lambda x: x['lines'], reverse=True)[:10]
    for i, model in enumerate(largest_models, 1):
        print(f"{i:2d}. {model['model_name']:<40} {model['lines']:>4} lines  {model['view_count']:>2} views")

    print("\n" + "=" * 100)
    print("🥇 MODELS WITH MOST VIEW FILES:")
    print("=" * 100)

    most_views = sorted(matched_data, key=lambda x: x['view_count'], reverse=True)[:10]
    for i, model in enumerate(most_views, 1):
        if model['view_count'] > 0:
            print(f"{i:2d}. {model['model_name']:<40} {model['view_count']:>2} view files")

    print("\n" + "=" * 100)
    print("⚠️  MODELS WITHOUT VIEW FILES:")
    print("=" * 100)

    no_views = [m for m in matched_data if m['view_count'] == 0]
    if no_views:
        for model in no_views:
            print(f"   • {model['model_name']} ({model['filename']})")
    else:
        print("   🎉 All models have corresponding view files!")

if __name__ == "__main__":
    # Change to the workspace root
    os.chdir("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")

    print("🔍 Analyzing models and views...")
    models_data = get_model_data()
    views_data = get_view_files()
    matched_data = match_models_to_views(models_data, views_data)

    generate_report(matched_data)

    print(f"\n✅ Analysis complete! Found {len(models_data)} models and {len(views_data)} view files.")
