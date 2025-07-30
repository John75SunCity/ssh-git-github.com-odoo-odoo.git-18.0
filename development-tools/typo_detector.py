#!/usr/bin/env python3
"""
Advanced Typo Detection for Odoo Records Management Module
=========================================================

This tool detects potential typos by:
1. Building a dictionary of known good words from the codebase
2. Finding anomalous words that might be paste errors
3. Detecting doubled/tripled characters that suggest copy-paste issues
4. Checking for common Odoo field/model naming patterns

Usage: python typo_detector.py
"""

import os
import re
import csv
from collections import defaultdict, Counter
from pathlib import Path

class TypoDetector:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.known_words = set()
        self.odoo_patterns = set()
        self.suspicious_words = []
        self.field_names = set()
        self.model_names = set()
        
        # Common Odoo field types and patterns
        self.odoo_field_types = {
            'char', 'text', 'html', 'integer', 'float', 'boolean', 'date', 'datetime',
            'binary', 'selection', 'many2one', 'one2many', 'many2many', 'reference',
            'monetary', 'computed', 'related', 'property'
        }
        
        # Common business terms in records management
        self.business_terms = {
            'records', 'document', 'container', 'box', 'location', 'shredding', 'naid',
            'compliance', 'audit', 'certificate', 'destruction', 'retention', 'policy',
            'pickup', 'delivery', 'barcode', 'scanning', 'portal', 'customer', 'feedback',
            'billing', 'invoice', 'payment', 'service', 'request', 'approval', 'workflow'
        }

    def build_dictionary(self):
        """Build dictionary from Python files"""
        print("🔍 Building dictionary from codebase...")
        
        for py_file in self.module_path.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract field names
                field_matches = re.findall(r'(\w+)\s*=\s*fields\.', content)
                self.field_names.update(field_matches)
                
                # Extract model names
                model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                self.model_names.update(model_matches)
                
                # Extract all identifier words
                words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
                self.known_words.update(words)
                
            except Exception as e:
                print(f"⚠️  Error reading {py_file}: {e}")

    def detect_doubled_characters(self, text):
        """Detect words with suspicious character doubling"""
        doubled_pattern = r'\b\w*([a-z])\1{2,}\w*\b'  # 3+ consecutive same letters
        return re.findall(doubled_pattern, text, re.IGNORECASE)

    def detect_paste_artifacts(self, text):
        """Detect common paste error patterns"""
        patterns = [
            r'\b\w*(requestuest|certificateificate|complianceliance)\w*\b',  # Known patterns
            r'\b\w*([a-z]{3,})\1+\w*\b',  # Repeated substrings
            r'\b\w*_[a-z]+_[a-z]+_[a-z]+_[a-z]+\b',  # Too many underscores
        ]
        
        suspicious = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            suspicious.extend(matches)
        return suspicious

    def check_csv_files(self):
        """Check CSV files for typos"""
        print("\n📄 Checking CSV files...")
        
        for csv_file in self.module_path.rglob("*.csv"):
            print(f"  Checking: {csv_file.name}")
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for doubled characters
                doubled = self.detect_doubled_characters(content)
                if doubled:
                    print(f"    🚨 Doubled characters found: {doubled}")
                    
                # Check for paste artifacts
                artifacts = self.detect_paste_artifacts(content)
                if artifacts:
                    print(f"    🚨 Paste artifacts found: {artifacts}")
                    
                # Check each line for external ID patterns
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'model_' in line:
                        # Extract model references
                        model_refs = re.findall(r'model_([a-zA-Z0-9_]+)', line)
                        for ref in model_refs:
                            # Check if it looks suspicious
                            if len(ref) > 50:  # Unusually long
                                print(f"    🚨 Line {i}: Suspiciously long model ref: model_{ref}")
                            if self.detect_doubled_characters(ref):
                                print(f"    🚨 Line {i}: Doubled chars in model ref: model_{ref}")
                                
            except Exception as e:
                print(f"    ⚠️  Error reading {csv_file}: {e}")

    def check_xml_files(self):
        """Check XML files for typos"""
        print("\n📄 Checking XML files...")
        
        for xml_file in self.module_path.rglob("*.xml"):
            if 'static' in str(xml_file):  # Skip static assets
                continue
                
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for doubled characters in field names
                field_refs = re.findall(r'name=["\']([^"\']+)["\']', content)
                for field_ref in field_refs:
                    doubled = self.detect_doubled_characters(field_ref)
                    if doubled:
                        print(f"  🚨 {xml_file.name}: Doubled chars in field: {field_ref}")
                        
                # Check for paste artifacts
                artifacts = self.detect_paste_artifacts(content)
                if artifacts:
                    print(f"  🚨 {xml_file.name}: Paste artifacts: {artifacts}")
                    
            except Exception as e:
                print(f"  ⚠️  Error reading {xml_file}: {e}")

    def find_unknown_words(self):
        """Find words that don't appear in our dictionary"""
        print("\n🔍 Finding potentially unknown words...")
        
        # Build comprehensive word list
        all_files_words = set()
        
        for file_type in ["*.py", "*.xml", "*.csv"]:
            for file_path in self.module_path.rglob(file_type):
                if '__pycache__' in str(file_path) or 'static' in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
                        all_files_words.update(words)
                except:
                    continue
        
        # Find words that are potentially typos
        word_freq = Counter(all_files_words)
        rare_words = [word for word, count in word_freq.items() 
                     if count == 1 and len(word) > 8 and '_' in word]
        
        print(f"  Found {len(rare_words)} rare/unique long words with underscores:")
        for word in sorted(rare_words)[:20]:  # Show first 20
            print(f"    {word}")

    def validate_model_references(self):
        """Validate all model references in CSV files"""
        print("\n🔗 Validating model references...")
        
        # Get all actual model names from Python files
        actual_models = set()
        for py_file in self.module_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    actual_models.update(model_matches)
            except:
                continue
        
        # Convert to expected external ID format
        expected_external_ids = set()
        for model in actual_models:
            external_id = f"model_{model.replace('.', '_')}"
            expected_external_ids.add(external_id)
        
        # Check CSV files for invalid references
        for csv_file in self.module_path.rglob("*.csv"):
            if 'access' not in csv_file.name:
                continue
                
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find all model references
                model_refs = re.findall(r'model_[a-zA-Z0-9_]+', content)
                
                for ref in model_refs:
                    if ref not in expected_external_ids:
                        print(f"  🚨 {csv_file.name}: Invalid model reference: {ref}")
                        
                        # Suggest closest match
                        closest = self.find_closest_match(ref, expected_external_ids)
                        if closest:
                            print(f"    💡 Did you mean: {closest}?")
                            
            except Exception as e:
                print(f"  ⚠️  Error checking {csv_file}: {e}")

    def find_closest_match(self, target, candidates):
        """Find closest matching string using simple similarity"""
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            # Simple similarity based on common characters
            common = len(set(target) & set(candidate))
            similarity = common / max(len(target), len(candidate))
            
            if similarity > best_score and similarity > 0.7:
                best_score = similarity
                best_match = candidate
                
        return best_match

    def run_full_scan(self):
        """Run complete typo detection scan"""
        print("🚀 Starting Comprehensive Typo Detection")
        print("=" * 60)
        
        self.build_dictionary()
        print(f"✅ Built dictionary with {len(self.known_words)} words")
        print(f"✅ Found {len(self.model_names)} models")
        print(f"✅ Found {len(self.field_names)} fields")
        
        self.check_csv_files()
        self.check_xml_files()
        self.find_unknown_words()
        self.validate_model_references()
        
        print("\n🎯 Typo Detection Complete!")
        print("=" * 60)

if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    detector = TypoDetector(module_path)
    detector.run_full_scan()
