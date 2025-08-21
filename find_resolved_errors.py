import re

# Path to the copilot-instructions.md file (adjust if needed based on workspace structure)
file_path = '.github/copilot-instructions.md'

# Read the file content
with open(file_path, 'r') as file:
    content = file.read()

# Regex pattern to find the resolved errors section
# Looks for the header and captures the numbered list 1-6
pattern = r"\*\*✅ RESOLVED ERRORS \(in chronological order\):\*\*\n\n(1\..*?)\n(2\..*?)\n(3\..*?)\n(4\..*?)\n(5\..*?)\n(6\..*?)\n"

# Find the matching section (using re.DOTALL to match across lines)
match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

if match:
    # Extract and print each item
    for i in range(1, 7):
        print(f"{i}. {match.group(i).strip()}")
else:
    print("Resolved errors section not found in the file.")
