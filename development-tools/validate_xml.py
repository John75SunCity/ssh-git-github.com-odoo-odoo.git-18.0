import sys
from lxml import etree

def validate_xml(file_path):
    try:
        etree.parse(file_path)
        print(f"Successfully parsed {file_path}")
    except etree.XMLSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_xml.py <file_path>")
        sys.exit(1)
    validate_xml(sys.argv[1])
