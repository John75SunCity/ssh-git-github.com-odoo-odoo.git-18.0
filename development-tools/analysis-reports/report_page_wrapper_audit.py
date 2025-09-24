"""Report Page Wrapper Audit
=================================

Purpose:
    Diagnose excessive <div class="page"> wrappers that might inflate
    page container counts in Odoo report rendering tests (e.g., base test
    expecting 3 page boxes but encountering a larger number such as 21).

Scope:
    Scans the records_management/report/ directory for QWeb XML templates
    and counts occurrences of:
        - <div class="page"> wrappers
        - t-call="web.external_layout"
        - t-call="web.html_container"

    It also flags templates that:
        * Omit both web.html_container and web.external_layout calls
        * Have multiple page wrappers inside a single template
        * Contain nested loops with page wrappers which can multiply output

Usage:
    python3 development-tools/analysis-reports/report_page_wrapper_audit.py

Output:
    Human-readable summary + JSON diagnostics (copy/paste friendly) to stdout.

Notes:
    This does NOT render reports; it is a static heuristic scan to quickly
    highlight structural anomalies. Rendering-level leakage or inheritance
    issues still require runtime validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RE_PAGE_DIV = re.compile(r'<div\s+class=["\"]page["\"][^>]*>', re.IGNORECASE)
RE_PAGE_SPAN = re.compile(r'<span\s+class=["\"]page["\"][^>]*>', re.IGNORECASE)
RE_EXTERNAL_LAYOUT = re.compile(r't-call=\"web.external_layout\"')
RE_HTML_CONTAINER = re.compile(r't-call=\"web.html_container\"')
RE_TEMPLATE_START = re.compile(r'<template\s+[^>]*id=\"([^"\"]+)\"')
RE_FOREACH = re.compile(r't-foreach=')

ROOT = Path(__file__).resolve().parents[2]  # repo root
REPORT_DIR = ROOT / 'records_management' / 'report'


def iter_report_files():
    for path in sorted(REPORT_DIR.glob('*.xml')):
        # Skip obvious placeholder or legacy marker files if needed later
        yield path


def analyze_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    page_divs = RE_PAGE_DIV.findall(text)
    page_spans = RE_PAGE_SPAN.findall(text)
    external_calls = RE_EXTERNAL_LAYOUT.findall(text)
    html_container_calls = RE_HTML_CONTAINER.findall(text)
    templates = RE_TEMPLATE_START.findall(text)
    foreach_count = len(RE_FOREACH.findall(text))

    issues = []
    if not external_calls and not html_container_calls:
        # Some simple / lightweight templates may intentionally bypass wrappers,
        # but for PDF/HTML reports this is usually unintentional.
        issues.append('NO_LAYOUT_CALL')
    if len(page_divs) > 1:
        issues.append('MULTIPLE_PAGE_DIVS')
    if foreach_count > 1 and page_divs:
        issues.append('NESTED_FOREACH_WITH_PAGE')
    if external_calls and not page_divs:
        # Usually each external_layout call wraps a page div.
        issues.append('EXTERNAL_WITHOUT_PAGE_DIV')

    return {
        'file': str(path.relative_to(ROOT)),
        'templates': templates,
        'page_div_count': len(page_divs),
        'page_span_count': len(page_spans),
        'external_layout_calls': len(external_calls),
        'html_container_calls': len(html_container_calls),
        'foreach_count': foreach_count,
        'issues': issues,
    }


def main():
    results = [analyze_file(p) for p in iter_report_files()]

    total_page_divs = sum(r['page_div_count'] for r in results)
    total_external = sum(r['external_layout_calls'] for r in results)
    total_html_container = sum(r['html_container_calls'] for r in results)

    # Highlight top offenders (multiple page divs)
    multi_page = [r for r in results if r['page_div_count'] > 1]
    no_layout = [r for r in results if 'NO_LAYOUT_CALL' in r['issues']]

    print('\n=== REPORT PAGE WRAPPER AUDIT ===')
    print(f'Scanned files: {len(results)}')
    print(f'Total <div class="page"> occurrences: {total_page_divs}')
    print(f'Total external_layout calls: {total_external}')
    print(f'Total html_container calls: {total_html_container}')
    print('\n-- Files with multiple page divs --')
    if multi_page:
        for r in multi_page:
            print(f"  {r['file']} -> page_divs={r['page_div_count']} templates={r['templates']}")
    else:
        print('  (none)')

    print('\n-- Files missing both web.html_container & web.external_layout --')
    if no_layout:
        for r in no_layout:
            print(f"  {r['file']} (page_divs={r['page_div_count']})")
    else:
        print('  (none)')

    print('\n-- JSON Diagnostics (copy/paste) --')
    print(json.dumps(results, indent=2))
    print('\nInterpretation Guidelines:')
    print('  * MULTIPLE_PAGE_DIVS: Consider splitting into separate templates or ensuring only one page wrapper per rendered doc iteration.')
    print('  * NO_LAYOUT_CALL: Add t-call="web.html_container" + t-call="web.external_layout" for standard wrapping to avoid leakage.')
    print('  * NESTED_FOREACH_WITH_PAGE: Multiple loops with page wrappers can multiply total page counts unexpectedly.')
    print('  * EXTERNAL_WITHOUT_PAGE_DIV: External layout used but missing explicit page wrapper (may rely on inherited structure).')


if __name__ == '__main__':
    main()
