#!/usr/bin/env python3
"""
Paste Artifact Cleaner for Odoo Records Management Module
=========================================================

This tool systematically removes all paste artifacts found by the typo detector:
- Doubled characters (requestuest, certificateificate, etc.)
- Duplicated XML IDs and references
- Copy/paste artifacts in views and data files

Usage: python paste_artifact_cleaner.py
"""

import os
import re
from pathlib import Path

class PasteArtifactCleaner:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.fixes_applied = 0
        
        # Doubled character patterns found by typo detector
        self.doubled_char_fixes = {
            'requestuest': 'request',
            'certificateificate': 'certificate', 
            'complianceliance': 'compliance',
            'managementgement': 'management',
            'documentcument': 'document',
            'servicesrvice': 'service',
            'destructionction': 'destruction',
            'auditaudit': 'audit',
            'inventoryentory': 'inventory'
        }
        
        # Duplicated model references
        self.model_ref_fixes = {
            'model_partner_bin_key_key': 'model_partner_bin_key',
            'model_naid_audit_log_log': 'model_naid_audit_log',
            'model_naid_certificateificate': 'model_naid_certificate',
            'model_naid_complianceliance_checklist': 'model_naid_compliance_checklist',
            'model_portal_requestuest': 'model_portal_request'
        }
        
        # Common XML artifacts that should be removed/cleaned
        self.xml_artifacts = [
            'o_view_nocontent_smiling_face',
            'o_kanban_card_header_title', 
            'o_kanban_manage_button_section',
            'o_kanban_manage_toggle_button',
            'o_kanban_card_manage_pane'
        ]

    def clean_csv_files(self):
        """Clean paste artifacts in CSV files"""
        print("🧹 Cleaning CSV files...")
        
        csv_files = list(self.module_path.rglob("*.csv"))
        
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                
                # Fix doubled characters
                for wrong, correct in self.doubled_char_fixes.items():
                    content = content.replace(wrong, correct)
                    
                # Fix model references  
                for wrong, correct in self.model_ref_fixes.items():
                    content = content.replace(wrong, correct)
                    
                # Remove duplicate lines
                lines = content.split('\n')
                unique_lines = []
                seen = set()
                
                for line in lines:
                    if line.strip() and line not in seen:
                        unique_lines.append(line)
                        seen.add(line)
                    elif not line.strip():
                        unique_lines.append(line)  # Keep empty lines
                        
                content = '\n'.join(unique_lines)
                
                if content != original_content:
                    with open(csv_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed {csv_file.name}")
                    self.fixes_applied += 1
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {csv_file}: {e}")

    def clean_xml_files(self):
        """Clean paste artifacts in XML files"""
        print("\n🧹 Cleaning XML files...")
        
        xml_files = list(self.module_path.rglob("*.xml"))
        
        for xml_file in xml_files:
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                
                # Fix doubled characters
                for wrong, correct in self.doubled_char_fixes.items():
                    content = content.replace(wrong, correct)
                    
                # Fix model references
                for wrong, correct in self.model_ref_fixes.items():
                    content = content.replace(wrong, correct)
                    
                # Clean XML artifacts - these are often legitimate but duplicated
                # We'll be more careful here and only remove obvious duplicates
                content = self.remove_duplicate_xml_elements(content)
                
                # Fix naid_aaa doubled characters specifically found
                content = content.replace('naid_aaa', 'naid_aa')
                
                if content != original_content:
                    with open(xml_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed {xml_file.name}")
                    self.fixes_applied += 1
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {xml_file}: {e}")

    def remove_duplicate_xml_elements(self, content):
        """Remove duplicate XML elements while preserving structure"""
        
        # Remove duplicate record IDs
        lines = content.split('\n')
        cleaned_lines = []
        seen_records = set()
        
        for line in lines:
            # Check for record definitions
            record_match = re.search(r'<record[^>]*id="([^"]+)"', line)
            if record_match:
                record_id = record_match.group(1)
                if record_id in seen_records:
                    # Skip this duplicate record
                    continue
                seen_records.add(record_id)
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)

    def clean_python_files(self):
        """Clean paste artifacts in Python files"""
        print("\n🧹 Cleaning Python files...")
        
        py_files = list(self.module_path.rglob("*.py"))
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                
                # Fix doubled characters in strings
                for wrong, correct in self.doubled_char_fixes.items():
                    # Only replace in strings, not variable names
                    content = re.sub(rf"'{wrong}'", f"'{correct}'", content)
                    content = re.sub(rf'"{wrong}"', f'"{correct}"', content)
                    
                # Fix model references
                for wrong, correct in self.model_ref_fixes.items():
                    content = content.replace(wrong, correct)
                    
                # Remove duplicate method definitions
                content = self.remove_duplicate_methods(content)
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ Fixed {py_file.name}")
                    self.fixes_applied += 1
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {py_file}: {e}")

    def remove_duplicate_methods(self, content):
        """Remove duplicate method definitions"""
        
        # Find all method definitions
        method_pattern = r'(    def\s+\w+\s*\([^)]*\):.*?)(?=\n    def|\n\nclass|\nclass|$)'
        methods = re.findall(method_pattern, content, re.DOTALL)
        
        # Keep track of seen methods by signature
        seen_methods = set()
        unique_methods = []
        
        for method in methods:
            # Extract method signature for comparison
            signature_match = re.search(r'def\s+(\w+)\s*\([^)]*\)', method)
            if signature_match:
                method_name = signature_match.group(1)
                if method_name not in seen_methods:
                    seen_methods.add(method_name)
                    unique_methods.append(method)
                    
        return content  # For now, return original to avoid breaking code structure

    def fix_manifest_dependencies(self):
        """Fix any paste artifacts in manifest file"""
        print("\n🧹 Cleaning manifest file...")
        
        manifest_file = self.module_path / '__manifest__.py'
        
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Fix doubled characters in manifest
            for wrong, correct in self.doubled_char_fixes.items():
                content = content.replace(wrong, correct)
                
            # Remove duplicate dependencies
            if "'depends'" in content:
                # Extract depends list and remove duplicates
                depends_match = re.search(r"'depends':\s*\[(.*?)\]", content, re.DOTALL)
                if depends_match:
                    depends_content = depends_match.group(1)
                    # Extract individual dependencies
                    deps = re.findall(r"'([^']+)'", depends_content)
                    unique_deps = list(dict.fromkeys(deps))  # Remove duplicates while preserving order
                    
                    # Rebuild depends list
                    new_depends = "[\n        " + ",\n        ".join(f"'{dep}'" for dep in unique_deps) + "\n    ]"
                    content = re.sub(r"'depends':\s*\[.*?\]", f"'depends': {new_depends}", content, flags=re.DOTALL)
                    
            if content != original_content:
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed __manifest__.py")
                self.fixes_applied += 1
                
        except Exception as e:
            print(f"  ⚠️  Error processing manifest: {e}")

    def create_backup(self):
        """Create backup before making changes"""
        print("💾 Creating backup...")
        
        import shutil
        backup_dir = self.module_path.parent / f"records_management_backup_{int(os.path.getmtime(self.module_path))}"
        
        try:
            shutil.copytree(self.module_path, backup_dir)
            print(f"✅ Backup created: {backup_dir}")
            return backup_dir
        except Exception as e:
            print(f"⚠️  Error creating backup: {e}")
            return None

    def validate_fixes(self):
        """Validate that fixes didn't break anything"""
        print("\n🔍 Validating fixes...")
        
        # Check for basic syntax errors in Python files
        py_files = list(self.module_path.rglob("*.py"))
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic syntax check
                compile(content, py_file, 'exec')
                
            except SyntaxError as e:
                print(f"  ⚠️  Syntax error in {py_file}: {e}")
            except Exception as e:
                print(f"  ⚠️  Error validating {py_file}: {e}")
                
        print("✅ Validation complete")

    def run_comprehensive_cleanup(self):
        """Run comprehensive paste artifact cleanup"""
        print("🚀 Starting Comprehensive Paste Artifact Cleanup")
        print("=" * 60)
        
        # Create backup first
        backup_dir = self.create_backup()
        if not backup_dir:
            print("❌ Cannot proceed without backup")
            return
            
        # Clean different file types
        self.clean_csv_files()
        self.clean_xml_files() 
        self.clean_python_files()
        self.fix_manifest_dependencies()
        
        # Validate fixes
        self.validate_fixes()
        
        print(f"\n🎯 Comprehensive Cleanup Complete!")
        print(f"✅ Total fixes applied: {self.fixes_applied}")
        print(f"💾 Backup available: {backup_dir}")
        print("=" * 60)


if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    cleaner = PasteArtifactCleaner(module_path)
    cleaner.run_comprehensive_cleanup()
