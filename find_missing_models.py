#!/usr/bin/env python3
import os
import re
import xml.etree.ElementTree as ET

# Get all model names from Python files
models = set()
for root, dirs, files in os.walk('records_management/models'):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            try:
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    # Find _name = declarations
                    matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
                    models.update(matches)
            except Exception as e:
                print(f"Error reading {file}: {e}")

print(f'Found {len(models)} model definitions')

# Get all model references from XML files
xml_models = set()
missing_models = set()

for root, dirs, files in os.walk('records_management'):
    for file in files:
        if file.endswith('.xml'):
            try:
                tree = ET.parse(os.path.join(root, file))
                # Find model references in views and actions
                for elem in tree.findall('.//field[@name="model"]'):
                    if elem.text:
                        xml_models.add(elem.text.strip())
                for elem in tree.findall('.//field[@name="res_model"]'):
                    if elem.text:
                        xml_models.add(elem.text.strip())
            except Exception as e:
                print(f'Error parsing {file}: {e}')

# Find potentially missing models (excluding Odoo core models)
core_prefixes = [
    'ir.', 'res.', 'account.', 'stock.', 'sale.', 'purchase.', 'product.', 
    'mail.', 'website.', 'calendar.', 'hr.', 'project.', 'maintenance.', 
    'crm.', 'pos.', 'fleet.', 'base.', 'portal.', 'sign.', 'survey.', 
    'documents.', 'helpdesk.', 'mass_mailing.', 'website_slides.', 
    'quality.', 'rating.', 'utm.', 'digest.', 'bus.', 'http_routing.', 
    'industry_fsm.'
]

for xml_model in xml_models:
    if xml_model not in models and not any(xml_model.startswith(prefix) for prefix in core_prefixes):
        missing_models.add(xml_model)

print(f'\nFound {len(missing_models)} potentially missing models:')
for model in sorted(missing_models):
    print(f'  - {model}')

if missing_models:
    print(f'\nFirst few existing models for reference:')
    for model in sorted(list(models))[:10]:
        print(f'  ✅ {model}')
