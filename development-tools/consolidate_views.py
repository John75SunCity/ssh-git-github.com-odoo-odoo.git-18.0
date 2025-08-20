import os
import re
from collections import defaultdict

def consolidate_duplicate_views():
    """
    Scans for duplicate view definitions in the integrity report,
    consolidates them into one file, and deletes the redundant files.
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
    duplicate_pattern = re.compile(r"\[⚠️ DUPLICATE\] ([\w\.]+) \(found in (.*?)\)")

    all_view_files = set()
    try:
        with open(manifest_file, 'r') as f:
            manifest_content = f.read()
            data_files_str = re.search(r"'data':\s*\[(.*?)\]", manifest_content, re.DOTALL).group(1)
            # Use a more robust regex to find all file paths
            view_files_in_manifest = re.findall(r"['\"](views/.*?.xml)['\"]", data_files_str)
            all_view_files.update(view_files_in_manifest)
    except (FileNotFoundError, AttributeError):
        print(f"Warning: Could not read or parse manifest file at {manifest_file}. File deletion from manifest will be skipped.")
        all_view_files = set() # Ensure it's a set

    files_to_delete = set()

    for match in duplicate_pattern.finditer(view_report):
        model_name = match.group(1)
        files_str = match.group(2)
        files = [f.strip() for f in files_str.split(',')]

        if not files:
            continue

        # Choose the primary file (e.g., the one with the model name in it)
        primary_file = next((f for f in files if model_name.replace('.', '_') in f), files[0])
        other_files = [f for f in files if f != primary_file]

        primary_file_path = os.path.join(views_dir, primary_file)

        print(f"\nConsolidating views for model '{model_name}' into '{primary_file}'...")

        # Ensure primary file exists, if not, create it
        if not os.path.exists(primary_file_path):
            print(f"  -> Primary file '{primary_file}' does not exist. Creating it.")
            with open(primary_file_path, 'w') as pf:
                pf.write('<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n\n</odoo>\n')

        # Read primary file content once
        with open(primary_file_path, 'r') as f:
            primary_content = f.read().strip()
            # Ensure the file ends correctly before appending
            if primary_content.endswith('</odoo>'):
                primary_content = primary_content[:-len('</odoo>')].strip()
            else:
                 # If it's empty or doesn't have odoo tags, initialize it
                primary_content = '<?xml version="1.0" encoding="utf-8"?>\n<odoo>'

        # Append content from other files
        for other_file in other_files:
            other_file_path = os.path.join(views_dir, other_file)
            if os.path.exists(other_file_path):
                print(f"  -> Merging content from '{other_file}'")
                with open(other_file_path, 'r') as of:
                    # Read content, strip XML header and odoo tags
                    other_content = of.read()
                    inner_content = re.search(r"<odoo>(.*?)</odoo>", other_content, re.DOTALL)
                    if inner_content:
                        primary_content += '\n\n' + inner_content.group(1).strip() + '\n'

                # Mark file for deletion
                files_to_delete.add(other_file)
            else:
                print(f"  -> Warning: File '{other_file}' not found, skipping.")

        # Write the consolidated content back to the primary file
        with open(primary_file_path, 'w') as f:
            f.write(primary_content.strip() + '\n\n</odoo>\n')
        print(f"  -> Successfully consolidated views into '{primary_file}'.")


    # Delete the redundant files
    if files_to_delete:
        print("\nDeleting redundant view files...")
        for file_to_delete in files_to_delete:
            file_path = os.path.join(views_dir, file_to_delete)
            try:
                os.remove(file_path)
                print(f"  -> Deleted '{file_to_delete}'")
            except OSError as e:
                print(f"  -> Error deleting file {file_to_delete}: {e}")

    # Update the manifest file
    if all_view_files and files_to_delete:
        print("\nUpdating manifest file...")
        updated_view_files = all_view_files - set('views/' + f for f in files_to_delete)

        # Create the new data list string
        new_data_list_str = ",\n        ".join(sorted([f"'{f}'" for f in updated_view_files]))

        # Replace the old list in the manifest content
        updated_manifest_content = re.sub(
            r"('data':\s*\[).*?(\])",
            r"\1\n        " + new_data_list_str + "\n    \2",
            manifest_content,
            flags=re.DOTALL
        )

        try:
            with open(manifest_file, 'w') as f:
                f.write(updated_manifest_content)
            print("  -> Successfully updated __manifest__.py")
        except IOError as e:
            print(f"  -> Error writing to manifest file: {e}")


if __name__ == "__main__":
    consolidate_duplicate_views()
