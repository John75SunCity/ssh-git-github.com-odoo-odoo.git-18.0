#!/usr/bin/env python3
"""
Grok-4 with cached/indexed codebase for faster responses.
Creates a persistent index file that's loaded once instead of scanning files every time.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# Configuration
XAI_API_KEY = os.environ.get("XAI_API_KEY")
if not XAI_API_KEY:
    print("❌ Error: XAI_API_KEY environment variable not set")
    sys.exit(1)

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# Paths
WORKSPACE_ROOT = Path.home() / "Documents/ssh-git-github.com-odoo-odoo.git-18.0"
INDEX_FILE = Path.home() / ".github/agents/grok-index.json"

def get_file_mtime(filepath):
    """Get modification time of a file"""
    return os.path.getmtime(filepath)

def should_rebuild_index():
    """Check if index needs rebuilding"""
    if not INDEX_FILE.exists():
        return True
    
    index_mtime = get_file_mtime(INDEX_FILE)
    
    # ONLY check records_management and records_management_fsm directories
    target_dirs = [
        WORKSPACE_ROOT / "records_management",
        WORKSPACE_ROOT / "records_management_fsm"
    ]
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for pattern in ["**/*.py", "**/*.xml", "**/*.csv"]:
            for filepath in target_dir.glob(pattern):
                if "/__pycache__/" in str(filepath) or "/.git/" in str(filepath):
                    continue
                if get_file_mtime(filepath) > index_mtime:
                    return True
    
    return False

def build_index():
    """Build/rebuild the codebase index - ONLY records_management and records_management_fsm"""
    print("📚 Building codebase index (records_management + records_management_fsm only)...")
    
    index = {
        "built_at": datetime.now().isoformat(),
        "files": {},
        "summary": {
            "total_files": 0,
            "total_chars": 0,
            "models": [],
            "demos": [],
            "views": [],
            "controllers": [],
            "wizards": [],
            "security": []
        }
    }
    
    # Index ALL files from both target directories
    target_dirs = ["records_management", "records_management_fsm"]
    
    for target_dir in target_dirs:
        dir_path = WORKSPACE_ROOT / target_dir
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {target_dir}")
            continue
        
        # Index all relevant file types
        patterns = [
            "**/*.py",      # All Python files
            "**/*.xml",     # All XML files  
            "**/*.csv",     # Security files
            "**/*.js",      # JavaScript files
            "**/*.scss",    # Stylesheets
            "**/*.md",      # Documentation
            "__manifest__.py",  # Manifest
        ]
        
        for pattern in patterns:
            for filepath in dir_path.glob(pattern):
                # Skip pycache, git, and other non-source files
                path_str = str(filepath)
                if any(skip in path_str for skip in ["/__pycache__/", "/.git/", ".pyc", ".pyo"]):
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    rel_path = str(filepath.relative_to(WORKSPACE_ROOT))
                    index["files"][rel_path] = {
                        "content": content,
                        "size": len(content),
                        "mtime": get_file_mtime(filepath)
                    }
                    
                    index["summary"]["total_files"] += 1
                    index["summary"]["total_chars"] += len(content)
                    
                    # Categorize files
                    if "/models/" in rel_path and rel_path.endswith(".py"):
                        index["summary"]["models"].append(rel_path)
                    elif "/demo/" in rel_path and rel_path.endswith(".xml"):
                        index["summary"]["demos"].append(rel_path)
                    elif "/views/" in rel_path and rel_path.endswith(".xml"):
                        index["summary"]["views"].append(rel_path)
                    elif "/controllers/" in rel_path and rel_path.endswith(".py"):
                        index["summary"]["controllers"].append(rel_path)
                    elif "/wizards/" in rel_path:
                        index["summary"]["wizards"].append(rel_path)
                    elif "/security/" in rel_path:
                        index["summary"]["security"].append(rel_path)
                        
                except Exception as e:
                    print(f"⚠️  Skipping {filepath}: {e}")
    
    # Save index
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Index built: {index['summary']['total_files']} files, {index['summary']['total_chars']:,} chars")
    print(f"  - Models: {len(index['summary']['models'])}")
    print(f"  - Views: {len(index['summary']['views'])}")
    print(f"  - Demos: {len(index['summary']['demos'])}")
    print(f"  - Controllers: {len(index['summary']['controllers'])}")
    print(f"  - Wizards: {len(index['summary']['wizards'])}")
    print(f"  - Security: {len(index['summary']['security'])}")
    
    return index

def load_index():
    """Load the codebase index"""
    if should_rebuild_index():
        return build_index()
    
    print("📖 Loading cached index...")
    with open(INDEX_FILE, 'r') as f:
        index = json.load(f)
    
    print(f"✓ Loaded: {index['summary']['total_files']} files, {index['summary']['total_chars']:,} chars")
    return index

def build_context(index, focus_files=None):
    """Build context string from index"""
    lines = []
    
    if focus_files:
        # Include only specific files
        for rel_path in focus_files:
            if rel_path in index["files"]:
                file_data = index["files"][rel_path]
                lines.append(f"\n{'='*80}\nFile: {rel_path}\n{'='*80}\n")
                lines.append(file_data["content"])
    else:
        # Smart selection: include ALL files but prioritize core ones
        # Priority order: models, demos, views, controllers, wizards, security
        priority_order = [
            index["summary"]["models"],
            index["summary"]["demos"],
            index["summary"]["views"],
            index["summary"]["controllers"],
            index["summary"]["wizards"],
            index["summary"]["security"],
        ]
        
        # Flatten priority list
        priority_files = []
        for file_list in priority_order:
            priority_files.extend(file_list)
        
        # Add any remaining files not in categories
        all_files = sorted(index["files"].keys())
        for rel_path in all_files:
            if rel_path not in priority_files:
                priority_files.append(rel_path)
        
        # Build context from all files
        for rel_path in priority_files:
            if rel_path in index["files"]:
                file_data = index["files"][rel_path]
                lines.append(f"\n{'='*80}\nFile: {rel_path}\n{'='*80}\n")
                lines.append(file_data["content"])
    
    context = "\n".join(lines)
    
    # Safety check: if still too large, truncate (keep priority files)
    max_chars = 450000  # ~112k tokens (safe for 131k limit with room for response)
    if len(context) > max_chars:
        print(f"⚠️  Context too large ({len(context):,} chars), truncating to {max_chars:,} chars")
        context = context[:max_chars] + f"\n\n... [Truncated: total {len(context):,} chars, showing first {max_chars:,}]"
    
    return context

def ask_grok(question, index, focus_files=None):
    """Ask Grok-4 with indexed context"""
    context = build_context(index, focus_files)
    
    messages = [
        {
            "role": "system",
            "content": f"""You are analyzing the Odoo 19 Records Management codebase. 

