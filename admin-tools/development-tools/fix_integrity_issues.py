
import os
import re

def fix_integrity_issues_from_report():
    """
    Reads the find_missing_components_report.txt and fixes the issues listed in it.
    - Adds missing security rules to ir.model.access.csv.
    - Creates missing view files.
    """
    workspace_root = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
    report_path = os.path.join(workspace_root, 'find_missing_components_report.txt')
    security_file_path = os.path.join(workspace_root, 'records_management', 'security', 'ir.model.access.csv')
    views_dir = os.path.join(workspace_root, 'records_management', 'views')

    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # --- 1. Fix Missing Security Rules ---
    security_section_match = re.search(r"🔐 Security Rule Status.*?:\n(.*?)(?=\n\n\w|\Z)", report_content, re.DOTALL)
    if security_section_match:
        security_report = security_section_match.group(1)
        missing_models = re.findall(r"\[❌ MISSING\] ([\w\.]+)", security_report)

        if missing_models:
            print(f"Found {len(missing_models)} missing security rules to add.")
            rules_to_add = []

            with open(security_file_path, 'r', encoding='utf-8') as f:
                existing_rules = f.read()

            for model_name in missing_models:
                model_id_str = f"model_{model_name.replace('.', '_')}"
                # Check if a rule for this model already exists to prevent duplicates
                if model_id_str not in existing_rules:
                    rule_name = model_name.replace('.', '_')
                    rule_line = f"access_{rule_name}_user,{model_name}.user,{model_id_str},records_management.group_records_user,1,1,1,0"
                    rules_to_add.append(rule_line)
                else:
                    print(f"  - Rule for '{model_name}' seems to exist already, skipping.")

            if rules_to_add:
                with open(security_file_path, 'a', encoding='utf-8') as f:
                    f.write('\n' + '\n'.join(rules_to_add) + '\n')
                print(f"Successfully appended {len(rules_to_add)} new security rules.")
            else:
                print("No new security rules were appended.")
        else:
            print("No missing security rules found in the report.")

    # --- 2. Fix Missing View Files ---
    view_section_match = re.search(r"🖼️ View Definition Status.*?:\n(.*?)(?=\n\n\w|\Z)", report_content, re.DOTALL)
    if view_section_match:
        view_report = view_section_match.group(1)
        missing_views = re.findall(r"\[❌ MISSING\] ([\w\.]+)", view_report)

        if missing_views:
            print(f"\nFound {len(missing_views)} missing view files to create.")
            for model_name in missing_views:
                view_file_name = f"{model_name.replace('.', '_')}_views.xml"
                view_file_path = os.path.join(views_dir, view_file_name)

                if not os.path.exists(view_file_path):
                    model_name_underscored = model_name.replace('.', '_')

                    xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Views for {model_name} -->
    <record id="view_{model_name_underscored}_tree" model="ir.ui.view">
        <field name="name">{model_name}.tree</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <tree string="{model_name.title()}">
                <!-- Add fields here -->
            </tree>
        </field>
    </record>

    <record id="view_{model_name_underscored}_form" model="ir.ui.view">
        <field name="name">{model_name}.form</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <form string="{model_name.title()}">
                <sheet>
                    <group>
                        <!-- Add fields here -->
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_{model_name_underscored}" model="ir.actions.act_window">
        <field name="name">{model_name.title()}</field>
        <field name="res_model">{model_name}</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''
                    with open(view_file_path, 'w', encoding='utf-8') as f:
                        f.write(xml_content)
                    print(f"  -> Created view file: {view_file_name}")
                else:
                    print(f"  -> View file '{view_file_name}' already exists, skipping.")
        else:
            print("\nNo missing view files found in the report.")


if __name__ == "__main__":
    fix_integrity_issues_from_report()
