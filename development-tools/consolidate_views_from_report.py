
import os
import re
from collections import defaultdict

def consolidate_views_from_report():
    """
    Reads the find_missing_components_report.txt to identify duplicate views,
    consolidates them into a single primary file, and deletes the redundant files.
    """
    workspace_root = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
    report_path = os.path.join(workspace_root, 'find_missing_components_report.txt')
    views_dir = os.path.join(workspace_root, 'records_management', 'views')

    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # Extract the view definition status section
    view_section_match = re.search(r"🖼️ View Definition Status:\n(.*?)(?=\n\n\w|\Z)", report_content, re.DOTALL)
    if not view_section_match:
        print("Could not find the view definition status section in the report.")
        return

    view_report = view_section_match.group(1)

    # Find all duplicate entries
    duplicate_pattern = re.compile(r"\[⚠️ DUPLICATE\] ([\w\.]+) \(found in (.*?)\)")

    files_to_delete = set()
    all_primary_files = set()

    for match in duplicate_pattern.finditer(view_report):
        model_name = match.group(1)
        files_str = match.group(2)
        files = [f.strip() for f in files_str.split(',')]

        if not files:
            continue

        # Determine the primary file (the one to keep and merge into)
        # A good heuristic is to choose the one named after the model.
        primary_file = next((f for f in files if model_name.replace('.', '_') in f), files[0])
        other_files = [f for f in files if f != primary_file]

        all_primary_files.add(primary_file)
        primary_file_path = os.path.join(views_dir, primary_file)

        print(f"\nConsolidating views for model '{model_name}' into '{primary_file}'...")

        # Read or create the primary file's content
        if os.path.exists(primary_file_path):
            with open(primary_file_path, 'r', encoding='utf-8') as f:
                primary_content = f.read()
        else:
            primary_content = '<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n</odoo>'

        # Use a set to store record IDs and avoid duplicate records within the same file
        record_ids = set(re.findall(r'<record\s+id="([^"]+)"', primary_content))

        # Extract the inner content of the primary file
        primary_inner_content_match = re.search(r"<odoo>(.*)</odoo>", primary_content, re.DOTALL)
        primary_inner_content = primary_inner_content_match.group(1).strip() if primary_inner_content_match else ""

        # Merge content from other files
        for other_file in other_files:
            other_file_path = os.path.join(views_dir, other_file)
            if os.path.exists(other_file_path):
                print(f"  -> Merging from '{other_file}'")
                with open(other_file_path, 'r', encoding='utf-8') as f:
                    other_content = f.read()

                # Find all records in the other file
                other_records = re.findall(r'(<record\s+id="[^"]+".*?</record>)', other_content, re.DOTALL)
                for record in other_records:
                    record_id_match = re.search(r'id="([^"]+)"', record)
                    if record_id_match:
                        record_id = record_id_match.group(1)
                        if record_id not in record_ids:
                            primary_inner_content += '\n\n' + record
                            record_ids.add(record_id)

                files_to_delete.add(other_file)
            else:
                print(f"  -> Warning: File '{other_file}' not found, skipping.")

        # Write the consolidated content back
        with open(primary_file_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<odoo>\n')
            f.write(primary_inner_content)
            f.write('\n</odoo>\n')
        print(f"  -> Successfully consolidated views into '{primary_file}'.")

    # Delete redundant files, ensuring we don't delete a file that was also a primary file
    actual_files_to_delete = files_to_delete - all_primary_files
    if actual_files_to_delete:
        print("\nDeleting redundant view files...")
        for file_to_delete in sorted(list(actual_files_to_delete)):
            file_path = os.path.join(views_dir, file_to_delete)
            try:
                os.remove(file_path)
                print(f"  -> Deleted '{file_to_delete}'")
            except OSError as e:
                print(f"  -> Error deleting file {file_to_delete}: {e}")
    else:
        print("\nNo redundant view files to delete.")

if __name__ == "__main__":
    consolidate_views_from_report()
