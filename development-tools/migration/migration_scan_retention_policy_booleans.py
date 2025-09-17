#!/usr/bin/env python3
"""
Migration Helper: Scan for deprecated Records Retention Policy boolean mirror fields.

Purpose:
    Identify legacy field usages (removed during refactor) in Python & XML files so integrators
    can update domains, search filters, and code logic to the new selection-based architecture.

Deprecated (removed) boolean mirrors:
    is_expired, is_under_legal_hold, is_approved, is_rejected, is_published, is_unpublished,
    is_locked, is_unlocked, is_archived_flag, is_pending_review, is_current, is_overdue,
    is_effective, is_ineffective, is_superseded

Replacement guidance:
    Expired / Overdue      -> review_state in ('expired','overdue') or specific value
    Approval flow          -> approval_state (draft|pending|approved|rejected|under_review)
    Publication flow       -> publication_state (draft|published|unpublished|effective|ineffective|superseded)
    Lifecycle lock/unlock  -> lifecycle_state (locked|unlocked|archived|active|deleted|purged|restored)
    Legal Hold             -> is_legal_hold (unchanged)

Output:
    Prints a table-like summary with file path, line number, matched token, and suggestion.

Usage:
    python3 development-tools/migration/migration_scan_retention_policy_booleans.py [--root records_management]

Exit codes:
    0 - Completed scan
    1 - Root path missing

NOTE: This script performs static grep-like scanning; manual validation still required.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from typing import List, Tuple

DEPRECATED = [
    'is_expired','is_under_legal_hold','is_approved','is_rejected','is_published','is_unpublished',
    'is_locked','is_unlocked','is_archived_flag','is_pending_review','is_current','is_overdue',
    'is_effective','is_ineffective','is_superseded'
]

SUGGESTIONS = {
    'is_expired': "review_state = 'expired'",
    'is_overdue': "review_state = 'overdue'",
    'is_pending_review': "review_state = 'pending_review'",
    'is_current': "review_state = 'current'",
    'is_under_legal_hold': "is_legal_hold",
    'is_approved': "approval_state = 'approved'",
    'is_rejected': "approval_state = 'rejected'",
    'is_published': "publication_state = 'published'",
    'is_unpublished': "publication_state = 'unpublished'",
    'is_effective': "publication_state = 'effective'",
    'is_ineffective': "publication_state = 'ineffective'",
    'is_superseded': "publication_state = 'superseded'",
    'is_locked': "lifecycle_state = 'locked'",
    'is_unlocked': "lifecycle_state = 'unlocked'",
    'is_archived_flag': "state = 'archived' or lifecycle_state = 'archived'",
}

FILE_PATTERNS = ('.py', '.xml')
TOKEN_RE = re.compile(r'\b(' + '|'.join(re.escape(tok) for tok in DEPRECATED) + r')\b')


def scan_file(path: str) -> List[Tuple[int, str, str]]:
    matches: List[Tuple[int, str, str]] = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for ln, line in enumerate(f, 1):
                for m in TOKEN_RE.finditer(line):
                    token = m.group(1)
                    suggestion = SUGGESTIONS.get(token, '')
                    matches.append((ln, token, suggestion))
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}", file=sys.stderr)
    return matches

def walk(root: str) -> List[Tuple[str, int, str, str]]:
    results: List[Tuple[str, int, str, str]] = []
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if fname.endswith(FILE_PATTERNS):
                full = os.path.join(dirpath, fname)
                file_matches = scan_file(full)
                for ln, token, suggestion in file_matches:
                    results.append((full, ln, token, suggestion))
    return results

def format_results(results: List[Tuple[str, int, str, str]]) -> str:
    if not results:
        return "No deprecated retention policy boolean usages found."
    # Determine column widths
    path_w = min(80, max(len(r[0]) for r in results))
    token_w = max(len(r[2]) for r in results)
    header = f"{'File'.ljust(path_w)}  {'Line':>5}  {'Token'.ljust(token_w)}  Suggestion"
    lines = [header, '-' * len(header)]
    for path, ln, token, suggestion in sorted(results):
        short_path = path[-path_w:]
        lines.append(f"{short_path.ljust(path_w)}  {ln:5}  {token.ljust(token_w)}  {suggestion}")
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser(description="Scan for deprecated retention policy boolean usages.")
    ap.add_argument('--root', default='records_management', help='Root directory to scan (default: records_management)')
    args = ap.parse_args()
    root = args.root
    if not os.path.isdir(root):
        print(f"Root directory not found: {root}", file=sys.stderr)
        sys.exit(1)
    results = walk(root)
    print(format_results(results))
    sys.exit(0)

if __name__ == '__main__':
    main()
