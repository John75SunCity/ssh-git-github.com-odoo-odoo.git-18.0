#!/usr/bin/env python3
"""
Comprehensive Field Analysis Orchestrator
- Runs a suite of existing validators/audits to surface issues across the module.
- Emits a concise console summary and writes a JSON/MD report into this folder.

This is a lightweight wrapper so VS Code tasks can call a single entry point (python3).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "development-tools"
REPORTS = ROOT / "development-tools" / "analysis-reports"

# Tools to run (path, args)
COMMANDS = [
    [sys.executable, str(TOOLS / "validate_imports.py")],
    [sys.executable, str(TOOLS / "validate_xml.py")],
    [sys.executable, str(TOOLS / "analyze_module_integrity.py")],
    [sys.executable, str(TOOLS / "comprehensive_loading_order_audit.py")],
    [sys.executable, str(TOOLS / "related_field_audit.py")],
    [sys.executable, str(TOOLS / "verify_comodels_and_inverses.py")],
]


def run_cmd(cmd):
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        return {
            "cmd": cmd,
            "code": proc.returncode,
            "stdout": proc.stdout[-16000:],
            "stderr": proc.stderr[-16000:],
        }
    except FileNotFoundError as e:
        return {"cmd": cmd, "code": 127, "stdout": "", "stderr": str(e)}


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = []

    print("=== Comprehensive Field Analysis (wrapper) ===")
    print(f"Workspace: {ROOT}")

    for cmd in COMMANDS:
        name = Path(cmd[1]).name
        print(f"\n→ Running {name} ...")
        res = run_cmd(cmd)
        results.append({"tool": name, **res})
        status = "OK" if res["code"] == 0 else f"FAIL ({res['code']})"
        print(f"{name}: {status}")
        if res["stderr"].strip():
            print(f"stderr (tail):\n{res['stderr'].strip().splitlines()[-5:]}")

    # Aggregate quick summary
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tools": [
            {"tool": r["tool"], "code": r["code"]} for r in results
        ],
        "failures": [r for r in results if r["code"] != 0],
    }

    # Write JSON
    json_path = REPORTS / "scan_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)

    # Write MD
    md_path = REPORTS / "COMPREHENSIVE_FIELD_ANALYSIS_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Comprehensive Field Analysis Report\n\n")
        f.write(f"Generated: {summary['timestamp']}\n\n")
        for r in results:
            f.write(f"## {r['tool']}\n\n")
            f.write(f"Exit code: {r['code']}\n\n")
            if r["stdout"].strip():
                f.write("<details><summary>stdout (tail)</summary>\n\n")
                f.write("\n\n".join(r["stdout"].strip().splitlines()[-50:]))
                f.write("\n\n</details>\n\n")
            if r["stderr"].strip():
                f.write("<details><summary>stderr (tail)</summary>\n\n")
                f.write("\n\n".join(r["stderr"].strip().splitlines()[-50:]))
                f.write("\n\n</details>\n\n")

    print("\n=== Summary ===")
    for t in summary["tools"]:
        status = "OK" if t["code"] == 0 else ("WARN" if t["tool"] == "validate_xml.py" else "FAIL")
        print(f"- {t['tool']}: {status}")

    blocking = [r for r in summary["failures"] if r["tool"] != "validate_xml.py"]
    if blocking:
        print("\n❌ Some tools reported failures. See analysis-reports/COMPREHENSIVE_FIELD_ANALYSIS_REPORT.md for details.")
        sys.exit(1)

    if any(r["tool"] == "validate_xml.py" and r["code"] != 0 for r in results):
        print("\n⚠️ XML validation found issues (non-blocking). See analysis-reports/COMPREHENSIVE_FIELD_ANALYSIS_REPORT.md.")

    print("\n✅ Comprehensive analysis completed.")


if __name__ == "__main__":
    main()