CODEBASE CONTEXT (indexed at {index['built_at']}):
{context}

Provide accurate, detailed answers based on the actual code above. Reference specific files, line numbers, and code snippets when possible."""
        },
        {
            "role": "user",
            "content": question
        }
    ]
    
    print("🤖 Asking Grok-4...")
    print("="*80)
    
    completion = client.chat.completions.create(
        model="grok-2-1212",
        messages=messages,
        temperature=0.1,
    )
    
    return completion.choices[0].message.content

def main():
    if len(sys.argv) < 2:
        print("Usage: grok-indexed 'your question'")
        print("   or: grok-indexed --rebuild (force rebuild index)")
        print("   or: grok-indexed --focus 'file1.py,file2.xml' 'question'")
        sys.exit(1)
    
    # Handle rebuild command
    if sys.argv[1] == "--rebuild":
        build_index()
        print("✅ Index rebuilt successfully")
        return
    
    # Handle focus files
    focus_files = None
    question_idx = 1
    if sys.argv[1] == "--focus":
        if len(sys.argv) < 4:
            print("Usage: grok-indexed --focus 'file1.py,file2.xml' 'question'")
            sys.exit(1)
        focus_files = [f.strip() for f in sys.argv[2].split(",")]
        question_idx = 3
    
    question = sys.argv[question_idx]
    
    # Load index
    index = load_index()
    
    # Ask Grok
    answer = ask_grok(question, index, focus_files)
    
    print(answer)
    print("="*80)

if __name__ == "__main__":
    main()
