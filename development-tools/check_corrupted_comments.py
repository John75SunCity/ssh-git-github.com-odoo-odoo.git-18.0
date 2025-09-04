#!/usr/bin/env python3
import os

def check_xml_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for unclosed comments by counting <!-- and --> occurrences
        open_comments = content.count('<!--')
        close_comments = content.count('-->')
        
        if open_comments != close_comments:
            return f'{file_path}: Mismatched comment tags - {open_comments} opens, {close_comments} closes'
        
        return None
    except Exception as e:
        return f'{file_path}: Error reading file - {e}'

def main():
    corrupted_files = []
    
    # Check view files
    view_dir = 'records_management/views'
    if os.path.exists(view_dir):
        for filename in os.listdir(view_dir):
            if filename.endswith('.xml'):
                file_path = os.path.join(view_dir, filename)
                result = check_xml_comments(file_path)
                if result:
                    corrupted_files.append(result)
    
    # Check report files
    report_dir = 'records_management/report'
    if os.path.exists(report_dir):
        for filename in os.listdir(report_dir):
            if filename.endswith('.xml'):
                file_path = os.path.join(report_dir, filename)
                result = check_xml_comments(file_path)
                if result:
                    corrupted_files.append(result)
    
    if corrupted_files:
        print("Found corrupted comments in the following files:")
        for file in corrupted_files:
            print(f"  - {file}")
    else:
        print("✅ No corrupted comments found in view or report files!")

if __name__ == "__main__":
    main()
