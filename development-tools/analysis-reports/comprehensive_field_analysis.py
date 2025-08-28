#!/usr/bin/env python3
"""
Enhanced Comprehensive Field Analysis Script
===========================================

Advanced orchestrator for running validation tools with improved error handling,
parallel execution, and intelligent recommendations.

Features:
- Parallel execution with configurable worker threads
- Comprehensive error categorization (blocking vs non-blocking)
- Intelligent recommendation engine
- Enhanced markdown reporting with executive summary
- JSON export for programmatic access
- Performance metrics and timeout handling
- Tool metadata-driven configuration

Author: GitHub Copilot
Version: 2.0.0
Date: 2025-01-27
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

# Add the workspace root to Python path
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

@dataclass
class ToolResult:
    """Container for tool execution results"""
    name: str
    category: str
    success: bool
    return_code: int
    stdout: str
    stderr: str
    execution_time: float
    error_message: Optional[str] = None
    is_blocking: bool = False

@dataclass
class AnalysisSummary:
    """Summary of analysis results"""
    total_tools: int
    successful_tools: int
    failed_tools: int
    blocking_issues: int
    non_blocking_issues: int
    total_execution_time: float
    timestamp: str

# Tool configuration with metadata
TOOL_CONFIG = {
    'validate_imports': {
        'script': 'development-tools/validate_imports.py',
        'category': 'Import Validation',
        'description': 'Validates Python import statements and module dependencies',
        'is_blocking': True,
        'timeout': 30
    },
    'validate_xml': {
        'script': 'development-tools/validate_xml.py',
        'category': 'XML Validation',
        'description': 'Validates XML view files and data files',
        'is_blocking': True,
        'timeout': 45
    },
    'validate_security': {
        'script': 'development-tools/validate_security.py',
        'category': 'Security Validation',
        'description': 'Validates security rules and access permissions',
        'is_blocking': True,
        'timeout': 30
    },
    'validate_models': {
        'script': 'development-tools/validate_models.py',
        'category': 'Model Validation',
        'description': 'Validates Odoo model definitions and field configurations',
        'is_blocking': True,
        'timeout': 60
    },
    'validate_views': {
        'script': 'development-tools/validate_views.py',
        'category': 'View Validation',
        'description': 'Validates view definitions and field references',
        'is_blocking': True,
        'timeout': 45
    },
    'check_dependencies': {
        'script': 'development-tools/check_dependencies.py',
        'category': 'Dependency Analysis',
        'description': 'Analyzes module dependencies and relationships',
        'is_blocking': False,
        'timeout': 30
    },
    'validate_translations': {
        'script': 'development-tools/validate_translations.py',
        'category': 'Translation Validation',
        'description': 'Validates translation patterns and i18n compliance',
        'is_blocking': False,
        'timeout': 20
    },
    'performance_check': {
        'script': 'development-tools/performance_check.py',
        'category': 'Performance Analysis',
        'description': 'Analyzes performance bottlenecks and optimization opportunities',
        'is_blocking': False,
        'timeout': 40
    }
}

class EnhancedFieldAnalyzer:
    """Enhanced field analysis orchestrator with parallel execution"""

    def __init__(self, workspace_root: Path, max_workers: int = 4):
        self.workspace_root = workspace_root
        self.max_workers = max_workers
        self.results: List[ToolResult] = []
        self.start_time = time.time()

    def run_tool(self, tool_name: str, config: Dict[str, Any]) -> ToolResult:
        """Execute a single validation tool"""
        script_path = self.workspace_root / config['script']

        if not script_path.exists():
            return ToolResult(
                name=tool_name,
                category=config['category'],
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Script not found: {script_path}",
                execution_time=0.0,
                error_message=f"Script not found: {script_path}",
                is_blocking=config['is_blocking']
            )

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=config['timeout'],
                cwd=self.workspace_root
            )

            execution_time = time.time() - start_time

            return ToolResult(
                name=tool_name,
                category=config['category'],
                success=result.returncode == 0,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                is_blocking=config['is_blocking']
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ToolResult(
                name=tool_name,
                category=config['category'],
                success=False,
                return_code=-2,
                stdout="",
                stderr=f"Tool execution timed out after {config['timeout']} seconds",
                execution_time=execution_time,
                error_message=f"Timeout: {config['timeout']}s",
                is_blocking=config['is_blocking']
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                name=tool_name,
                category=config['category'],
                success=False,
                return_code=-3,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                error_message=str(e),
                is_blocking=config['is_blocking']
            )

    def run_analysis(self) -> List[ToolResult]:
        """Run all validation tools in parallel"""
        print("🚀 Starting Enhanced Comprehensive Field Analysis")
        print(f"📊 Running {len(TOOL_CONFIG)} validation tools with {self.max_workers} workers")
        print("=" * 80)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tools for execution
            future_to_tool = {
                executor.submit(self.run_tool, tool_name, config): (tool_name, config)
                for tool_name, config in TOOL_CONFIG.items()
            }

            # Process completed tools
            for future in as_completed(future_to_tool):
                tool_name, config = future_to_tool[future]
                try:
                    result = future.result()
                    self.results.append(result)

                    # Print immediate status
                    status = "✅" if result.success else "❌"
                    blocking = "🔴 BLOCKING" if result.is_blocking and not result.success else ""
                    print(f"  {status} {result.name} ({result.execution_time:.2f}s) {blocking}")
                except Exception as e:
                    print(f"❌ Error processing {tool_name}: {e}")

        # Sort results by category and success status
        self.results.sort(key=lambda x: (x.category, not x.success, x.name))

        return self.results

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze results and generate insights"""
        total_tools = len(self.results)
        successful_tools = sum(1 for r in self.results if r.success)
        failed_tools = total_tools - successful_tools

        blocking_failures = sum(1 for r in self.results if not r.success and r.is_blocking)
        non_blocking_failures = sum(1 for r in self.results if not r.success and not r.is_blocking)

        # Group by category
        category_stats = {}
        for result in self.results:
            if result.category not in category_stats:
                category_stats[result.category] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'blocking_failures': 0,
                    'tools': []
                }

            category_stats[result.category]['total'] += 1
            category_stats[result.category]['tools'].append(result)

            if result.success:
                category_stats[result.category]['successful'] += 1
            else:
                category_stats[result.category]['failed'] += 1
                if result.is_blocking:
                    category_stats[result.category]['blocking_failures'] += 1

        return {
            'summary': AnalysisSummary(
                total_tools=total_tools,
                successful_tools=successful_tools,
                failed_tools=failed_tools,
                blocking_issues=blocking_failures,
                non_blocking_issues=non_blocking_failures,
                total_execution_time=time.time() - self.start_time,
                timestamp=datetime.now().isoformat()
            ),
            'categories': category_stats,
            'results': self.results
        }

    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate intelligent recommendations based on analysis results"""
        recommendations = []

        summary = analysis['summary']
        categories = analysis['categories']

        # Overall health assessment
        if summary.blocking_issues > 0:
            recommendations.append("🚨 **CRITICAL**: Address all blocking issues before deployment")
        elif summary.failed_tools > 0:
            recommendations.append("⚠️ **WARNING**: Non-blocking issues should be addressed for optimal performance")
        else:
            recommendations.append("✅ **EXCELLENT**: All validation checks passed successfully")

        # Category-specific recommendations
        for category, stats in categories.items():
            if stats['blocking_failures'] > 0:
                failed_tools = [r.name for r in stats['tools'] if not r.success and r.is_blocking]
                recommendations.append(f"🔧 **{category}**: Fix blocking issues in {', '.join(failed_tools)}")

            elif stats['failed'] > 0:
                failed_tools = [r.name for r in stats['tools'] if not r.success]
                recommendations.append(f"📈 **{category}**: Consider optimizing {', '.join(failed_tools)}")

        # Performance recommendations
        if summary.total_execution_time > 120:
            recommendations.append("⚡ **PERFORMANCE**: Consider increasing max_workers for faster analysis")

        # Tool-specific recommendations
        for result in analysis['results']:
            if not result.success:
                if "timeout" in str(result.error_message).lower():
                    recommendations.append(f"⏱️ **TIMEOUT**: Increase timeout for {result.name} or optimize the tool")
                elif "not found" in str(result.error_message).lower():
                    recommendations.append(f"📁 **MISSING**: Create or locate {result.name} script")

        return recommendations

    def export_json(self, analysis: Dict[str, Any], output_path: Path) -> None:
        """Export analysis results to JSON"""
        # Convert dataclasses to dictionaries
        json_data = {
            'summary': asdict(analysis['summary']),
            'categories': {},
            'recommendations': self.generate_recommendations(analysis),
            'results': [asdict(result) for result in analysis['results']]
        }

        # Process categories
        for category, stats in analysis['categories'].items():
            json_data['categories'][category] = {
                'total': stats['total'],
                'successful': stats['successful'],
                'failed': stats['failed'],
                'blocking_failures': stats['blocking_failures'],
                'tools': [asdict(tool) for tool in stats['tools']]
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

    def format_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive markdown report"""
        summary = analysis['summary']
        categories = analysis['categories']
        recommendations = self.generate_recommendations(analysis)

        report = f"""# 🔍 Enhanced Comprehensive Field Analysis Report

**Generated on:** {summary.timestamp}
**Analysis Duration:** {summary.total_execution_time:.2f} seconds
**Tools Executed:** {summary.total_tools}

## 📊 Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Total Tools** | {summary.total_tools} | - |
| **Successful** | {summary.successful_tools} | {'✅' if summary.successful_tools == summary.total_tools else '⚠️'} |
| **Failed** | {summary.failed_tools} | {'❌' if summary.failed_tools > 0 else '✅'} |
| **Blocking Issues** | {summary.blocking_issues} | {'🔴' if summary.blocking_issues > 0 else '✅'} |
| **Non-blocking Issues** | {summary.non_blocking_issues} | {'⚠️' if summary.non_blocking_issues > 0 else '✅'} |

## 🎯 Recommendations

{chr(10).join(f"- {rec}" for rec in recommendations)}

## 📈 Category Breakdown

"""

        for category, stats in categories.items():
            success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0

            report += f"""### {category}

**Success Rate:** {success_rate:.1f}% ({stats['successful']}/{stats['total']})
**Blocking Failures:** {stats['blocking_failures']}

| Tool | Status | Execution Time | Details |
|------|--------|----------------|---------|
"""

            for result in stats['tools']:
                status = "✅ PASS" if result.success else "❌ FAIL"
                if not result.success and result.is_blocking:
                    status = "🔴 BLOCKING"

                error_info = ""
                if not result.success and result.error_message:
                    error_info = f" - {result.error_message[:50]}..."

                report += f"| {result.name} | {status} | {result.execution_time:.2f}s | {error_info} |\n"

            report += "\n"

        # Detailed results section
        report += """## 🔧 Detailed Results

### ✅ Successful Tools

"""

        successful_results = [r for r in analysis['results'] if r.success]
        for result in successful_results:
            report += f"""<details>
<summary>{result.name} - ✅ PASSED ({result.execution_time:.2f}s)</summary>

**Category:** {result.category}
**Execution Time:** {result.execution_time:.2f} seconds

```
{result.stdout[-500:] if result.stdout else "No output"}
```

</details>

"""

        # Failed tools section
        failed_results = [r for r in analysis['results'] if not r.success]
        if failed_results:
            report += """

### ❌ Failed Tools

"""

            for result in failed_results:
                blocking_indicator = "🔴 **BLOCKING**" if result.is_blocking else "⚠️ **NON-BLOCKING**"

                report += f"""<details>
<summary>{result.name} - ❌ FAILED ({result.execution_time:.2f}s) {blocking_indicator}</summary>

**Category:** {result.category}
**Return Code:** {result.return_code}
**Execution Time:** {result.execution_time:.2f} seconds

**Error Message:**
```
{result.error_message or "No error message"}
```

**Standard Error:**
```
{result.stderr[-1000:] if result.stderr else "No stderr output"}
```

**Standard Output:**
```
{result.stdout[-1000:] if result.stdout else "No stdout output"}
```

</details>

"""

        # Footer
        report += f"""

---

**Report generated by Enhanced Comprehensive Field Analysis v2.0.0**
**Analysis completed in {summary.total_execution_time:.2f} seconds**
**Parallel execution with {self.max_workers} workers**
"""

        return report

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent.parent

    # Initialize analyzer
    analyzer = EnhancedFieldAnalyzer(workspace_root, max_workers=4)

    try:
        # Run analysis
        results = analyzer.run_analysis()

        # Analyze results
        analysis = analyzer.analyze_results()

        # Generate reports
        markdown_report = analyzer.format_markdown_report(analysis)

        # Save reports
        reports_dir = workspace_root / "development-tools" / "analysis-reports"
        reports_dir.mkdir(exist_ok=True)

        # Markdown report
        md_path = reports_dir / "ENHANCED_COMPREHENSIVE_FIELD_ANALYSIS_REPORT.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        # JSON export
        json_path = reports_dir / "enhanced_analysis_results.json"
        analyzer.export_json(analysis, json_path)

        # Print summary to console
        summary = analysis['summary']
        print("\n" + "=" * 80)
        print("📊 ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"✅ Successful: {summary.successful_tools}/{summary.total_tools}")
        print(f"❌ Failed: {summary.failed_tools}/{summary.total_tools}")
        print(f"🔴 Blocking Issues: {summary.blocking_issues}")
        print(f"⚠️ Non-blocking Issues: {summary.non_blocking_issues}")
        print(f"⏱️ Total Execution Time: {summary.total_execution_time:.2f}s")
        print(f"📄 Reports saved to: {reports_dir}")
        print(f"   - Markdown: {md_path.name}")
        print(f"   - JSON: {json_path.name}")

        # Exit with appropriate code
        if summary.blocking_issues > 0:
            print("\n🔴 BLOCKING ISSUES DETECTED - FIX REQUIRED BEFORE DEPLOYMENT")
            sys.exit(1)
        elif summary.failed_tools > 0:
            print("\n⚠️ NON-BLOCKING ISSUES DETECTED - CONSIDER FIXING")
            sys.exit(0)
        else:
            print("\n✅ ALL VALIDATION CHECKS PASSED")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
