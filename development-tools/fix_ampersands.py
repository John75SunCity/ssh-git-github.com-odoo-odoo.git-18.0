import os
import re
import sys

def fix_ampersands_in_file(file_path):
    """
    Replaces all unescaped ampersands in a file with '&amp;'.
    It avoids replacing ampersands that are already part of an entity.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use regex to replace '&' that is not followed by a known entity name
        new_content, count = re.subn(r'&(?!(?:amp|lt|gt|quot|apos|#\d+);)', '&amp;', content)

        if count > 0:
            print(f"Found and replaced {count} unescaped ampersand(s) in {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return count > 0
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def main(directory):
    """
    Walks through a directory and fixes unescaped ampersands in all .xml files.
    """
    if not os.path.isdir(directory):
        print(f"Error: Directory not found at '{directory}'")
        sys.exit(1)

    print(f"Starting scan in '{directory}'...")
    fixed_files_count = 0
    total_replacements = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".xml"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content, count = re.subn(r'&(?!(?:amp|lt|gt|quot|apos|#\d+);)', '&amp;', content)

                    if count > 0:
                        total_replacements += count
                        print(f"Fixed {count} issue(s) in: {file_path}")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        fixed_files_count += 1

                except Exception as e:
                    print(f"Could not process file {file_path}: {e}")

    if total_replacements > 0:
        print(f"\nFinished. Replaced {total_replacements} ampersand(s) across {fixed_files_count} file(s).")
    else:
        print("\nFinished. No unescaped ampersands found.")

if __name__ == "__main__":
    target_directory = sys.argv[1] if sys.argv[1:] else 'records_management/views'
    main(target_directory)
