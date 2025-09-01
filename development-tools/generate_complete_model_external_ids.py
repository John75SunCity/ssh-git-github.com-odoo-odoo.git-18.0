#!/usr/bin/env python3
"""
Generate Complete Model External IDs for Records Management

This script automatically generates a complete model_external_ids_data.xml file
containing all the model external ID references needed by the Records Management module.
"""

import os
import re
from collections import defaultdict

def extract_custom_models():
    """Extract all custom model names from Python files."""
    models = set()
    models_dir = 'records_management/models'

    for file in os.listdir(models_dir):
        if file.endswith('.py') and file != '__init__.py':
            try:
                with open(os.path.join(models_dir, file), 'r') as f:
                    content = f.read()
                    matches = re.findall(r'_name\s*=\s*[\'\"](.*?)[\'\"]', content)
                    for match in matches:
                        if not match.startswith('_') and '.' in match:
                            models.add(match)
            except Exception as e:
                print(f"Error reading {file}: {e}")

    return sorted(models)

def extract_referenced_models():
    """Extract all model references from XML/data files."""
    referenced_models = set()
    xml_dirs = ['records_management/data', 'records_management/views', 'records_management/security']

    for xml_dir in xml_dirs:
        if os.path.exists(xml_dir):
            for root, dirs, files in os.walk(xml_dir):
                for file in files:
                    if file.endswith('.xml') or file.endswith('.csv'):
                        try:
                            with open(os.path.join(root, file), 'r') as f:
                                content = f.read()
                                # Find model_ references
                                matches = re.findall(r'model_([a-zA-Z_][a-zA-Z0-9_]*)', content)
                                referenced_models.update(matches)

                                # Find model="" references and convert to model_ format
                                model_refs = re.findall(r'model=[\"\'](.*?)[\"\']', content)
                                for model_ref in model_refs:
                                    if '.' in model_ref and not model_ref.startswith('ir.'):
                                        clean_name = model_ref.replace('.', '_')
                                        referenced_models.add(clean_name)
                        except Exception as e:
                            print(f"Error reading {os.path.join(root, file)}: {e}")

    return sorted(referenced_models)

def model_name_to_external_id(model_name):
    """Convert model name to external ID format."""
    return f"model_{model_name.replace('.', '_')}"

def model_name_to_display_name(model_name):
    """Convert model name to human-readable display name."""
    # Split by dots and underscores, then title case each part
    parts = model_name.replace('.', ' ').replace('_', ' ').split()
    return ' '.join(word.title() for word in parts)

def categorize_models(models):
    """Categorize models by domain for better organization."""
    categories = defaultdict(list)

    for model in models:
        if any(keyword in model for keyword in ['naid', 'compliance', 'audit', 'certification']):
            categories['NAID & Compliance'].append(model)
        elif any(keyword in model for keyword in ['billing', 'payment', 'invoice', 'rate']):
            categories['Billing & Finance'].append(model)
        elif any(keyword in model for keyword in ['container', 'document', 'location', 'storage']):
            categories['Core Records'].append(model)
        elif any(keyword in model for keyword in ['pickup', 'route', 'fsm', 'vehicle']):
            categories['Fleet & Routes'].append(model)
        elif any(keyword in model for keyword in ['shredding', 'destruction', 'paper', 'bale']):
            categories['Shredding & Destruction'].append(model)
        elif any(keyword in model for keyword in ['portal', 'feedback', 'customer']):
            categories['Portal & Customer'].append(model)
        elif any(keyword in model for keyword in ['survey', 'template', 'mail']):
            categories['Communication'].append(model)
        elif any(keyword in model for keyword in ['wizard', 'report', 'config']):
            categories['System & Configuration'].append(model)
        else:
            categories['Other Models'].append(model)

    return categories

def generate_model_external_ids_xml():
    """Generate the complete model_external_ids_data.xml file."""
    # Get all custom models and referenced models
    custom_models = extract_custom_models()
    referenced_models = extract_referenced_models()

    # Convert referenced model IDs back to model names
    referenced_model_names = set()
    for ref_model in referenced_models:
        # Convert model_xxx back to xxx format, then dots
        if ref_model.startswith('model_'):
            clean_name = ref_model[6:]  # Remove 'model_' prefix
        else:
            clean_name = ref_model

        # Try to match with actual custom models
        model_name = clean_name.replace('_', '.')
        if model_name in custom_models:
            referenced_model_names.add(model_name)
        else:
            # Also check for partial matches or variations
            for custom_model in custom_models:
                if custom_model.replace('.', '_') == clean_name:
                    referenced_model_names.add(custom_model)
                    break

    # Combine and deduplicate
    all_needed_models = sorted(set(custom_models) | referenced_model_names)

    print(f"Found {len(custom_models)} custom models")
    print(f"Found {len(referenced_models)} model references")
    print(f"Will generate {len(all_needed_models)} model external IDs")

    # Categorize for better organization
    categories = categorize_models(all_needed_models)

    # Generate XML content
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="0">
        <!--
        Complete External ID references for Records Management models

        This file contains external ID definitions for all custom models in the
        Records Management module. These external IDs are required for:
        - Mail templates that reference models
        - Report bindings
        - Security rules
        - Intelligent search indexes
        - Automated actions
        - Any XML data that references models

        Generated automatically - do not edit manually.
        Use development-tools/generate_complete_model_external_ids.py to regenerate.
        -->

'''

    for category, models in categories.items():
        if models:
            xml_content += f'        <!-- {category} Models -->\n'
            for model in sorted(models):
                external_id = model_name_to_external_id(model)
                display_name = model_name_to_display_name(model)
                xml_content += f'''        <record id="{external_id}" model="ir.model">
            <field name="model">{model}</field>
            <field name="name">{display_name}</field>
        </record>

'''

    xml_content += '''    </data>
</odoo>
'''

    return xml_content

def main():
    """Main execution function."""
    print("🔧 Generating Complete Model External IDs...")

    # Change to the correct directory
    if not os.path.exists('records_management'):
        print("❌ Error: Must run from the root directory containing records_management/")
        return

    # Generate the XML content
    xml_content = generate_model_external_ids_xml()

    # Write to file
    output_file = "records_management/data/model_external_ids_data.xml"
    with open(output_file, 'w') as f:
        f.write(xml_content)

    print(f"✅ Generated complete model external IDs in {output_file}")
    print("🎯 This file now contains all model external IDs needed by your module.")

if __name__ == '__main__':
    main()
