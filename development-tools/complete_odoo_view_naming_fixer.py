#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Odoo View Naming Convention Fixer

Applies the correct Odoo naming conventions to ALL view files:
1. View IDs: <model_name>_view_<view_type> (e.g., base_rate_view_tree)
2. View names: <model.name>.view.<type> (e.g., base.rate.view.tree)
3. View modes: tree instead of list
4. Comments: standardized format

Based on the manual edits seen in base_rate_views.xml
"""

import os
import re
import glob
from pathlib import Path

def fix_all_view_naming_conventions():
    """Fix ALL view files to follow proper Odoo naming conventions"""
    
    views_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views"
    
    fixed_files = []
    errors = []
    
    # Get all XML files in views directory
    xml_files = glob.glob(os.path.join(views_dir, "*.xml"))
    
    print(f"🔍 Processing {len(xml_files)} XML view files...")
    print("=" * 60)
    
    for xml_file in xml_files:
        filename = os.path.basename(xml_file)
        print(f"\n📄 Processing: {filename}")
        
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply all fixes
            content = fix_view_ids_and_names(content, filename)
            content = fix_view_modes(content)
            content = fix_comments(content)
            content = fix_xml_entities(content)
            
            # Only write if changes were made
            if content != original_content:
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(filename)
                print(f"✅ Fixed: {filename}")
            else:
                print(f"⏭️  Already correct: {filename}")
                
        except Exception as e:
            error_msg = f"❌ Error processing {filename}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    print("\n" + "=" * 60)
    print(f"🎉 SUMMARY: Fixed {len(fixed_files)} files")
    
    if fixed_files:
        print(f"\n✅ Successfully fixed files:")
        for file in sorted(fixed_files):
            print(f"  • {file}")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors:
            print(f"  • {error}")
    
    return fixed_files, errors

def fix_view_ids_and_names(content, filename):
    """Fix view IDs and names to follow proper Odoo conventions"""
    
    # Extract model name from filename (e.g., base_rate_views.xml -> base_rate)
    model_name_from_file = filename.replace('_views.xml', '').replace('-', '_')
    
    def fix_record_id_and_name(match):
        full_match = match.group(0)
        current_id = match.group(1) if match.group(1) else ""
        current_name = match.group(2) if match.group(2) else ""
        model = match.group(3)
        
        # Convert model name to use underscores for ID
        model_underscore = model.replace('.', '_').replace('-', '_')
        
        # Determine view type from current ID or name
        view_type = 'tree'
        if 'form' in current_id.lower() or 'form' in current_name.lower():
            view_type = 'form'
        elif 'search' in current_id.lower() or 'search' in current_name.lower():
            view_type = 'search'
        elif 'kanban' in current_id.lower() or 'kanban' in current_name.lower():
            view_type = 'kanban'
        elif 'calendar' in current_id.lower() or 'calendar' in current_name.lower():
            view_type = 'calendar'
        elif 'pivot' in current_id.lower() or 'pivot' in current_name.lower():
            view_type = 'pivot'
        elif 'graph' in current_id.lower() or 'graph' in current_name.lower():
            view_type = 'graph'
        elif 'list' in current_id.lower() or 'list' in current_name.lower() or 'tree' in current_id.lower():
            view_type = 'tree'
        
        # Generate correct ID and name
        correct_id = f"{model_underscore}_view_{view_type}"
        correct_name = f"{model}.view.{view_type}"
        
        # Replace in the match
        new_match = full_match
        if current_id:
            new_match = new_match.replace(f'id="{current_id}"', f'id="{correct_id}"')
        if current_name:
            new_match = new_match.replace(f'<field name="name">{current_name}</field>', f'<field name="name">{correct_name}</field>')
        
        return new_match
    
    # Pattern to match record definitions with ID and name
    pattern = r'<record id="([^"]*)" model="ir\.ui\.view">\s*<field name="name">([^<]*)</field>\s*<field name="model">([^<]*)</field>'
    content = re.sub(pattern, fix_record_id_and_name, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def fix_view_modes(content):
    """Fix view modes: list -> tree"""
    
    # Fix in action definitions
    content = re.sub(
        r'<field name="view_mode">[^<]*list[^<]*</field>',
        lambda m: m.group(0).replace('list', 'tree'),
        content
    )
    
    # Fix XML tags: <list> -> <tree>
    content = re.sub(r'<list([^>]*)>', r'<tree\1>', content)
    content = re.sub(r'</list>', r'</tree>', content)
    
    return content

def fix_comments(content):
    """Standardize comments to follow proper format"""
    
    def replace_comment(match):
        comment = match.group(1).strip()
        
        # Extract view type and model from comment
        view_type = 'tree'
        if 'form' in comment.lower():
            view_type = 'form'
        elif 'search' in comment.lower():
            view_type = 'search'
        elif 'kanban' in comment.lower():
            view_type = 'kanban'
        elif 'list' in comment.lower() or 'tree' in comment.lower():
            view_type = 'tree'
        
        # Extract model name
        model_match = re.search(r'(\w+(?:\.\w+)*)', comment)
        if model_match:
            model = model_match.group(1)
            return f"    <!-- {view_type.title()} view for {model} -->"
        
        return match.group(0)
    
    content = re.sub(r'    <!--\s*([^>]+)\s*-->', replace_comment, content)
    
    return content

def fix_xml_entities(content):
    """Fix XML entities: & -> &amp;"""
    
    # Fix unescaped ampersands in attribute values
    content = re.sub(r'="([^"]*?)&([^"]*?)"', r'="\1&amp;\2"', content)
    
    return content

if __name__ == "__main__":
    print("🚀 Starting Complete Odoo View Naming Convention Fix...")
    print("Following the pattern established in base_rate_views.xml")
    print("=" * 60)
    
    fixed_files, errors = fix_all_view_naming_conventions()
    
    print("\n" + "=" * 60)
    print("🎯 PROCESS COMPLETE!")
    
    if fixed_files:
        print(f"\n📋 Applied Odoo naming conventions:")
        print("  ✅ View IDs: <model_name>_view_<view_type>")
        print("  ✅ View names: <model.name>.view.<type>")
        print("  ✅ View modes: tree instead of list")
        print("  ✅ Comments: standardized format")
        print("  ✅ XML entities: properly escaped")
        print(f"\n🚀 Ready to commit {len(fixed_files)} fixed files!")
    else:
        print("✨ All files already follow proper Odoo naming conventions!")
    
    if errors:
        print(f"\n⚠️  {len(errors)} files had processing errors - please review manually")
