#!/usr/bin/env python3
"""
Grok-4 with Full Records Management Context

Automatically includes all model definitions and demo files when querying.
This gives Grok access to your entire codebase for accurate answers.

Usage:
    python .github/agents/grok-with-context.py "your question"
    
Or with alias:
    grok-full "check if demo fields are valid"
"""

import os
import sys
import glob
from openai import OpenAI

ODOO_EXPERT_PROMPT = """You are a PhD-level Odoo 18.0 development expert specializing in:

- Enterprise Records Management module architecture
- NAID AAA compliance and chain of custody workflows
- Model inheritance, ORM optimization, and batch operations
- Portal development, barcode integration, and eLearning content
- Security rules, access controls, and department-based permissions

Key principles:
1. One model per file - search existing models before creating new ones
2. Always update security access rules when creating models/fields
3. Verify field compatibility (numeric vs text Selection fields)
4. Follow Odoo coding standards (proper import order, naming conventions)

You have full access to the Records Management codebase provided below.
"""

def gather_codebase_context():
    """Gather all model files and demo data"""
    context = []
    
    # Get all Python model files
    model_files = glob.glob("records_management/models/*.py")
    fsm_model_files = glob.glob("records_management_fsm/models/*.py") if os.path.exists("records_management_fsm") else []
    
    # Get all demo XML files
    demo_files = glob.glob("records_management/demo/*.xml")
    fsm_demo_files = glob.glob("records_management_fsm/demo/*.xml") if os.path.exists("records_management_fsm") else []
    
    all_files = model_files + fsm_model_files + demo_files + fsm_demo_files
    
    # Limit to most important files to avoid token limits
    priority_files = [f for f in all_files if any(keyword in f for keyword in [
        'records_container.py', 'records_location.py', 'destruction_certificate.py',
        'customer_inventory_demo.xml', 'naid_demo_certificates.xml'
    ])]
    
    # Add other model files (limited)
    other_models = [f for f in model_files if f not in priority_files][:20]
    files_to_include = priority_files + other_models
    
    for filepath in files_to_include:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Truncate very long files
                if len(content) > 10000:
                    content = content[:10000] + "\n\n... (file truncated)"
                context.append(f"\n--- {filepath} ---\n{content}")
        except Exception as e:
            context.append(f"\n--- {filepath} ---\nError reading: {str(e)}")
    
    return "\n".join(context)

def ask_grok_with_context(question: str, context: str, api_key: str = None) -> str:
    """Ask Grok-4 with full codebase context"""
    
    api_key = api_key or os.getenv('XAI_API_KEY')
    if not api_key:
        return "Error: XAI_API_KEY not set."
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        
        full_prompt = f"{ODOO_EXPERT_PROMPT}\n\n--- CODEBASE CONTEXT ---\n{context}\n\n--- USER QUESTION ---\n{question}"
        
        completion = client.chat.completions.create(
            model="grok-4-0709",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"Error calling Grok API: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print(f"\n🤖 Asking Grok-4 with full codebase context...")
    print(f"📋 Question: {question}\n")
    print("=" * 80)
    print("Loading codebase context... (this may take a moment)")
    
    context = gather_codebase_context()
    print(f"✓ Loaded {len(context)} characters of context")
    print("=" * 80 + "\n")
    
    answer = ask_grok_with_context(question, context)
    print(answer)
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
