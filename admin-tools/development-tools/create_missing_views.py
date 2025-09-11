import os

def create_missing_view_files():
    """
    Parses the integrity report to find models with missing view
    definitions and creates placeholder XML files for them.
    """
    report_path = 'find_missing_components_report.txt'
    views_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views/'
    manifest_file = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/__manifest__.py'

    try:
        with open(report_path, 'r') as f:
            report_content = f.read()
    except FileNotFoundError:
        print(f"Error: Report file not found at {report_path}")
        return

    view_section = re.search(r"🖼️ View Definition Status:\n(.*?)\n\n", report_content, re.DOTALL)
    if not view_section:
        print("Could not find the view definition status section in the report.")
        return

    view_report = view_section.group(1)
    missing_pattern = re.compile(r"\[❌ MISSING\] ([\w\.]+)")

    newly_created_files = []

    for match in missing_pattern.finditer(view_report):
        model_name = match.group(1)
        # Sanitize model name for the filename
        file_name = f"{model_name.replace('.', '_')}_views.xml"
        file_path = os.path.join(views_dir, file_name)

        if not os.path.exists(file_path):
            print(f"Creating missing view file for model '{model_name}' at '{file_path}'...")

            xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Tree view for {model_name} -->
    <record id="{model_name.replace('.', '_')}_view_tree" model="ir.ui.view">
        <field name="name">{model_name}.view.tree</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <tree>
                <field name="name"/>
            </tree>
        </field>
    </record>

    <!-- Form view for {model_name} -->
    <record id="{model_name.replace('.', '_')}_view_form" model="ir.ui.view">
        <field name="name">{model_name}.view.form</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <form string="{model_name.replace('_', ' ').title()}">
                <sheet>
                    <div class="oe_title">
                        <label for="name"/>
                        <h1>
                            <field name="name" placeholder="Name..."/>
                        </h1>
                    </div>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Search view for {model_name} -->
    <record id="{model_name.replace('.', '_')}_view_search" model="ir.ui.view">
        <field name="name">{model_name}.view.search</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <search>
                <group expand="1" string="Group By">
                    <filter string="Name" name="name" domain="[]" context="{{'group_by':'name'}}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Action for {model_name} -->
    <record id="action_{model_name.replace('.', '_')}" model="ir.actions.act_window">
        <field name="name">{model_name.replace('_', ' ').title()}</field>
        <field name="type">ir.actions.act_window</field>
        <field name="res_model">{model_name}</field>
        <field name="view_mode">tree,form</field>
        <field name="domain">[]</field>
        <field name="context">{{}}</field>
        <field name="help" type="html">
            <p class="oe_view_nocontent_create">
                Click to add a new {model_name.replace('_', ' ').lower()}.
            </p>
        </field>
    </record>

</odoo>
"""
            try:
                with open(file_path, 'w') as f:
                    f.write(xml_content)
                print(f"  -> Successfully created '{file_name}'")
                newly_created_files.append(f"        'views/{file_name}',")
            except IOError as e:
                print(f"  -> Error creating file {file_name}: {e}")
        else:
            print(f"View file for '{model_name}' already exists at '{file_path}', skipping.")

    # Update the manifest file with the new view files
    if newly_created_files:
        print("\nUpdating manifest file with new views...")
        try:
            with open(manifest_file, 'r') as f:
                manifest_content = f.readlines()

            # Find the line with 'data':
            data_line_index = -1
            for i, line in enumerate(manifest_content):
                if "'data':" in line:
                    data_line_index = i
                    break

            if data_line_index != -1:
                # Insert new files after the 'data' line
                for new_file_line in reversed(newly_created_files):
                    manifest_content.insert(data_line_index + 1, new_file_line + '\n')

                with open(manifest_file, 'w') as f:
                    f.writelines(manifest_content)
                print("  -> Successfully updated __manifest__.py")
            else:
                print("  -> Warning: Could not find the 'data' key in the manifest file. Please add the new files manually.")

        except FileNotFoundError:
            print(f"Warning: Manifest file not found at {manifest_file}. Please add the new files manually.")
        except IOError as e:
            print(f"  -> Error updating manifest file: {e}")


if __name__ == "__main__":
    import re
    create_missing_view_files()
