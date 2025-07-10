#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

def validate_xml(file_path):
    try:
        tree = ET.parse(file_path)
        print(f'✅ {file_path} is valid XML')
        return True
    except ET.ParseError as e:
        print(f'❌ {file_path} - XML Parse Error: {e}')
        return False
    except Exception as e:
        print(f'❌ {file_path} - Error: {e}')
        return False

# Validate products.xml
if validate_xml('records_management/data/products.xml'):
    print('Products XML is ready for deployment!')
else:
    sys.exit(1)
