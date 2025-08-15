#!/usr/bin/env python3
"""
COMPREHENSIVE ONE2MANY → MANY2ONE RELATIONSHIP VALIDATOR
========================================================

Systematically validates ALL One2many relationships to find missing inverse fields.
This addresses the KeyError: 'certificate_id' and similar field reference errors.

Usage: python development-tools/comprehensive_relationship_validator.py
"""

import os
import re
import sys
from pathlib import Path

class ComprehensiveRelationshipValidator:
    def __init__(self):
        self.models_dir = Path("records_management/models")
        self.one2many_relationships = {}
        self.model_fields = {}
        self.broken_relationships = []
        
        # Framework models to exclude from validation (these are core Odoo models)
        self.framework_models = {
            'mail.activity', 'mail.message', 'mail.followers', 'mail.thread',
            'account.move', 'account.move.line', 'account.payment',
            'quality.check', 'maintenance.request', 'maintenance.equipment',
            'project.task', 'hr.employee', 'res.partner', 'res.company',
            'stock.picking', 'stock.move', 'stock.lot',
        }
        
    def extract_model_name_from_file(self, filepath):
        """Extract the _name value from a model file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for _name = 'model.name' pattern
            name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            if name_match:
                return name_match.group(1)
                
            # Fallback: derive from filename
            filename = filepath.stem
            if filename.endswith('.py'):
                filename = filename[:-3]
            return filename.replace('_', '.')
            
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return None
    
    def extract_fields_from_model(self, filepath):
        """Extract all field definitions from a model file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fields = {}
            
            # Find all field definitions
            field_patterns = [
                r"(\w+)\s*=\s*fields\.Many2one\(",
                r"(\w+)\s*=\s*fields\.One2many\(",
                r"(\w+)\s*=\s*fields\.Many2many\(",
                r"(\w+)\s*=\s*fields\.Char\(",
                r"(\w+)\s*=\s*fields\.Text\(",
                r"(\w+)\s*=\s*fields\.Integer\(",
                r"(\w+)\s*=\s*fields\.Float\(",
                r"(\w+)\s*=\s*fields\.Boolean\(",
                r"(\w+)\s*=\s*fields\.Date\(",
                r"(\w+)\s*=\s*fields\.Datetime\(",
                r"(\w+)\s*=\s*fields\.Selection\(",
                r"(\w+)\s*=\s*fields\.Monetary\(",
            ]
            
            for pattern in field_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for field_name in matches:
                    if not field_name.startswith('_'):  # Skip private fields
                        fields[field_name] = True
                        
            return fields
            
        except Exception as e:
            print(f"❌ Error extracting fields from {filepath}: {e}")
            return {}
    
    def extract_one2many_relationships(self, filepath):
        """Extract One2many field definitions with their inverse relationships"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            relationships = []
            
            # Pattern to match One2many field definitions
            pattern = r'(\w+)\s*=\s*fields\.One2many\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*[,\)]'
            
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            
            for field_name, comodel, inverse_name in matches:
                relationships.append({
                    'field_name': field_name,
                    'comodel': comodel,
                    'inverse_name': inverse_name,
                    'source_file': filepath.name
                })
                
            return relationships
            
        except Exception as e:
            print(f"❌ Error extracting One2many from {filepath}: {e}")
            return []
    
    def find_model_file_for_name(self, model_name):
        """Find the Python file that defines a specific model"""
        # Try direct filename mapping first
        expected_filename = model_name.replace('.', '_') + '.py'
        expected_path = self.models_dir / expected_filename
        
        if expected_path.exists():
            return expected_path
            
        # Search through all model files
        for py_file in self.models_dir.glob("*.py"):
            if py_file.name.startswith('__'):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if f"_name = '{model_name}'" in content or f'_name = "{model_name}"' in content:
                    return py_file
                    
            except Exception:
                continue
                
        return None
    
    def validate_all_relationships(self):
        """Validate all One2many relationships in the models directory"""
        print("🔍 COMPREHENSIVE ONE2MANY RELATIONSHIP VALIDATION")
        print("=" * 60)
        
        # Step 1: Collect all model fields
        print("📋 Step 1: Scanning all model files for field definitions...")
        py_files = [f for f in self.models_dir.glob("*.py") if not f.name.startswith('__')]
        
        for py_file in py_files:
            model_name = self.extract_model_name_from_file(py_file)
            if model_name:
                fields = self.extract_fields_from_model(py_file)
                self.model_fields[model_name] = {
                    'fields': fields,
                    'file': py_file.name
                }
        
        print(f"✅ Scanned {len(self.model_fields)} model files")
        
        # Step 2: Collect all One2many relationships
        print("\n📋 Step 2: Extracting all One2many relationships...")
        all_relationships = []
        
        for py_file in py_files:
            relationships = self.extract_one2many_relationships(py_file)
            all_relationships.extend(relationships)
            
        print(f"✅ Found {len(all_relationships)} One2many relationships")
        
        # Step 3: Validate each relationship
        print("\n📋 Step 3: Validating inverse field existence...")
        valid_count = 0
        broken_count = 0
        
        for rel in all_relationships:
            comodel = rel['comodel']
            inverse_name = rel['inverse_name']
            field_name = rel['field_name']
            source_file = rel['source_file']
            
            # Check if comodel exists and has the inverse field
            if comodel in self.model_fields:
                if inverse_name in self.model_fields[comodel]['fields']:
                    print(f"✅ {source_file}: {field_name} → {comodel}.{inverse_name}")
                    valid_count += 1
                else:
                    print(f"❌ {source_file}: {field_name} → {comodel}.{inverse_name} (MISSING)")
                    self.broken_relationships.append({
                        'source_file': source_file,
                        'field_name': field_name,
                        'comodel': comodel,
                        'inverse_name': inverse_name,
                        'target_file': self.model_fields[comodel]['file']
                    })
                    broken_count += 1
            elif comodel in self.framework_models:
                # Skip framework models - they're not broken, just not in our custom modules
                print(f"⚪ {source_file}: {field_name} → {comodel}.{inverse_name} (FRAMEWORK - SKIPPED)")
                valid_count += 1
            else:
                # Try to find the model file
                model_file = self.find_model_file_for_name(comodel)
                if model_file:
                    print(f"⚠️  {source_file}: {field_name} → {comodel}.{inverse_name} (model found but not scanned)")
                    broken_count += 1
                else:
                    print(f"❌ {source_file}: {field_name} → {comodel} (MODEL NOT FOUND)")
                    broken_count += 1
        
        # Step 4: Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY:")
        print(f"   Total relationships: {len(all_relationships)}")
        print(f"   Valid relationships: {valid_count}")
        print(f"   Broken relationships: {broken_count}")
        
        if self.broken_relationships:
            print(f"\n🚨 CRITICAL: {len(self.broken_relationships)} broken relationships found!")
            print("\n📋 BROKEN RELATIONSHIPS TO FIX:")
            
            for broken in self.broken_relationships:
                print(f"\n❌ {broken['source_file']}:")
                print(f"   Field: {broken['field_name']}")
                print(f"   Comodel: {broken['comodel']}")
                print(f"   Missing inverse: {broken['inverse_name']}")
                print(f"   Target file: {broken['target_file']}")
                print(f"   💡 FIX: Add '{broken['inverse_name']} = fields.Many2one(\"{self.get_model_name_from_file(broken['source_file'])}\")' to {broken['target_file']}")
        else:
            print("\n🎉 SUCCESS: All One2many relationships are properly configured!")
            
        # Summary of exclusions
        framework_count = len([r for r in all_relationships if r['comodel'] in self.framework_models])
        print(f"\n📋 FRAMEWORK MODELS EXCLUDED: {framework_count} relationships")
        print("   (These are core Odoo models - mail.*, account.*, hr.*, etc.)")
            
        return broken_count == 0
    
    def get_model_name_from_file(self, filename):
        """Get model name from source filename"""
        for model_name, data in self.model_fields.items():
            if data['file'] == filename:
                return model_name
        return filename.replace('.py', '').replace('_', '.')

def main():
    """Main validation function"""
    try:
        validator = ComprehensiveRelationshipValidator()
        success = validator.validate_all_relationships()
        
        if not success:
            print("\n🚨 ACTION REQUIRED: Fix the broken relationships above!")
            sys.exit(1)
        else:
            print("\n✅ All relationships validated successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
