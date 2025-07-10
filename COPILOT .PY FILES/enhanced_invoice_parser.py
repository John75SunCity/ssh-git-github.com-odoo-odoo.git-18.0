#!/usr/bin/env python3
"""
Enhanced Invoice Parser - Improved OCR Text to Structured Data
Handles missing patterns identified from invoice screenshots:
1. Zero-dollar invoices (skip these)
2. WORKORDERS section parsing
3. Storage line items with minimum charges
4. Better invoice total detection
"""

import csv
import re
import os
import sys

def parse_invoice_text_enhanced(text):
    """
    Enhanced parser with better pattern recognition for missing invoices
    """
    invoices = []
    current_invoice_metadata = {}
    invoice_line_counter = 0
    current_page_number = 1
    
    lines = text.strip().split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for page number to handle multi-page invoices
        if line.startswith('Page:'):
            page_match = re.search(r'Page:\s*(\d+)', line)
            if page_match:
                current_page_number = int(page_match.group(1))
                if current_page_number > 1:
                    continue
            
        # Check for start of new invoice (INVOICE keyword)
        if line == 'INVOICE':
            if current_page_number == 1:
                current_invoice_metadata = {}
                invoice_line_counter = 0
            continue
            
        # Process metadata only on page 1
        if len(current_invoice_metadata) >= 0 and current_page_number == 1:
            invoice_line_counter += 1
            
            # Line 1 after INVOICE: Customer Name
            if invoice_line_counter == 1:
                current_invoice_metadata['Customer_Name'] = line
                
            # Line 4 after INVOICE: Contact Person
            elif invoice_line_counter == 4:
                current_invoice_metadata['Contact'] = line
            
        # Extract invoice number
        if line.startswith('Invoice No.') and current_page_number == 1:
            invoice_match = re.search(r'Invoice No\.\s*(\S+)', line)
            if invoice_match:
                invoice_num = invoice_match.group(1)
                current_invoice_metadata['Invoice_Number'] = invoice_num
            continue
            
        # Extract date
        if line.startswith('Date:') and current_page_number == 1:
            date_match = re.search(r'Date:\s*(.+)', line)
            if date_match:
                invoice_date = date_match.group(1).strip()
                current_invoice_metadata['Invoice_Date'] = invoice_date
            continue
            
        # Extract account number
        if line.startswith('Acct:'):
            acct_match = re.search(r'Acct:\s*(.+)', line)
            if acct_match:
                account_num = acct_match.group(1).strip()
                current_invoice_metadata['Account_Number'] = account_num
            continue
            
        # Extract PO number
        if line.startswith('Account PO#:'):
            po_match = re.search(r'Account PO#:\s*(.+)', line)
            if po_match:
                po_number = po_match.group(1).strip()
                current_invoice_metadata['PO_Number'] = po_number
            continue
            
        # Extract billing period
        if line.startswith('From:') and 'to' in line:
            period_match = re.search(r'From:\s*(.+)\s+to\s+(.+)', line)
            if period_match:
                from_date = period_match.group(1).strip()
                to_date = period_match.group(2).strip()
                current_invoice_metadata['Billing_Period_From'] = from_date
                current_invoice_metadata['Billing_Period_To'] = to_date
                billing_period = f"{from_date} to {to_date}"
                current_invoice_metadata['Billing_Period'] = billing_period
            continue
            
        # Extract contact email
        if '@' in line and '.' in line:
            current_invoice_metadata['Contact_Email'] = line
            continue
            
        # Extract address components
        if (line.startswith('P.O. BOX') or
            (re.match(r'^\d+\s+[A-Z]', line) and 'Billy' in line)):
            if 'Address_Line_1' not in current_invoice_metadata:
                current_invoice_metadata['Address_Line_1'] = line
            else:
                current_invoice_metadata['Address_Line_2'] = line
            continue
            
        # Extract city, state, zip
        if re.match(r'^[A-Z\s]+,\s*[A-Z]{2}\s+\d{5}', line):
            city_state_zip = line.split(',')
            if len(city_state_zip) == 2:
                current_invoice_metadata['City'] = city_state_zip[0].strip()
                state_zip = city_state_zip[1].strip().split()
                if len(state_zip) >= 2:
                    current_invoice_metadata['State'] = state_zip[0]
                    current_invoice_metadata['Zip_Code'] = state_zip[1]
            continue
            
        # Extract organization name
        if (('SCHOOL DISTRICT' in line or 'INDEPENDENT' in line) and
            len(line) > 10):
            current_invoice_metadata['Organization'] = line
            continue
            
        # Extract phone numbers
        if re.match(r'^\d{3}-\d{3}-\d{4}', line):
            phone_email = line.split('I')
            current_invoice_metadata['Phone'] = phone_email[0].strip()
            if len(phone_email) > 1 and '@' in phone_email[1]:
                email = phone_email[1].strip()
                current_invoice_metadata['Contact_Email'] = email
            continue
        
        # NEW: Handle WORKORDERS section (from screenshot 3)
        if (line == 'WORKORDERS' and 
            current_invoice_metadata.get('Invoice_Number')):
            # Look for work order pattern in next lines
            for j in range(i + 1, min(i + 10, len(lines))):
                wo_line = lines[j].strip()
                if wo_line.startswith('WO #'):
                    # Found work order, process it
                    if j + 4 < len(lines):
                        desc = lines[j + 1].strip()
                        
                        # Look for rate/qty/amount pattern
                        for k in range(j + 2, min(j + 6, len(lines))):
                            rate_line = lines[k].strip()
                            if re.match(r'^\d+\.\d+$', rate_line) and k + 2 < len(lines):
                                qty_line = lines[k + 1].strip()
                                amount_line = lines[k + 2].strip()
                                
                                if (re.match(r'^\d+(\.\d+)?$', qty_line) and
                                    re.match(r'^\d+\.\d+$', amount_line)):
                                    
                                    rate = float(rate_line)
                                    qty = float(qty_line)
                                    amount = float(amount_line)
                                    
                                    invoice_record = create_invoice_record(
                                        current_invoice_metadata, wo_line, desc, rate, qty, amount)
                                    invoices.append(invoice_record)
                                    break
            continue
            
        # Original WO # pattern
        if (line.startswith('WO #') and
                current_invoice_metadata.get('Invoice_Number')):
            if i + 4 < len(lines):
                desc = lines[i + 1].strip()
                rate_str = lines[i + 2].strip()
                qty_str = lines[i + 3].strip()
                amount_str = lines[i + 4].strip()
                
                if (re.match(r'^\d+\.\d+$', rate_str) and
                    re.match(r'^\d+\.\d+$', qty_str) and
                        re.match(r'^\d+\.\d+$', amount_str)):
                    
                    rate = float(rate_str)
                    qty = float(qty_str)
                    amount = float(amount_str)
                    
                    invoice_record = create_invoice_record(
                        current_invoice_metadata, line, desc, rate, qty, amount)
                    invoices.append(invoice_record)
                    
        # NEW: Enhanced storage line item detection (from screenshot 1)
        elif (current_invoice_metadata.get('Invoice_Number') and
              ('Storage_line_item' in line or 'BOX STORAGE' in line)):
            # Look for storage minimum charge pattern
            for j in range(i, min(i + 5, len(lines))):
                storage_line = lines[j].strip()
                if 'Storage Minimum Charge' in storage_line:
                    # Extract the charge amount from parentheses
                    charge_match = re.search(r'\(([0-9.]+)\)', storage_line)
                    if charge_match:
                        amount = float(charge_match.group(1))
                        
                        invoice_record = create_invoice_record(
                            current_invoice_metadata, 
                            'BOX STORAGE',
                            'Storage Minimum Charge',
                            amount, 1.0, amount)
                        invoices.append(invoice_record)
                        break
            continue
            
        # Other service types
        elif (current_invoice_metadata.get('Invoice_Number') and
              (line in ['BOX STORAGE', 'RECURRING SERVICES', 'SERVICES', 
                        'MATERIALS'] or
               line.startswith('DELIVERY FEE') or
               line.startswith('PICKUP FEE') or
               line.startswith('REGULAR RETRIEVAL'))):
            # Original logic for other services
            if i + 4 < len(lines):
                desc = lines[i + 1].strip()
                
                desc_line_idx = i + 1
                while (desc_line_idx < len(lines) and 
                       (lines[desc_line_idx].strip().startswith('(') or
                        'Storage Minimum Charge' in lines[desc_line_idx] or
                        not lines[desc_line_idx].strip())):
                    desc_line_idx += 1
                
                if desc_line_idx < len(lines):
                    desc = lines[desc_line_idx].strip()
                    
                    for j in range(desc_line_idx + 1, min(desc_line_idx + 5, len(lines))):
                        potential_rate = lines[j].strip()
                        if (j + 2 < len(lines) and 
                            re.match(r'^\d+\.\d+$', potential_rate)):
                            
                            qty_str = lines[j + 1].strip()
                            amount_str = lines[j + 2].strip()
                            
                            if (re.match(r'^\d+(\.\d+)?$', qty_str) and
                                re.match(r'^\d+\.\d+$', amount_str)):
                                
                                rate = float(potential_rate)
                                qty = float(qty_str)
                                amount = float(amount_str)
                                
                                invoice_record = create_invoice_record(
                                    current_invoice_metadata, line, desc, rate, qty, amount)
                                invoices.append(invoice_record)
                                break
        
        # ENHANCED: Better invoice total detection
        if line == 'Total Amount Due':
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Handle both "0.00" and other amounts
                if re.match(r'^\d+\.\d+$', next_line):
                    total_amount = float(next_line)
                    current_invoice_metadata['Invoice_Total'] = next_line
                    
                    # SKIP zero-dollar invoices as shown in screenshot 2
                    if total_amount == 0.00:
                        print(f"Skipping zero-dollar invoice: {current_invoice_metadata.get('Invoice_Number', 'Unknown')}")
                        continue
                    
                    # For non-zero invoices with no line items
                    if (current_invoice_metadata.get('Invoice_Number') and
                        current_invoice_metadata.get('Customer_Name')):
                        
                        invoice_exists = any(
                            item['Invoice_Number'] == current_invoice_metadata.get('Invoice_Number')
                            for item in invoices
                        )
                        
                        if not invoice_exists:
                            invoice_record = create_invoice_record(
                                current_invoice_metadata,
                                'INVOICE TOTAL ONLY',
                                'No detailed line items - total only',
                                0.0, 0.0, total_amount)
                            invoices.append(invoice_record)
            continue
    
    return invoices


