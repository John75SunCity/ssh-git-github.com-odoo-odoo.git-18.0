#!/usr/bin/env python3
"""
Grok-4 Helper for Odoo Development
Uses xAI API with OpenAI-compatible client

Setup:
1. Install: pip install openai
2. Set API key: export XAI_API_KEY="your-key-here"
3. Run: python .github/agents/grok-helper.py "your question"

Example:
    python .github/agents/grok-helper.py "Analyze records.container model"
"""

import os
import sys
from openai import OpenAI

# Odoo-specific system prompt
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

You have deep knowledge of the Records Management codebase including 30+ models,
portal controllers, training course content, and validation tools.
"""

def ask_grok(question: str, api_key: str = None) -> str:
    """Ask Grok-4 a question with Odoo expert context"""
    
    # Get API key from environment or parameter
    api_key = api_key or os.getenv('XAI_API_KEY')
    if not api_key:
        return "Error: XAI_API_KEY not set. Export it or pass as parameter."
    
    try:
        # Initialize OpenAI client with xAI endpoint
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Create chat completion with Grok model
        completion = client.chat.completions.create(
            model="grok-4-0709",
            messages=[
                {"role": "system", "content": ODOO_EXPERT_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.7
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"Error calling Grok API: {str(e)}"

def main():
    # Check for piped input
    import select
    has_stdin = select.select([sys.stdin], [], [], 0.0)[0]
    
    if has_stdin:
        # Read from stdin (piped content)
        file_content = sys.stdin.read()
        if len(sys.argv) < 2:
            print("Usage: cat file.xml | grok 'your question about this file'")
            sys.exit(1)
        question = " ".join(sys.argv[1:])
        full_question = f"{question}\n\n--- FILE CONTENT ---\n{file_content}"
    else:
        # Normal command-line arguments
        if len(sys.argv) < 2:
            print(__doc__)
            sys.exit(1)
        question = " ".join(sys.argv[1:])
        full_question = question
    
    print(f"\n🤖 Asking Grok-4: {question}\n")
    print("=" * 80)
    
    answer = ask_grok(full_question)
    print(answer)
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
