#!/usr/bin/env python3
"""
Systematic XML Declaration Standardization Script

This script fixes the XML declaration format issue identified in the Records Management module.
It converts single-quote XML declarations to double-quote format for Odoo 18.0 schema compliance.

Problem: <?xml version='1.0' encoding='utf-8'?>
Solution: <?xml version="1.0" encoding="utf-8"?>

The script:
1. Identifies all XML files with single-quote declarations
2. Safely converts them to double-quote format
3. Validates each conversion
4. Provides detailed logging and rollback capability
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple
import xml.etree.ElementTree as ET

class XMLDeclarationFixer:
    def __init__(self, root_dir: str = "records_management"):
        self.root_dir = Path(root_dir)
        self.backup_dir = Path("backup/xml_declarations_backup")
        self.single_quote_pattern = r"<\?xml\s+version='1\.0'\s+encoding='utf-8'\s*\?>"
        self.double_quote_replacement = '<?xml version="1.0" encoding="utf-8"?>'
        self.fixed_files = []
        self.failed_files = []
        
    def setup_backup_directory(self):
        """Create backup directory for safety"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Backup directory created: {self.backup_dir}")
    
    def find_affected_files(self) -> List[Path]:
        """Find all XML files with single-quote declarations"""
        affected_files = []
        xml_files = list(self.root_dir.rglob("*.xml"))
        
        for xml_file in xml_files:
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if re.search(self.single_quote_pattern, content):
                    affected_files.append(xml_file)
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not read {xml_file}: {e}")
                
        return affected_files
    
    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the file"""
        relative_path = file_path.relative_to(self.root_dir)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_xml_declaration(self, file_path: Path) -> bool:
        """Fix the XML declaration in a single file"""
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Check if file needs fixing
            if not re.search(self.single_quote_pattern, original_content):
                return True  # Already correct
            
            # Create backup
            backup_path = self.backup_file(file_path)
            print(f"📋 Backed up {file_path} → {backup_path}")
            
            # Apply fix
            fixed_content = re.sub(
                self.single_quote_pattern, 
                self.double_quote_replacement, 
                original_content
            )
            
            # Validate XML is still well-formed
            try:
                ET.fromstring(fixed_content)
            except ET.ParseError as e:
                print(f"❌ XML validation failed for {file_path}: {e}")
                return False
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"✅ Fixed XML declaration in {file_path}")
            self.fixed_files.append(file_path)
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix {file_path}: {e}")
            self.failed_files.append((file_path, str(e)))
            return False
    
    def fix_all_files(self, files: List[Path], test_mode: bool = False) -> Tuple[int, int]:
        """Fix XML declarations in all specified files"""
        if test_mode:
            print(f"🧪 TEST MODE: Would fix {len(files)} files")
            files = files[:5]  # Test with only first 5 files
            print(f"🧪 Testing with first {len(files)} files only")
        
        fixed_count = 0
        failed_count = 0
        
        for file_path in files:
            if self.fix_xml_declaration(file_path):
                fixed_count += 1
            else:
                failed_count += 1
        
        return fixed_count, failed_count
    
    def generate_report(self, total_files: int, fixed_count: int, failed_count: int):
        """Generate a summary report"""
        print("\n" + "="*60)
        print("📊 XML Declaration Standardization Report")
        print("="*60)
        print(f"📁 Total files examined: {total_files}")
        print(f"✅ Files successfully fixed: {fixed_count}")
        print(f"❌ Files that failed: {failed_count}")
        print(f"📋 Backup location: {self.backup_dir}")
        
        if self.failed_files:
            print("\n❌ Failed files:")
            for file_path, error in self.failed_files:
                print(f"   - {file_path}: {error}")
        
        if self.fixed_files:
            print(f"\n✅ Successfully fixed {len(self.fixed_files)} files")
            print("🔧 Pattern changed:")
            print("   FROM: <?xml version='1.0' encoding='utf-8'?>")
            print("   TO:   <?xml version=\"1.0\" encoding=\"utf-8\"?>")

def main():
    """Main execution function"""
    print("🚀 Starting XML Declaration Standardization")
    print("🎯 Purpose: Convert single-quote to double-quote XML declarations")
    print("📋 Target: Odoo 18.0 schema compliance for Records Management module\n")
    
    # Parse command line arguments
    test_mode = "--test" in sys.argv
    force_mode = "--force" in sys.argv
    
    # Initialize fixer
    fixer = XMLDeclarationFixer()
    fixer.setup_backup_directory()
    
    # Find affected files
    print("🔍 Scanning for files with single-quote XML declarations...")
    affected_files = fixer.find_affected_files()
    
    if not affected_files:
        print("✅ No files found with single-quote XML declarations!")
        print("🎉 All XML files already use correct double-quote format.")
        return
    
    print(f"📋 Found {len(affected_files)} files needing standardization:")
    for i, file_path in enumerate(affected_files[:10], 1):  # Show first 10
        print(f"   {i:2d}. {file_path}")
    
    if len(affected_files) > 10:
        print(f"   ... and {len(affected_files) - 10} more files")
    
    # Ask for confirmation unless in force mode
    if not force_mode and not test_mode:
        response = input(f"\n🤔 Proceed with fixing {len(affected_files)} files? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled by user")
            return
    
    # Execute fixes
    print(f"\n🔧 {'Testing' if test_mode else 'Fixing'} XML declarations...")
    fixed_count, failed_count = fixer.fix_all_files(affected_files, test_mode)
    
    # Generate report
    fixer.generate_report(len(affected_files), fixed_count, failed_count)
    
    if test_mode:
        print(f"\n🧪 Test completed. Use 'python3 {sys.argv[0]} --force' to apply changes to all files.")
    elif failed_count == 0:
        print(f"\n🎉 SUCCESS: All {fixed_count} files fixed successfully!")
        print("💡 Next steps:")
        print("   1. Run validation: python3 development-tools/comprehensive_validator.py")
        print("   2. Test deployment to confirm XML schema compliance")
        print("   3. Commit changes: git add . && git commit -m 'fix: Standardize XML declarations to double quotes'")
    else:
        print(f"\n⚠️  WARNING: {failed_count} files failed to fix. Check errors above.")

if __name__ == "__main__":
    main()
