#!/usr/bin/env python3
"""
Smart Test Analysis and Fix Suggestion Tool

This tool analyzes test files and provides intelligent fix suggestions
that GitHub Copilot can use to generate better tests.
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class TestAnalyzer:
    """Analyzes test files and suggests improvements"""

    def __init__(self, records_management_path: str):
        self.rm_path = Path(records_management_path)
        self.tests_path = self.rm_path / 'tests'
        self.models_path = self.rm_path / 'models'

    def analyze_all_tests(self) -> Dict[str, Any]:
        """Analyze all test files and return comprehensive report"""
        report = {
            'test_files': [],
            'missing_tests': [],
            'test_issues': [],
            'coverage_gaps': [],
            'fix_suggestions': []
        }

        # Get all test files
        test_files = list(self.tests_path.glob('test_*.py'))
        model_files = list(self.models_path.glob('*.py'))

        print(f"📊 Analyzing {len(test_files)} test files...")

        for test_file in test_files:
            analysis = self.analyze_test_file(test_file)
            report['test_files'].append(analysis)

            if analysis['issues']:
                report['test_issues'].extend(analysis['issues'])

        # Find missing tests
        tested_models = {tf.stem.replace('test_', '') for tf in test_files}
        all_models = {mf.stem for mf in model_files if not mf.stem.startswith('__')}
        missing = all_models - tested_models

        report['missing_tests'] = list(missing)
        report['fix_suggestions'] = self.generate_fix_suggestions(report)

        return report

    def analyze_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Analyze individual test file"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return {
                    'file': test_file.name,
                    'status': 'syntax_error',
                    'error': str(e),
                    'issues': [{'type': 'syntax', 'message': str(e)}]
                }

            analysis = {
                'file': test_file.name,
                'status': 'analyzed',
                'classes': [],
                'methods': [],
                'imports': [],
                'issues': [],
                'patterns': []
            }

            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        analysis['methods'].append(node.name)
                elif isinstance(node, ast.Import):
                    analysis['imports'].extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['imports'].append(node.module)

            # Check for common issues
            analysis['issues'] = self.check_test_issues(content, analysis)
            analysis['patterns'] = self.identify_test_patterns(content)

            return analysis

        except Exception as e:
            return {
                'file': test_file.name,
                'status': 'error',
                'error': str(e),
                'issues': [{'type': 'file_error', 'message': str(e)}]
            }

    def check_test_issues(self, content: str, analysis: Dict) -> List[Dict]:
        """Check for common test issues"""
        issues = []

        # Check for missing imports
        required_imports = ['TransactionCase', 'ValidationError', 'UserError']
        for req_import in required_imports:
            if req_import not in content:
                issues.append({
                    'type': 'missing_import',
                    'message': f'Missing import: {req_import}',
                    'suggestion': f'Add: from odoo.exceptions import {req_import}',
                    'severity': 'medium'
                })

        # Check for test method patterns
        if not any(method.startswith('test_') for method in analysis['methods']):
            issues.append({
                'type': 'no_test_methods',
                'message': 'No test methods found (should start with test_)',
                'suggestion': 'Add test methods starting with test_',
                'severity': 'high'
            })

        # Check for setup methods
        if 'setUpClass' not in content and 'setUp' not in content:
            issues.append({
                'type': 'missing_setup',
                'message': 'Missing setup method',
                'suggestion': 'Add setUpClass or setUp method for test data',
                'severity': 'medium'
            })

        # Check for TODO comments (incomplete tests)
        todo_count = len(re.findall(r'# TODO', content, re.IGNORECASE))
        if todo_count > 5:
            issues.append({
                'type': 'incomplete_test',
                'message': f'Many TODO comments ({todo_count}) - test may be incomplete',
                'suggestion': 'Complete TODO items or remove placeholder code',
                'severity': 'low'
            })

        # Check for hardcoded values
        if 'test@example.com' in content:
            issues.append({
                'type': 'hardcoded_values',
                'message': 'Using placeholder email addresses',
                'suggestion': 'Use more realistic test data',
                'severity': 'low'
            })

        return issues

    def identify_test_patterns(self, content: str) -> List[str]:
        """Identify test patterns used"""
        patterns = []

        if 'with self.assertRaises' in content:
            patterns.append('exception_testing')

        if '@patch' in content or 'MagicMock' in content:
            patterns.append('mocking')

        if 'self.env[' in content:
            patterns.append('odoo_orm')

        if 'create(' in content:
            patterns.append('record_creation')

        if 'search(' in content:
            patterns.append('record_search')

        if 'write(' in content:
            patterns.append('record_update')

        if 'unlink(' in content:
            patterns.append('record_deletion')

        return patterns

    def generate_fix_suggestions(self, report: Dict) -> List[Dict]:
        """Generate intelligent fix suggestions"""
        suggestions = []

        # Suggestions for missing tests
        for missing_model in report['missing_tests']:
            suggestions.append({
                'type': 'missing_test',
                'target': missing_model,
                'priority': 'high',
                'action': f'Create test_{missing_model}.py',
                'copilot_prompt': f'# Generate comprehensive test for {missing_model} model',
                'template': self.get_test_template(missing_model)
            })

        # Suggestions for test issues
        issue_types = {}
        for issue in report['test_issues']:
            issue_type = issue['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issues in issue_types.items():
            if len(issues) > 3:  # Common issue
                suggestions.append({
                    'type': 'bulk_fix',
                    'target': issue_type,
                    'priority': 'medium',
                    'action': f'Fix {len(issues)} instances of {issue_type}',
                    'copilot_prompt': f'# Fix {issue_type} in all test files',
                    'files_affected': len(set(issue.get('file', '') for issue in issues))
                })

        return suggestions

    def get_test_template(self, model_name: str) -> str:
        """Get test template for a model"""
        class_name = ''.join(word.capitalize() for word in model_name.split('_'))

        return f'''"""
