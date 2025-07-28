#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

def validate_xml_file(filepath):
    try:
        ET.parse(filepath)
        print(f"✅ {filepath} - Valid XML")
        return True
    except ET.ParseError as e:
        print(f"❌ {filepath} - XML Parse Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {filepath} - Error: {e}")
        return False

if __name__ == "__main__":
    files_to_test = [
        "records_management/templates/portal_document_retrieval.xml",
        "records_management/views/records_box_views.xml"
    ]
    
    all_valid = True
    for file_path in files_to_test:
        if not validate_xml_file(file_path):
            all_valid = False
    
    if all_valid:
        print("\n🎉 All XML files are valid!")
    else:
        print("\n⚠️ Some XML files have errors!")
        sys.exit(1)
