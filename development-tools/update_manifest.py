
import os
import re
import ast

def update_manifest_data():
    """
    Scans the 'records_management/views' directory for XML files and
    updates the 'data' key in 'records_management/__manifest__.py' to
    reflect the found files, preserving the order of other data entries.
    """
    workspace_root = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'
    manifest_path = os.path.join(workspace_root, 'records_management', '__manifest__.py')
    views_dir = os.path.join(workspace_root, 'records_management', 'views')
    report_path = os.path.join(workspace_root, 'find_missing_components_report.txt')

    print(f"Starting manifest update for: {manifest_path}")

    # 1. Get the list of actual XML files in the views directory
    if not os.path.isdir(views_dir):
        print(f"Error: Views directory not found at {views_dir}")
        return
    
    try:
        view_files = sorted([f'views/{f}' for f in os.listdir(views_dir) if f.endswith('.xml')])
        print(f"Found {len(view_files)} XML files in {views_dir}")
    except Exception as e:
        print(f"Error reading views directory {views_dir}: {e}")
        return

    # 2. Read the existing manifest file content
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {manifest_path}")
        return
    except Exception as e:
        print(f"Error reading manifest file: {e}")
        return

    # 3. Parse the manifest content as a Python literal
    try:
        manifest_dict = ast.literal_eval(manifest_content)
        if not isinstance(manifest_dict, dict):
            raise ValueError("Manifest content is not a dictionary.")
    except (ValueError, SyntaxError) as e:
        print(f"Error: Could not parse manifest file content. It might not be a valid Python dictionary. Error: {e}")
        # Fallback to regex if ast fails
        return update_manifest_with_regex(manifest_path, manifest_content, view_files)


    # 4. Get existing data files, excluding view files
    existing_data = manifest_dict.get('data', [])
    other_data_files = [df for df in existing_data if not df.startswith('views/')]
    
    print(f"Found {len(other_data_files)} non-view data files to preserve.")

    # 5. Combine and update the data list
    manifest_dict['data'] = other_data_files + view_files

    # 6. Write the updated dictionary back to the manifest file
    # This part is tricky because ast doesn't preserve formatting.
    # We will use regex to replace just the 'data' list.
    update_manifest_with_regex(manifest_path, manifest_content, manifest_dict['data'])


def update_manifest_with_regex(manifest_path, manifest_content, new_data_list):
    """
    Uses regex to replace the 'data' key's value in the manifest file content.
    """
    print("Using regex method to update manifest.")
    
    # Convert the list of strings to a nicely formatted string for the file
    # Note: Odoo manifests often have a trailing comma.
    formatted_data_list = ',\n        '.join([f"'{item}'" for item in new_data_list])
    data_list_str = f"[\n        {formatted_data_list},\n    ]"

    # Regex to find the 'data' key and its list value
    # This is complex due to the multi-line, nested nature of the list.
    # It looks for 'data': [ ... ]
    data_pattern = re.compile(r"'data'\s*:\s*\[.*?\]", re.DOTALL)

    new_data_section = f"'data': {data_list_str}"

    if data_pattern.search(manifest_content):
        new_content = data_pattern.sub(new_data_section, manifest_content, count=1)
        print("Successfully replaced 'data' list in manifest.")
    else:
        # If 'data' key doesn't exist, we might need to add it.
        # This is a simplified approach, adding it before the closing '}'
        closing_brace_pattern = re.compile(r"\n}\s*$")
        new_data_section_with_comma = f",\n    {new_data_section}\n"
        if closing_brace_pattern.search(manifest_content):
             new_content = closing_brace_pattern.sub(f"{new_data_section_with_comma}}}", manifest_content)
             print("Added 'data' key to manifest.")
        else:
            print("Warning: Could not find a suitable place to add the 'data' key.")
            new_content = manifest_content # fallback to original

    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully updated manifest file: {manifest_path}")
    except Exception as e:
        print(f"Error writing updated manifest file: {e}")


if __name__ == "__main__":
    update_manifest_data()
