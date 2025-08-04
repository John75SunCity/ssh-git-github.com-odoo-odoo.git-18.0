#!/usr/bin/env python3
"""Simple debug version of field analysis"""

import re


def main():
    print("🔍 DEBUG FIELD PARSING")
    print("=" * 50)

    missing_fields = {}
    current_model = None
    field_count = 0

    with open("missing_fields_output.txt", "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Parse model lines
            model_match = re.match(r"🚨 Model: (.+)", line)
            if model_match:
                current_model = model_match.group(1)
                missing_fields[current_model] = []
                print(f"Found model: {current_model}")
                continue

            # Parse field lines - exact format: "   - fieldname"
            if line.startswith("   - ") and current_model:
                field_name = line[5:].strip()  # Remove "   - " prefix
                missing_fields[current_model].append(field_name)
                field_count += 1
                if field_count % 100 == 0:  # Progress indicator
                    print(f"  ... processed {field_count} fields")

    print(f"\n📊 RESULTS:")
    print(f"Models found: {len(missing_fields)}")
    print(f"Total fields: {field_count}")

    # Show first few models
    for i, (model, fields) in enumerate(missing_fields.items()):
        if i < 3:
            print(f"\n{model}: {len(fields)} fields")
            for field in fields[:5]:
                print(f"  - {field}")
            if len(fields) > 5:
                print(f"  ... and {len(fields) - 5} more")


if __name__ == "__main__":
    main()
