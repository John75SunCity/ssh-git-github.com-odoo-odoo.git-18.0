#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Records Management Model Analysis Tool

This script analyzes all model files in the records_management system and provides
detailed summaries of their functionality, purpose, and key features.

Author: Records Management System Analysis
Date: August 14, 2025
"""

import os
import re
import ast
from pathlib import Path

class ModelAnalyzer:
    def __init__(self, models_path):
        self.models_path = Path(models_path)
        self.models_info = {}
        
    def extract_docstring(self, file_content):
        """Extract the module/class docstring from Python file"""
        try:
            tree = ast.parse(file_content)
            if (isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                return tree.body[0].value.value.strip()
        except:
            pass
        
        # Fallback to regex-based extraction
        docstring_pattern = r'"""(.*?)"""'
        match = re.search(docstring_pattern, file_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def extract_class_info(self, file_content):
        """Extract class information from model file"""
        classes = []
        
        # Find class definitions
        class_pattern = r'class\s+(\w+)\([^)]*\):\s*\n(?:\s*"""([^"]*?)""")?'
        matches = re.finditer(class_pattern, file_content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            class_doc = match.group(2).strip() if match.group(2) else None
            classes.append({
                'name': class_name,
                'docstring': class_doc
            })
        
        # Extract _name and _description
        name_pattern = r'_name\s*=\s*["\']([^"\']+)["\']'
        desc_pattern = r'_description\s*=\s*["\']([^"\']+)["\']'
        
        model_name_match = re.search(name_pattern, file_content)
        model_desc_match = re.search(desc_pattern, file_content)
        
        model_name = model_name_match.group(1) if model_name_match else None
        model_desc = model_desc_match.group(1) if model_desc_match else None
        
        return {
            'classes': classes,
            'model_name': model_name,
            'model_description': model_desc
        }
    
    def count_fields(self, file_content):
        """Count different types of fields in the model"""
        field_patterns = {
            'Char': r'fields\.Char\(',
            'Text': r'fields\.Text\(',
            'Integer': r'fields\.Integer\(',
            'Float': r'fields\.Float\(',
            'Boolean': r'fields\.Boolean\(',
            'Date': r'fields\.Date\(',
            'Datetime': r'fields\.Datetime\(',
            'Selection': r'fields\.Selection\(',
            'Many2one': r'fields\.Many2one\(',
            'One2many': r'fields\.One2many\(',
            'Many2many': r'fields\.Many2many\(',
            'Binary': r'fields\.Binary\(',
            'Html': r'fields\.Html\(',
            'Monetary': r'fields\.Monetary\(',
            'Reference': r'fields\.Reference\(',
        }
        
        field_counts = {}
        total_fields = 0
        
        for field_type, pattern in field_patterns.items():
            count = len(re.findall(pattern, file_content))
            if count > 0:
                field_counts[field_type] = count
                total_fields += count
                
        return field_counts, total_fields
    
    def extract_methods(self, file_content):
        """Extract method information from the model"""
        method_patterns = {
            'compute': r'def\s+(_compute_\w+)',
            'onchange': r'def\s+(_onchange_\w+)',
            'action': r'def\s+(action_\w+)',
            'api_model': r'@api\.model\s*\n\s*def\s+(\w+)',
            'constrains': r'@api\.constrains.*?\n\s*def\s+(\w+)',
        }
        
        method_counts = {}
        for method_type, pattern in method_patterns.items():
            matches = re.findall(pattern, file_content, re.MULTILINE)
            if matches:
                method_counts[method_type] = len(matches)
                
        return method_counts
    
    def categorize_model(self, model_name, file_name, class_info):
        """Categorize the model based on its name and content"""
        categories = {
            'Core Records': ['records.container', 'records.document', 'records.location', 'records.tag'],
            'NAID Compliance': ['naid.', 'chain.of.custody', 'destruction', 'certificate'],
            'Customer Portal': ['portal.', 'customer.feedback', 'portal.request'],
            'Billing & Finance': ['billing', 'rate', 'invoice', 'payment', 'revenue'],
            'Field Service': ['fsm.', 'pickup.', 'route', 'work.order'],
            'Document Management': ['document.', 'file.', 'scan', 'retrieval'],
            'Shredding Operations': ['shredding', 'destruction', 'hard.drive', 'bale'],
            'Security & Access': ['bin.key', 'access', 'security', 'audit'],
            'Wizards & Tools': ['wizard', 'report.wizard', 'import'],
            'System Configuration': ['config', 'settings', 'installer', 'configurator'],
            'Integration': ['hr.', 'res.', 'account.', 'stock.', 'project.', 'pos.'],
        }
        
        model_lower = (model_name or file_name).lower()
        
        for category, keywords in categories.items():
            if any(keyword in model_lower for keyword in keywords):
                return category
                
        return 'Other'
    
    def analyze_file(self, file_path):
        """Analyze a single model file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_name = file_path.stem
            file_size = len(content)
            line_count = content.count('\n') + 1
            
            # Extract information
            module_docstring = self.extract_docstring(content)
            class_info = self.extract_class_info(content)
            field_counts, total_fields = self.count_fields(content)
            method_counts = self.extract_methods(content)
            
            # Categorize model
            category = self.categorize_model(class_info['model_name'], file_name, class_info)
            
            return {
                'file_name': file_name,
                'file_size': file_size,
                'line_count': line_count,
                'module_docstring': module_docstring,
                'model_name': class_info['model_name'],
                'model_description': class_info['model_description'],
                'classes': class_info['classes'],
                'field_counts': field_counts,
                'total_fields': total_fields,
                'method_counts': method_counts,
                'category': category,
            }
            
        except Exception as e:
            return {
                'file_name': file_path.stem,
                'error': str(e),
                'category': 'Error'
            }
    
    def analyze_all_models(self):
        """Analyze all model files"""
        model_files = [f for f in self.models_path.glob('*.py') if f.name != '__init__.py']
        
        print(f"🔍 Analyzing {len(model_files)} model files...")
        
        for file_path in sorted(model_files):
            analysis = self.analyze_file(file_path)
            self.models_info[file_path.stem] = analysis
            
        return self.models_info
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        if not self.models_info:
            self.analyze_all_models()
            
        # Categorize models
        categories = {}
        total_files = 0
        total_lines = 0
        total_fields = 0
        
        for model_name, info in self.models_info.items():
            if 'error' in info:
                continue
                
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(info)
            
            total_files += 1
            total_lines += info.get('line_count', 0)
            total_fields += info.get('total_fields', 0)
        
        # Generate report
        report = []
        report.append("# 📋 COMPREHENSIVE RECORDS MANAGEMENT MODEL ANALYSIS")
        report.append(f"## Generated: August 14, 2025")
        report.append("")
        report.append("## 📊 **SYSTEM OVERVIEW**")
        report.append("")
        report.append(f"- **Total Model Files**: {total_files}")
        report.append(f"- **Total Lines of Code**: {total_lines:,}")
        report.append(f"- **Total Fields**: {total_fields:,}")
        report.append(f"- **Model Categories**: {len(categories)}")
        report.append("")
        
        # Category breakdown
        report.append("## 🏗️ **MODEL CATEGORIES BREAKDOWN**")
        report.append("")
        
        for category, models in sorted(categories.items()):
            report.append(f"### {category} ({len(models)} models)")
            report.append("")
            
            for model in sorted(models, key=lambda x: x['file_name']):
                model_name = model.get('model_name', 'N/A')
                model_desc = model.get('model_description', 'No description')
                total_fields = model.get('total_fields', 0)
                line_count = model.get('line_count', 0)
                
                report.append(f"**{model['file_name']}.py**")
                report.append(f"- Model Name: `{model_name}`")
                report.append(f"- Description: {model_desc}")
                report.append(f"- Fields: {total_fields}, Lines: {line_count}")
                
                if model.get('module_docstring'):
                    # Extract first line of docstring for summary
                    first_line = model['module_docstring'].split('\n')[0].strip()
                    if first_line:
                        report.append(f"- Purpose: {first_line}")
                
                report.append("")
            
            report.append("")
        
        return '\n'.join(report)
    
    def generate_detailed_model_summaries(self):
        """Generate detailed summaries for each model"""
        if not self.models_info:
            self.analyze_all_models()
            
        report = []
        report.append("# 📚 DETAILED MODEL SUMMARIES")
        report.append("## Records Management System - Complete Model Documentation")
        report.append("")
        report.append("---")
        report.append("")
        
        # Sort models by category and name
        categorized_models = {}
        for model_name, info in self.models_info.items():
            if 'error' in info:
                continue
            category = info['category']
            if category not in categorized_models:
                categorized_models[category] = []
            categorized_models[category].append(info)
        
        for category, models in sorted(categorized_models.items()):
            report.append(f"## 🏷️ {category}")
            report.append("")
            
            for model in sorted(models, key=lambda x: x['file_name']):
                report.append(f"### 📄 {model['file_name']}.py")
                report.append("")
                
                # Basic info
                report.append("**Model Information:**")
                report.append(f"- **Model Name**: `{model.get('model_name', 'N/A')}`")
                report.append(f"- **Description**: {model.get('model_description', 'No description')}")
                report.append(f"- **File Size**: {model.get('line_count', 0):,} lines")
                report.append(f"- **Total Fields**: {model.get('total_fields', 0)}")
                report.append("")
                
                # Field breakdown
                if model.get('field_counts'):
                    report.append("**Field Types:**")
                    for field_type, count in sorted(model['field_counts'].items()):
                        report.append(f"- {field_type}: {count}")
                    report.append("")
                
                # Methods
                if model.get('method_counts'):
                    report.append("**Methods:**")
                    for method_type, count in sorted(model['method_counts'].items()):
                        report.append(f"- {method_type.title()}: {count}")
                    report.append("")
                
                # Purpose/Documentation
                if model.get('module_docstring'):
                    report.append("**Purpose & Functionality:**")
                    # Clean up the docstring for display
                    docstring = model['module_docstring']
                    # Remove excessive whitespace but preserve structure
                    lines = [line.strip() for line in docstring.split('\n') if line.strip()]
                    cleaned_docstring = '\n'.join(lines)
                    
                    if len(cleaned_docstring) > 500:
                        # Truncate very long docstrings
                        cleaned_docstring = cleaned_docstring[:500] + "..."
                    
                    report.append(f"```")
                    report.append(cleaned_docstring)
                    report.append("```")
                    report.append("")
                
                # Classes
                if model.get('classes'):
                    report.append("**Classes:**")
                    for cls in model['classes']:
                        report.append(f"- `{cls['name']}`")
                        if cls.get('docstring'):
                            report.append(f"  - {cls['docstring']}")
                    report.append("")
                
                report.append("---")
                report.append("")
        
        return '\n'.join(report)

def main():
    """Main execution function"""
    script_dir = Path(__file__).parent
    models_path = script_dir.parent / "records_management" / "models"
    
    analyzer = ModelAnalyzer(models_path)
    
    print("🚀 Starting comprehensive model analysis...")
    
    # Generate summary report
    summary_report = analyzer.generate_summary_report()
    summary_path = script_dir / "MODEL_ANALYSIS_SUMMARY.md"
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    print(f"📋 Summary report saved to: {summary_path}")
    
    # Generate detailed model summaries
    detailed_report = analyzer.generate_detailed_model_summaries()
    detailed_path = script_dir / "DETAILED_MODEL_SUMMARIES.md"
    
    with open(detailed_path, 'w', encoding='utf-8') as f:
        f.write(detailed_report)
    
    print(f"📚 Detailed summaries saved to: {detailed_path}")
    
    print("✅ Model analysis complete!")
    
    # Print quick stats
    total_models = len([info for info in analyzer.models_info.values() if 'error' not in info])
    total_fields = sum(info.get('total_fields', 0) for info in analyzer.models_info.values() if 'error' not in info)
    total_lines = sum(info.get('line_count', 0) for info in analyzer.models_info.values() if 'error' not in info)
    
    print(f"\n📊 **QUICK STATS:**")
    print(f"   Models: {total_models}")
    print(f"   Fields: {total_fields:,}")
    print(f"   Lines:  {total_lines:,}")

if __name__ == "__main__":
    main()