def create_invoice_record(metadata, work_order, description, rate, qty, amount):
    """Helper function to create consistent invoice records"""
    return {
        'Invoice_Number': metadata.get('Invoice_Number', ''),
        'Customer_Name': metadata.get('Customer_Name', ''),
        'Contact': metadata.get('Contact', ''),
        'Invoice_Date': metadata.get('Invoice_Date', ''),
        'Contact_Email': metadata.get('Contact_Email', ''),
        'Address_Line_1': metadata.get('Address_Line_1', ''),
        'Address_Line_2': metadata.get('Address_Line_2', ''),
        'City': metadata.get('City', ''),
        'State': metadata.get('State', ''),
        'Zip_Code': metadata.get('Zip_Code', ''),
        'Account_Number': metadata.get('Account_Number', ''),
        'PO_Number': metadata.get('PO_Number', ''),
        'Billing_Period': metadata.get('Billing_Period', ''),
        'Billing_Period_From': metadata.get('Billing_Period_From', ''),
        'Billing_Period_To': metadata.get('Billing_Period_To', ''),
        'Organization': metadata.get('Organization', ''),
        'Phone': metadata.get('Phone', ''),
        'Invoice_Total': metadata.get('Invoice_Total', ''),
        'Work_Order': work_order,
        'Description': description,
        'Rate': f"{rate:.4f}",
        'Qty': f"{qty:.2f}",
        'Amount': f"{amount:.2f}"
    }


