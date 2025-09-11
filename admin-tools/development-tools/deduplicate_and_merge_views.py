import os
import re

def deduplicate_and_merge_views():
    """
    Reads specified XML view files, extracts all <record> blocks,
    deduplicates them by ID, and merges them into a new consolidated file.
    The old files are then deleted.
    """
    views_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views/'
    files_to_merge = [
        'records_advanced_billing_period_views.xml',
        'records_billing_service_views.xml',
    ]
    output_file = 'records_billing_consolidated_views.xml'
    output_path = os.path.join(views_dir, output_file)

    all_records = {}
    print("Starting view deduplication and merge process...")

    for filename in files_to_merge:
        filepath = os.path.join(views_dir, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File not found, skipping: {filepath}")
            continue

        print(f"Reading records from {filename}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all <record>...</record> blocks
        records = re.findall(r'<record\s+id="[^"]+".*?</record>', content, re.DOTALL)

        for record in records:
            record_id_match = re.search(r'id="([^"]+)"', record)
            if record_id_match:
                record_id = record_id_match.group(1)
                if record_id not in all_records:
                    all_records[record_id] = record

    print(f"Found {len(all_records)} unique records to consolidate.")

    # Write the deduplicated records to the new file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<odoo>\n\n')
            # Writing records in a sorted order for consistency
            for record_id in sorted(all_records.keys()):
                f.write(all_records[record_id])
                f.write('\n\n')
            f.write('</odoo>\n')
        print(f"Successfully consolidated views into {output_file}")
    except IOError as e:
        print(f"Error writing to new file {output_path}: {e}")
        return

    # Delete the old, now redundant, files
    print("Deleting old view files...")
    for filename in files_to_merge:
        filepath = os.path.join(views_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"  -> Deleted: {filename}")
            except OSError as e:
                print(f"  -> Error deleting file {filename}: {e}")

if __name__ == "__main__":
    deduplicate_and_merge_views()