Test cases for the {model_name} model in the records management module.

Generated by Smart Test Analyzer - customize as needed.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date
from unittest.mock import patch, MagicMock

class Test{class_name}(TransactionCase):
    """Test cases for {model_name} model"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # TODO: Add model-specific setup data
        cls.partner = cls.env['res.partner'].create({{
            'name': 'Test Partner',
            'email': 'test@example.com',
        }})

    def test_create_{model_name}(self):
        """Test creating a {model_name} record"""
        # TODO: Implement creation test
        pass

    def test_validation_{model_name}(self):
        """Test validation rules for {model_name}"""
        # TODO: Implement validation tests
        pass

    def test_constraints_{model_name}(self):
        """Test constraints for {model_name}"""
        # TODO: Implement constraint tests
        pass
'''

    def generate_copilot_suggestions(self, report: Dict) -> List[str]:
        """Generate specific GitHub Copilot prompts for fixing issues"""
        prompts = []

        # High-priority fixes
        for suggestion in report['fix_suggestions']:
            if suggestion['priority'] == 'high':
                prompts.append(suggestion['copilot_prompt'])

        # Common patterns to implement
        if report['missing_tests']:
            prompts.append("# Generate comprehensive test suite for Records Management models")

        # Issue-specific prompts
        common_issues = {}
        for issue in report['test_issues']:
            issue_type = issue['type']
            common_issues[issue_type] = common_issues.get(issue_type, 0) + 1

        for issue_type, count in common_issues.items():
            if count > 2:
                prompts.append(f"# Fix {issue_type} in test files - add proper {issue_type.replace('_', ' ')}")

        return prompts

def main():
    """Main function to run test analysis"""
    import sys

    if len(sys.argv) > 1:
        rm_path = sys.argv[1]
    else:
        rm_path = 'records_management'

    analyzer = TestAnalyzer(rm_path)

    print("🔍 Smart Test Analysis and Fix Suggestions")
    print("=" * 50)

    try:
        report = analyzer.analyze_all_tests()

        print(f"📊 Analysis Results:")
        print(f"   • Test files analyzed: {len(report['test_files'])}")
        print(f"   • Missing tests: {len(report['missing_tests'])}")
        print(f"   • Issues found: {len(report['test_issues'])}")
        print(f"   • Fix suggestions: {len(report['fix_suggestions'])}")

        # Show missing tests
        if report['missing_tests']:
            print(f"\n❌ Missing Tests ({len(report['missing_tests'])}):")
            for missing in report['missing_tests'][:10]:  # Show first 10
                print(f"   • {missing}")
            if len(report['missing_tests']) > 10:
                print(f"   • ... and {len(report['missing_tests']) - 10} more")

        # Show critical issues
        critical_issues = [issue for issue in report['test_issues']
                          if issue.get('severity') == 'high']
        if critical_issues:
            print(f"\n🚨 Critical Issues ({len(critical_issues)}):")
            for issue in critical_issues[:5]:
                print(f"   • {issue['message']}")
                print(f"     Fix: {issue['suggestion']}")

        # Show fix suggestions
        if report['fix_suggestions']:
            print(f"\n💡 Top Fix Suggestions:")
            for suggestion in report['fix_suggestions'][:5]:
                print(f"   • {suggestion['action']} (Priority: {suggestion['priority']})")
                print(f"     Copilot Prompt: {suggestion['copilot_prompt']}")

        # Generate Copilot prompts
        copilot_prompts = analyzer.generate_copilot_suggestions(report)
        if copilot_prompts:
            print(f"\n🤖 GitHub Copilot Prompts:")
            for prompt in copilot_prompts[:5]:
                print(f"   • {prompt}")

        # Save detailed report
        report_file = 'test_analysis_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")
        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
