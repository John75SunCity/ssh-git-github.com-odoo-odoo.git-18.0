#!/usr/bin/env python3
"""
Report Manager for Records Management Module
Adds report files to manifest when needed, based on user requirements.
"""

import os
import sys
from pathlib import Path

class ReportManager:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.manifest_path = self.module_path / "__manifest__.py"
        self.report_dir = self.module_path / "report"

    def get_available_reports(self):
        """Get all available report files"""
        if not self.report_dir.exists():
            return []

        reports = []
        for file in self.report_dir.glob("*.xml"):
            reports.append(f"report/{file.name}")
        return sorted(reports)

    def get_current_manifest_reports(self):
        """Get reports currently in manifest"""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract data section
        start = content.find('"data": [')
        end = content.find('],\n    "demo":')
        if start == -1 or end == -1:
            return []

        data_section = content[start:end+1]
        reports = []

        for line in data_section.split('\n'):
            line = line.strip()
            if line.startswith('"report/') and line.endswith('",'):
                reports.append(line.strip('",'))

        return reports

    def find_reports_by_keyword(self, keyword):
        """Find reports containing a specific keyword"""
        available = self.get_available_reports()
        current = self.get_current_manifest_reports()

        # Find reports not yet in manifest that match keyword
        matching = []
        for report in available:
            if report not in current and keyword.lower() in report.lower():
                matching.append(report)

        return matching

    def add_reports_to_manifest(self, reports_to_add):
        """Add specified reports to manifest"""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the data section
        start = content.find('"data": [')
        end = content.find('],\n    "demo":')

        if start == -1 or end == -1:
            print("❌ Could not find data section in manifest")
            return False

        # Get current reports in data section
        data_section = content[start:end+1]
        current_reports = []

        for line in data_section.split('\n'):
            line = line.strip()
            if line.startswith('"report/') and line.endswith('",'):
                current_reports.append(line)

        # Add new reports after existing report entries
        new_data_section = data_section
        insert_position = len(current_reports) - 1  # Insert before last report

        for i, report in enumerate(reports_to_add):
            if i == 0 and current_reports:
                # Replace last report line with report + new one
                last_report = current_reports[-1]
                new_data_section = new_data_section.replace(
                    last_report,
                    f"{last_report}\n        \"{report}\","
                )
            else:
                # Add new report
                new_data_section = new_data_section.replace(
                    '],\n    "demo":',
                    f'        "{report}",\n    ],\n    "demo":'
                )

        # Update manifest
        new_content = content.replace(data_section, new_data_section)

        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Added {len(reports_to_add)} reports to manifest:")
        for report in reports_to_add:
            print(f"   + {report}")

        return True

    def interactive_add_reports(self):
        """Interactive mode to add reports"""
        print("🔍 Records Management Report Manager")
        print("=" * 50)

        available = self.get_available_reports()
        current = self.get_current_manifest_reports()

        print(f"📊 Total available reports: {len(available)}")
        print(f"📋 Currently in manifest: {len(current)}")
        print(f"📝 Available to add: {len(available) - len(current)}")

        if not available:
            print("❌ No report files found in report/ directory")
            return

        print("\n🔎 Search for reports by keyword (or 'all' for everything, 'quit' to exit):")
        while True:
            keyword = input("\nEnter keyword: ").strip()

            if keyword.lower() == 'quit':
                break

            if keyword.lower() == 'all':
                to_add = [r for r in available if r not in current]
            else:
                to_add = self.find_reports_by_keyword(keyword)

            if not to_add:
                print(f"❌ No reports found matching '{keyword}'")
                continue

            print(f"\n📋 Found {len(to_add)} reports:")
            for i, report in enumerate(to_add, 1):
                print(f"   {i}. {report}")

            response = input("\nAdd these reports to manifest? (y/N): ").lower().strip()
            if response.startswith('y'):
                if self.add_reports_to_manifest(to_add):
                    print("✅ Reports added successfully!")
                    break
                else:
                    print("❌ Failed to add reports")
            else:
                print("❌ Operation cancelled")

def main():
    if len(sys.argv) != 2:
        print("Usage: python report_manager.py <module_path>")
        print("Example: python report_manager.py /path/to/records_management")
        sys.exit(1)

    module_path = sys.argv[1]
    if not os.path.exists(module_path):
        print(f"❌ Module path does not exist: {module_path}")
        sys.exit(1)

    manager = ReportManager(module_path)
    manager.interactive_add_reports()

if __name__ == "__main__":
    main()