def write_csv(data, filename):
    """Write data to CSV file"""
    if not data:
        print("No data to write to CSV")
        return False
        
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Invoice_Number', 'Customer_Name', 'Contact', 'Invoice_Date',
                'Contact_Email', 'Address_Line_1', 'Address_Line_2',
                'City', 'State', 'Zip_Code', 'Account_Number',
                'PO_Number', 'Billing_Period', 'Billing_Period_From',
                'Billing_Period_To', 'Organization', 'Phone', 'Invoice_Total',
                'Work_Order', 'Description', 'Rate', 'Qty', 'Amount'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error writing CSV: {e}")
        return False


def main():
    """Main function to test enhanced parser"""
    input_file = '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/rawText.txt'
    csv_output = '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/invoices_converted_enhanced.csv'
    tsv_output = '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/invoices_converted_enhanced.tsv'
    
    print("=== Enhanced Invoice Conversion Tool ===")
    print(f"Reading from: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    print(f"Input file size: {len(text_content)} characters")
    
    # Parse with enhanced parser
    print("Parsing with enhanced patterns...")
    parsed_data = parse_invoice_text_enhanced(text_content)
    
    if not parsed_data:
        print("No invoice data found!")
        return False
    
    print(f"Found {len(parsed_data)} line items")
    
    # Get unique invoices for summary
    unique_invoices = set(item['Invoice_Number'] for item in parsed_data)
    print(f"Across {len(unique_invoices)} unique invoices")
    
    # Write outputs
    print(f"\nWriting enhanced CSV to: {csv_output}")
    if write_csv(parsed_data, csv_output):
        print("✓ Enhanced CSV file created successfully")
    
    # Write TSV
    print(f"Writing enhanced TSV to: {tsv_output}")
    try:
        with open(tsv_output, 'w', newline='', encoding='utf-8') as file:
            fieldnames = [
                'Invoice_Number', 'Customer_Name', 'Contact', 'Invoice_Date',
                'Contact_Email', 'Address_Line_1', 'Address_Line_2',
                'City', 'State', 'Zip_Code', 'Account_Number',
                'PO_Number', 'Billing_Period', 'Billing_Period_From',
                'Billing_Period_To', 'Organization', 'Phone', 'Invoice_Total',
                'Work_Order', 'Description', 'Rate', 'Qty', 'Amount'
            ]
            file.write('\t'.join(fieldnames) + '\n')
            for row in parsed_data:
                values = [str(row.get(field, '')) for field in fieldnames]
                file.write('\t'.join(values) + '\n')
        print("✓ Enhanced TSV file created successfully")
    except Exception as e:
        print(f"✗ Failed to create enhanced TSV file: {e}")
    
    print("\n=== Enhanced Conversion Complete ===")
    print(f"✓ Processed {len(parsed_data)} line items")
    print(f"✓ From {len(unique_invoices)} invoices")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
