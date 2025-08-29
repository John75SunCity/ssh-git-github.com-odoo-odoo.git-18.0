#!/usr/bin/env python3
"""
Advanced Odoo Model Analysis Tool
Provides detailed analysis of model structure, relationships, and dependencies
"""

import os
import re
import ast
import sys
from collections import defaultdict, Counter

class OdooModelAnalyzer:
    def __init__(self, module_path):
        self.module_path = module_path
        self.models_dir = os.path.join(module_path, 'models')
        self.analysis_results = {}

    def analyze_models(self):
        """Main analysis function"""
        print("🔍 Advanced Odoo Model Analysis")
        print("=" * 50)

        # Get all Python model files
        model_files = [f for f in os.listdir(self.models_dir)
                      if f.endswith('.py') and f not in ['__init__.py', '__pycache__']]

        print(f"Found {len(model_files)} model files to analyze")

        # Analyze each model
        models_data = []
        for model_file in model_files:
            model_data = self.analyze_model_file(model_file)
            if model_data:
                models_data.append(model_data)

        # Generate comprehensive report
        self.generate_report(models_data)

    def analyze_model_file(self, filename):
        """Analyze a single model file"""
        filepath = os.path.join(self.models_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            model_data = {
                'filename': filename,
                'model_name': None,
                'inherit': [],
                'fields': [],
                'methods': [],
                'imports': [],
                'dependencies': []
            }

            # Extract model information
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's an Odoo model
                    for base in node.bases:
                        if isinstance(base, ast.Attribute):
                            if (isinstance(base.value, ast.Name) and
                                base.value.id in ['models', 'odoo']) or \
                               (hasattr(base, 'attr') and base.attr == 'Model'):
                                model_data['class_name'] = node.name
                                break

                    # Look for _name and _inherit
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    if target.id == '_name':
                                        if isinstance(item.value, ast.Str):
                                            model_data['model_name'] = item.value.s
                                        elif hasattr(item.value, 'value'):  # Python 3.8+
                                            model_data['model_name'] = item.value.value
                                    elif target.id == '_inherit':
                                        if isinstance(item.value, ast.Str):
                                            model_data['inherit'].append(item.value.s)
                                        elif isinstance(item.value, ast.List):
                                            for elt in item.value.elts:
                                                if isinstance(elt, ast.Str):
                                                    model_data['inherit'].append(elt.s)

                    # Count fields and methods
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    if target.id.endswith('_id') or 'field' in target.id.lower():
                                        model_data['fields'].append(target.id)
                        elif isinstance(item, ast.FunctionDef):
                            if not item.name.startswith('_'):
                                model_data['methods'].append(item.name)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        model_data['imports'].append(node.module)

            return model_data if model_data['model_name'] else None

        except Exception as e:
            print(f"Error analyzing {filename}: {e}")
            return None

    def generate_report(self, models_data):
        """Generate comprehensive analysis report"""
        if not models_data:
            print("No models found to analyze")
            return

        print(f"\n📊 Analysis Results ({len(models_data)} models)")
        print("-" * 40)

        # Model categories
        categories = defaultdict(int)
        inheritance_patterns = Counter()
        field_patterns = Counter()

        for model in models_data:
            # Categorize models
            if 'records' in model['model_name'].lower():
                categories['Core Records'] += 1
            elif 'billing' in model['model_name'].lower():
                categories['Billing'] += 1
            elif 'naid' in model['model_name'].lower():
                categories['NAID Compliance'] += 1
            elif 'fsm' in model['model_name'].lower():
                categories['FSM Integration'] += 1
            elif 'portal' in model['model_name'].lower():
                categories['Portal'] += 1
            elif 'survey' in model['model_name'].lower():
                categories['Survey'] += 1
            else:
                categories['Other'] += 1

            # Inheritance patterns
            if model['inherit']:
                for inherit in model['inherit']:
                    inheritance_patterns[inherit] += 1

            # Field patterns
            for field in model['fields'][:5]:  # First 5 fields
                if '_id' in field:
                    field_patterns['Many2one'] += 1
                elif '_ids' in field:
                    field_patterns['One2many/Many2many'] += 1
                else:
                    field_patterns['Other'] += 1

        # Print category breakdown
        print("\n🏷️  Model Categories:")
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count} models")

        # Print inheritance patterns
        print("\n🔗 Top Inheritance Patterns:")
        for pattern, count in inheritance_patterns.most_common(5):
            print(f"  {pattern}: {count} models")

        # Print field patterns
        print("\n📋 Field Type Distribution:")
        total_fields = sum(field_patterns.values())
        for field_type, count in field_patterns.items():
            percentage = (count / total_fields * 100) if total_fields > 0 else 0
            print(".1f")

        # Model complexity analysis
        print("\n📈 Model Complexity:")
        complexities = []
        for model in models_data:
            complexity = len(model['fields']) + len(model['methods'])
            complexities.append((model['filename'], complexity))

        complexities.sort(key=lambda x: x[1], reverse=True)
        print("Top 5 most complex models:")
        for filename, complexity in complexities[:5]:
            print(f"  {filename}: {complexity} components")

        # Dependency analysis
        print("\n🔧 Module Dependencies:")
        all_imports = []
        for model in models_data:
            all_imports.extend(model['imports'])

        import_counts = Counter(all_imports)
        print("Top external dependencies:")
        for module, count in import_counts.most_common(5):
            if module and not module.startswith('.'):
                print(f"  {module}: {count} models")

        print("\n✅ Model analysis completed!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python model_analyzer.py <module_path>")
        print("Example: python model_analyzer.py /path/to/records_management")
        sys.exit(1)

    module_path = sys.argv[1]
    if not os.path.exists(module_path):
        print(f"Error: Module path {module_path} does not exist")
        sys.exit(1)

    analyzer = OdooModelAnalyzer(module_path)
    analyzer.analyze_models()

if __name__ == "__main__":
    main()
