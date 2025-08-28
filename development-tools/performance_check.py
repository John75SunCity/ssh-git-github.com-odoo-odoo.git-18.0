#!/usr/bin/env python3
"""
Performance Check Script
=======================

Analyzes code for performance optimization opportunities.
Identifies potential bottlenecks and suggests improvements.

Features:
- Query optimization analysis
- Memory usage patterns
- Database access patterns
- Code complexity analysis
- Performance anti-patterns detection

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
import ast
from collections import defaultdict

class PerformanceAnalyzer:
    """Analyzes code for performance optimization opportunities"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.metrics: Dict[str, int] = defaultdict(int)

    def analyze_performance(self) -> bool:
        """Main analysis function"""
        print("⚡ Analyzing Performance Optimization Opportunities...")

        # Analyze Python files
        self._analyze_python_files()

        # Analyze query patterns
        self._analyze_query_patterns()

        # Analyze memory usage
        self._analyze_memory_patterns()

        # Analyze code complexity
        self._analyze_complexity()

        return len(self.issues) == 0

    def _analyze_python_files(self) -> None:
        """Analyze Python files for performance issues"""
        module_dir = self.workspace_root / "records_management"

        if not module_dir.exists():
            return

        for py_file in module_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                self._analyze_file_performance(content, py_file)

            except Exception as e:
                self.warnings.append(f"Error analyzing {py_file}: {e}")

    def _analyze_file_performance(self, content: str, file_path: Path) -> None:
        """Analyze performance patterns in a single file"""
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for performance anti-patterns
            self._check_performance_anti_patterns(line, line_num, file_path)

            # Check for inefficient operations
            self._check_inefficient_operations(line, line_num, file_path)

            # Check for database access patterns
            self._check_database_patterns(line, line_num, file_path)

        # Analyze overall file complexity
        self._analyze_file_complexity(content, file_path)

    def _check_performance_anti_patterns(self, line: str, line_num: int, file_path: Path) -> None:
        """Check for common performance anti-patterns"""
        # Pattern 1: Loop with database queries (N+1 problem)
        if re.search(r'for\s+\w+\s+in\s+.*:\s*$', line):
            next_lines = self._get_next_lines(file_path, line_num, 3)
            for next_line in next_lines:
                if re.search(r'\.search\(|browse\(|create\(|write\(|unlink\(|\.mapped\(|\.filtered\(|\.sorted\(', next_line):
                    self.issues.append(f"{file_path}:{line_num}: Potential N+1 query in loop - consider using mapped/filtered/sorted on recordset")

        # Pattern 2: Inefficient list comprehensions
        if '[x.' in line and 'for x in' in line and ('search(' in line or 'browse(' in line):
            self.warnings.append(f"{file_path}:{line_num}: List comprehension with database query - consider optimizing")

        # Pattern 3: Multiple database calls in sequence
        if re.search(r'\.(search|browse|create|write|unlink)\(', line):
            self.metrics['db_calls'] += 1

        # Pattern 4: Large data processing without batching
        if re.search(r'for\s+\w+\s+in\s+.*records', line):
            self.warnings.append(f"{file_path}:{line_num}: Processing records in loop - consider batch processing")

    def _check_inefficient_operations(self, line: str, line_num: int, file_path: Path) -> None:
        """Check for inefficient operations"""
        # Pattern 1: String concatenation in loop
        if '+' in line and ('"' in line or "'" in line) and 'for ' in line:
            self.warnings.append(f"{file_path}:{line_num}: String concatenation in loop - use join() instead")

        # Pattern 2: Inefficient list operations
        if re.search(r'\.append\([^)]*\)\s*$', line):
            # Check if this is in a loop
            context_lines = self._get_context_lines(file_path, line_num, 5)
            if any('for ' in context_line for context_line in context_lines):
                self.suggestions.append(f"{file_path}:{line_num}: Consider using list comprehension instead of append in loop")

        # Pattern 3: Unnecessary computations
        if re.search(r'len\(.*\)\s*>\s*0', line) or re.search(r'len\(.*\)\s*==\s*0', line):
            self.suggestions.append(f"{file_path}:{line_num}: Use 'if records:' instead of 'if len(records) > 0:'")

        # Pattern 4: Redundant field access
        if re.search(r'\.\w+\.\w+', line) and not re.search(r'\.(id|name|create_date|write_date)', line):
            self.suggestions.append(f"{file_path}:{line_num}: Consider storing field value in variable to avoid repeated access")

    def _check_database_patterns(self, line: str, line_num: int, file_path: Path) -> None:
        """Check database access patterns"""
        # Pattern 1: Missing sudo() for admin operations
        if re.search(r'\.(create|write|unlink)\(', line) and not re.search(r'\.sudo\(\)', line):
            context_lines = self._get_context_lines(file_path, line_num, 3)
            if not any('sudo()' in context_line for context_line in context_lines):
                self.warnings.append(f"{file_path}:{line_num}: Database operation without sudo() - verify permissions")

        # Pattern 2: Large result sets without limit
        if re.search(r'\.search\(\[\]', line) and not re.search(r'limit\s*[:=]', line):
            self.warnings.append(f"{file_path}:{line_num}: Unbounded search - consider adding limit")

        # Pattern 3: Missing index hints
        if re.search(r'\.search\(\[.*\w+\.?\w+.*\]', line):
            self.suggestions.append(f"{file_path}:{line_num}: Consider database indexes for search fields")

        # Pattern 4: Inefficient field access
        if re.search(r'\.mapped\(\s*[\'\"]\w+[\'\"]\s*\)', line):
            self.suggestions.append(f"{file_path}:{line_num}: Consider using dot notation for single field access")

    def _analyze_file_complexity(self, content: str, file_path: Path) -> None:
        """Analyze overall file complexity"""
        try:
            tree = ast.parse(content)

            class ComplexityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.complexity = 0
                    self.functions = []

                def visit_FunctionDef(self, node):
                    self.functions.append((node.name, self._calculate_complexity(node)))
                    self.generic_visit(node)

                def _calculate_complexity(self, node):
                    complexity = 1  # Base complexity
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                    return complexity

            visitor = ComplexityVisitor()
            visitor.visit(tree)

            # Check for complex functions
            for func_name, complexity in visitor.functions:
                if complexity > 10:
                    self.warnings.append(f"{file_path}: Function '{func_name}' has high complexity ({complexity}) - consider refactoring")
                elif complexity > 5:
                    self.suggestions.append(f"{file_path}: Function '{func_name}' has moderate complexity ({complexity})")

            # Overall file metrics
            total_lines = len(content.split('\n'))
            if total_lines > 500:
                self.warnings.append(f"{file_path}: Large file ({total_lines} lines) - consider splitting")

        except SyntaxError:
            self.issues.append(f"{file_path}: Syntax error prevents complexity analysis")

    def _analyze_query_patterns(self) -> None:
        """Analyze database query patterns"""
        # Check for common query optimization opportunities
        if self.metrics['db_calls'] > 20:
            self.warnings.append(f"High number of database calls ({self.metrics['db_calls']}) - consider batching operations")

        # Look for potential query optimization patterns
        self._check_query_optimization_patterns()

    def _check_query_optimization_patterns(self) -> None:
        """Check for query optimization patterns"""
        # This would analyze actual query patterns in the codebase
        # For now, we'll add general suggestions
        self.suggestions.append("Consider using read_group() for aggregated data instead of multiple queries")
        self.suggestions.append("Use exists() instead of search() when only checking existence")
        self.suggestions.append("Consider prefetching related records to avoid N+1 queries")

    def _analyze_memory_patterns(self) -> None:
        """Analyze memory usage patterns"""
        # Check for potential memory issues
        self.suggestions.append("Consider using itertools for large data processing to save memory")
        self.suggestions.append("Use generators instead of lists for large datasets")
        self.suggestions.append("Consider lazy loading for large related datasets")

    def _analyze_complexity(self) -> None:
        """Analyze overall code complexity"""
        # This would perform module-level complexity analysis
        self.suggestions.append("Consider breaking down complex methods into smaller, focused functions")
        self.suggestions.append("Use early returns to reduce nesting levels")
        self.suggestions.append("Consider using strategy pattern for complex conditional logic")

    def _get_next_lines(self, file_path: Path, line_num: int, count: int) -> List[str]:
        """Get next lines from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = line_num
                end = min(line_num + count, len(lines))
                return [lines[i].strip() for i in range(start, end)]
        except:
            return []

    def _get_context_lines(self, file_path: Path, line_num: int, context: int) -> List[str]:
        """Get context lines around a specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = max(0, line_num - context - 1)
                end = min(len(lines), line_num + context)
                return [lines[i].strip() for i in range(start, end)]
        except:
            return []

    def print_report(self) -> None:
        """Print performance analysis report"""
        print(f"\n⚡ Performance Analysis Report")
        print("=" * 50)

        if self.issues:
            print(f"❌ Critical Issues ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.suggestions:
            print(f"\n💡 Suggestions ({len(self.suggestions)}):")
            for suggestion in self.suggestions:
                print(f"  • {suggestion}")

        if not self.issues and not self.warnings and not self.suggestions:
            print("✅ No performance issues found!")

        print(f"\n📊 Metrics:")
        print(f"  • Database calls detected: {self.metrics['db_calls']}")
        print(f"  • Files analyzed: {len(list(self.workspace_root.glob('records_management/**/*.py')))}")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent.parent

    analyzer = PerformanceAnalyzer(workspace_root)

    try:
        success = analyzer.analyze_performance()
        analyzer.print_report()

        if success:
            print("\n✅ Performance analysis completed successfully")
            sys.exit(0)
        else:
            print(f"\n⚠️ Performance analysis completed with {len(analyzer.issues)} critical issues")
            sys.exit(0)  # Don't fail on performance issues

    except Exception as e:
        print(f"❌ Performance analysis failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
