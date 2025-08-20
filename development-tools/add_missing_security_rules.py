
import os

def add_missing_security_rules():
    """
    Adds missing security rules to ir.model.access.csv if they don't already exist.
    """
    security_file_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv'

    missing_rules = {
        'display_name': "access_display_name_user,display.name.user,model_display_name,records_management.group_records_user,1,1,1,0",
        'full_customization_name': "access_full_customization_name_user,full.customization.name.user,model_full_customization_name,records_management.group_records_user,1,1,1,0",
        'report.records_management.report_customer_inventory': "access_report_records_management_report_customer_inventory_user,report.records_management.report_customer_inventory.user,model_report_records_management_report_customer_inventory,records_management.group_records_user,1,1,1,0",
        'report.records_management.report_location_utilization': "access_report_records_management_report_location_utilization_user,report.records_management.report_location_utilization.user,model_report_records_management_report_location_utilization,records_management.group_records_user,1,1,1,0",
        'serial_number': "access_serial_number_user,serial.number.user,model_serial_number,records_management.group_records_user,1,1,1,0",
        'shredding.hard_drive': "access_shredding_hard_drive_user,shredding.hard.drive.user,model_shredding_hard_drive,records_management.group_records_user,1,1,1,0",
    }

    try:
        with open(security_file_path, 'r+') as f:
            existing_rules = f.read()
            rules_to_add = []

            for model_name, rule_line in missing_rules.items():
                # Check if a rule for the model already exists to avoid duplicates
                if f"model_{model_name.replace('.', '_')}" not in existing_rules:
                    rules_to_add.append(rule_line)

            if rules_to_add:
                print(f"Adding {len(rules_to_add)} missing security rules...")
                # Go to the end of the file to append
                f.seek(0, 2)
                # Ensure there's a newline before adding new rules if the file doesn't end with one
                if not existing_rules.endswith('\n'):
                    f.write('\n')
                f.write('\n'.join(rules_to_add))
                f.write('\n')
                print("Successfully added missing rules.")
            else:
                print("No missing security rules to add. The file is up-to-date.")

    except FileNotFoundError:
        print(f"Error: Security file not found at {security_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    add_missing_security_rules()
