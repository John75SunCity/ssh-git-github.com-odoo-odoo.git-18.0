#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report XML Files Fixer

This script fixes common issues in Odoo report XML files:
1. Fixes report_name to match actual QWeb template id
2. Replaces generic "addon" module name with "records_management"
3. Updates generic "<h2>Title</h2>" with actual report names
4. Ensures field_ids is properly handled in templates
5. Adds missing field definitions and report content

Created: August 14, 2025
Author: GitHub Copilot for Records Management System
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


class ReportXMLFixer:
    """Fix report XML files with proper Odoo patterns"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.report_dir = self.base_path / "records_management" / "report"
        self.module_name = "records_management"
        self.fixes_applied = []
        self.errors_found = []
        
    def find_report_files(self):
        """Find all XML report files"""
        report_files = []
        
        if not self.report_dir.exists():
            print(f"❌ Report directory not found: {self.report_dir}")
            return report_files
            
        for xml_file in self.report_dir.glob("*.xml"):
            if xml_file.is_file() and xml_file.stat().st_size > 0:
                report_files.append(xml_file)
                
        print(f"🔍 Found {len(report_files)} report XML files")
        return report_files
    
    def extract_model_name_from_file(self, filepath):
        """Extract model name from file path and content"""
        filename = filepath.stem
        
        # Try to extract from filename patterns
        if filename.endswith('_report'):
            base_name = filename[:-7]  # Remove '_report'
        elif filename.endswith('_reports'):
            base_name = filename[:-8]  # Remove '_reports'
        else:
            base_name = filename
            
        # Convert underscores to dots for model name
        model_name = base_name.replace('_', '.')
        
        return model_name, base_name
    
    def generate_report_title(self, model_name, base_name):
        """Generate appropriate report title from model name"""
        # Convert model name to title case
        title_parts = []
        for part in base_name.split('_'):
            if part.upper() in ['NAID', 'FSM', 'API', 'URL', 'PDF', 'SMS']:
                title_parts.append(part.upper())
            else:
                title_parts.append(part.title())
        
        title = ' '.join(title_parts)
        
        # Add "Report" if not already present
        if 'Report' not in title:
            title += ' Report'
            
        return title
    
    def fix_report_xml_content(self, filepath):
        """Fix XML content in report file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                print(f"📝 File is empty, skipping: {filepath.name}")
                return False
                
            original_content = content
            model_name, base_name = self.extract_model_name_from_file(filepath)
            report_title = self.generate_report_title(model_name, base_name)
            
            fixes_in_file = []
            
            # Fix 1: Replace "addon" with proper module name
            if 'addon.' in content:
                content = content.replace('addon.', f'{self.module_name}.')
                fixes_in_file.append(f"Fixed module name: addon → {self.module_name}")
            
            # Fix 2: Fix report_name to match template id
            # Look for template id and report_name mismatches
            template_id_match = re.search(r'<template id="([^"]+)"', content)
            report_name_match = re.search(r'<field name="report_name">([^<]+)</field>', content)
            
            if template_id_match and report_name_match:
                template_id = template_id_match.group(1)
                current_report_name = report_name_match.group(1)
                expected_report_name = f"{self.module_name}.{template_id}"
                
                if current_report_name != expected_report_name:
                    content = content.replace(
                        f'<field name="report_name">{current_report_name}</field>',
                        f'<field name="report_name">{expected_report_name}</field>'
                    )
                    fixes_in_file.append(f"Fixed report_name: {current_report_name} → {expected_report_name}")
            
            # Fix 3: Replace generic <h2>Title</h2> with actual report name
            title_patterns = [
                r'<h2>Title</h2>',
                r'<h2>\s*Title\s*</h2>',
                r'<h1>Title</h1>',
                r'<h1>\s*Title\s*</h1>',
            ]
            
            for pattern in title_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, f'<h2>{report_title}</h2>', content)
                    fixes_in_file.append(f"Fixed title: Title → {report_title}")
                    break
            
            # Fix 4: Ensure proper field_ids handling
            # Check if template references field_ids but model doesn't have it
            if 'doc.field_ids' in content and 'field_ids' in content:
                # Add conditional check for field_ids
                field_pattern = r'(<t t-if="doc\.field_ids">.*?</t>)'
                if not re.search(field_pattern, content, re.DOTALL):
                    # Wrap existing field_ids usage with conditional
                    content = re.sub(
                        r'(<tr t-foreach="doc\.field_ids" t-as="field">.*?</tr>)',
                        r'<t t-if="doc.field_ids">\n                                \1\n                            </t>',
                        content,
                        flags=re.DOTALL
                    )
                    fixes_in_file.append("Added conditional check for field_ids")
            
            # Fix 5: Add proper model field references if missing
            if 'field.name' in content and 'field.description' not in content:
                # Add basic field template if missing
                field_template = '''                                        <td>
                                            <span t-esc="field.description or 'No description'"/>
                                        </td>'''
                
                # Look for name field and add description after it
                content = re.sub(
                    r'(<span t-esc="field\.name"/>.*?</td>)',
                    r'\1\n' + field_template,
                    content,
                    flags=re.DOTALL
                )
                fixes_in_file.append("Added description field to template")
            
            # Fix 6: Ensure proper print_report_name format
            if 'print_report_name' in content:
                # Standardize print_report_name format
                old_patterns = [
                    r'"&quot;%s&quot;" % \(object\.name,\)',
                    r"'%s' % object\.name",
                    r'&quot;%s&quot; % \(object\.name,\)',
                ]
                
                new_format = f'"({report_title}) %s" % (object.name or \'N/A\')'
                
                for pattern in old_patterns:
                    if re.search(pattern, content):
                        content = re.sub(pattern, new_format, content)
                        fixes_in_file.append("Standardized print_report_name format")
                        break
            
            # Fix 7: Add proper data context if template is too generic
            if '<tbody>' in content and 'doc.' not in content.split('<tbody>')[1].split('</tbody>')[0]:
                # Template has table but no actual data fields - add basic info
                basic_info = f'''                                <tr>
                                    <td><strong>Name:</strong></td>
                                    <td><span t-esc="doc.name or 'N/A'"/></td>
                                </tr>
                                <tr t-if="doc.create_date">
                                    <td><strong>Created:</strong></td>
                                    <td><span t-esc="doc.create_date.strftime('%Y-%m-%d %H:%M')" /></td>
                                </tr>
                                <tr t-if="doc.user_id">
                                    <td><strong>Created by:</strong></td>
                                    <td><span t-esc="doc.user_id.name"/></td>
                                </tr>'''
                
                # Add basic info to empty tbody
                content = re.sub(
                    r'(<tbody>\s*)(.*?)(\s*</tbody>)',
                    f'\\1{basic_info}\\3',
                    content,
                    flags=re.DOTALL
                )
                fixes_in_file.append("Added basic data fields to empty template")
            
            # Only write if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.extend([f"{filepath.name}: {fix}" for fix in fixes_in_file])
                print(f"✅ Fixed {filepath.name} ({len(fixes_in_file)} fixes)")
                return True
            else:
                print(f"⚪ No changes needed: {filepath.name}")
                return False
                
        except Exception as e:
            error_msg = f"❌ Error processing {filepath.name}: {str(e)}"
            self.errors_found.append(error_msg)
            print(error_msg)
            return False
    
    def create_missing_report_content(self, filepath):
        """Create content for empty report files"""
        model_name, base_name = self.extract_model_name_from_file(filepath)
        report_title = self.generate_report_title(model_name, base_name)
        
        # Generate template ID
        template_id = f"report_{base_name}_view"
        report_id = f"report_{base_name}"
        
        content = f'''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="{report_id}" model="ir.actions.report">
        <field name="name">{report_title}</field>
        <field name="model">{model_name}</field>
        <field name="report_type">qweb-html</field>
        <field name="report_name">{self.module_name}.{template_id}</field>
        <field name="report_file">{self.module_name}.{report_id}</field>
        <field name="print_report_name">"{report_title} - %s" % (object.name or 'N/A')</field>
        <field name="binding_model_id" ref="model_{base_name}"/>
        <field name="binding_type">report</field>
    </record>

    <template id="{template_id}">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc">
                <t t-call="web.external_layout">
                    <div class="page">
                        <h2>{report_title}</h2>
                        <div class="row mb-4">
                            <div class="col-6">
                                <strong>Name:</strong> <span t-esc="doc.name or 'N/A'"/>
                            </div>
                            <div class="col-6" t-if="doc.create_date">
                                <strong>Created:</strong> <span t-esc="doc.create_date.strftime('%Y-%m-%d %H:%M')"/>
                            </div>
                        </div>
                        
                        <table class="table table-condensed">
                            <thead>
                                <tr>
                                    <th>Field</th>
                                    <th>Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Name</strong></td>
                                    <td><span t-esc="doc.name or 'N/A'"/></td>
                                </tr>
                                <tr t-if="doc.create_date">
                                    <td><strong>Created</strong></td>
                                    <td><span t-esc="doc.create_date.strftime('%Y-%m-%d %H:%M')"/></td>
                                </tr>
                                <tr t-if="doc.user_id">
                                    <td><strong>Created by</strong></td>
                                    <td><span t-esc="doc.user_id.name"/></td>
                                </tr>
                                <tr t-if="doc.company_id">
                                    <td><strong>Company</strong></td>
                                    <td><span t-esc="doc.company_id.name"/></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </t>
            </t>
        </t>
    </template>
</odoo>
'''
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created content for empty file: {filepath.name}")
            self.fixes_applied.append(f"{filepath.name}: Created complete report content")
            return True
        except Exception as e:
            error_msg = f"❌ Error creating content for {filepath.name}: {str(e)}"
            self.errors_found.append(error_msg)
            print(error_msg)
            return False
    
    def fix_all_reports(self):
        """Fix all report XML files"""
        print("🚀 Starting Report XML Files Fix Process...")
        print("="*60)
        
        report_files = self.find_report_files()
        
        if not report_files:
            print("❌ No report files found to process")
            return
        
        fixed_count = 0
        empty_files_fixed = 0
        
        for filepath in report_files:
            print(f"\n📄 Processing: {filepath.name}")
            
            # Check if file is empty
            if filepath.stat().st_size == 0:
                if self.create_missing_report_content(filepath):
                    empty_files_fixed += 1
                    fixed_count += 1
                continue
            
            # Fix existing content
            if self.fix_report_xml_content(filepath):
                fixed_count += 1
        
        # Print summary
        print("\n" + "="*60)
        print("📊 REPORT XML FIXES SUMMARY")
        print("="*60)
        print(f"📁 Total files processed: {len(report_files)}")
        print(f"✅ Files fixed: {fixed_count}")
        print(f"📝 Empty files with content added: {empty_files_fixed}")
        print(f"❌ Errors encountered: {len(self.errors_found)}")
        
        if self.fixes_applied:
            print(f"\n🔧 {len(self.fixes_applied)} FIXES APPLIED:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"   {i:2d}. {fix}")
        
        if self.errors_found:
            print(f"\n⚠️  {len(self.errors_found)} ERRORS FOUND:")
            for i, error in enumerate(self.errors_found, 1):
                print(f"   {i:2d}. {error}")
        
        print(f"\n🎯 SUCCESS RATE: {((len(report_files) - len(self.errors_found)) / len(report_files) * 100):.1f}%")
        print("✅ Report XML fixes complete!")


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    
    print("🔧 REPORT XML FILES FIXER")
    print("="*60)
    print(f"📁 Base path: {base_path}")
    print(f"🎯 Target: records_management/report/*.xml")
    print("🔍 Issues to fix:")
    print("   1. Fix report_name to match QWeb template id")
    print("   2. Replace 'addon' with 'records_management'")
    print("   3. Update generic titles with proper names")
    print("   4. Ensure field_ids is properly handled")
    print("   5. Add missing report content")
    print("   6. Standardize print_report_name format")
    print()
    
    fixer = ReportXMLFixer(base_path)
    fixer.fix_all_reports()


if __name__ == "__main__":
    main()
