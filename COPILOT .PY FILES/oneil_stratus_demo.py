#!/usr/bin/env python3
"""
O'Neil Stratus Compatibility Demo Script
========================================

This script demonstrates the enhanced Records Management module's compatibility
with O'Neil Stratus features based on the provided documentation.

Features demonstrated:
1. Enhanced Container/Box Management
2. Comprehensive Service Types
3. Flexible Barcode Configuration
4. Advanced Billing with Quantity Breaks
5. Status Tracking and Access Control
6. Account Hierarchy Management
"""

import os
import sys
import logging

# Add the Odoo directory to the Python path
sys.path.insert(0, '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.exceptions import ValidationError
    import datetime
    from dateutil.relativedelta import relativedelta
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def demo_enhanced_box_management(env):
        """Demonstrate enhanced box management with O'Neil Stratus fields"""
        print("\n" + "="*60)
        print("DEMO: Enhanced Box Management (O'Neil Stratus Compatible)")
        print("="*60)
        
        # Create a customer
        customer = env['res.partner'].create({
            'name': 'ACME Corporation',
            'is_company': True,
            'customer_rank': 1,
        })
        
        # Create a department
        department = env['records.department'].create({
            'name': 'Legal Department',
            'customer_id': customer.id,
            'code': 'LEG',
        })
        
        # Create a location
        location = env['records.location'].create({
            'name': 'Warehouse A - Section 1',
            'code': 'WH-A-S1',
            'capacity': 1000,
        })
        
        # Create an enhanced box with O'Neil Stratus fields
        box_data = {
            'name': 'BOX-2024-001',
            'alternate_code': 'ALT-001',
            'description': 'Legal Documents - Contract Files',
            'container_type': 'standard',
            'customer_id': customer.id,
            'department_id': department.id,
            'location_id': location.id,
            
            # O'Neil Stratus Classification Fields
            'security_code': 'CONF',
            'category_code': 'LEGAL',
            'record_series': 'CONTRACTS',
            'object_code': 'DOC',
            
            # Account Hierarchy
            'account_level1': '1000',
            'account_level2': '1100',
            'account_level3': '1110',
            
            # Sequence and Date Ranges
            'sequence_from': 1,
            'sequence_to': 100,
            'date_from': datetime.date(2024, 1, 1),
            'date_to': datetime.date(2024, 12, 31),
            
            # User-defined fields
            'user_field1': 'Project Alpha',
            'user_field2': 'High Priority',
            'user_field3': 'Review Required',
            'user_field4': 'External Counsel',
            'custom_date': datetime.date(2024, 6, 30),
            
            # Barcode configuration
            'barcode': '123456789012',
            'barcode_type': 'code128',
            'barcode_length': 12,
            
            # Billing flags
            'charge_for_storage': True,
            'charge_for_add': True,
            'perm_flag': False,
            
            # Status
            'item_status': 'active',
            'state': 'active',
        }
        
        box = env['records.box'].create(box_data)
        
        print(f"✓ Created enhanced box: {box.name}")
        print(f"  - Alternate Code: {box.alternate_code}")
        print(f"  - Description: {box.description}")
        print(f"  - Container Type: {box.container_type}")
        print(f"  - Security Code: {box.security_code}")
        print(f"  - Category Code: {box.category_code}")
        print(f"  - Record Series: {box.record_series}")
        print(f"  - Account Hierarchy: {box.account_level1}/{box.account_level2}/{box.account_level3}")
        print(f"  - Sequence Range: {box.sequence_from}-{box.sequence_to}")
        print(f"  - Date Range: {box.date_from} to {box.date_to}")
        print(f"  - Barcode: {box.barcode} ({box.barcode_type})")
        print(f"  - User Fields: {box.user_field1}, {box.user_field2}")
        print(f"  - Custom Date: {box.custom_date}")
        print(f"  - Billing: Storage={box.charge_for_storage}, Add={box.charge_for_add}")
        print(f"  - Status: {box.item_status} / {box.state}")
        
        # Test access tracking
        initial_access = box.access_count
        box.action_increment_access()
        print(f"  - Access Count: {initial_access} → {box.access_count}")
        
        # Test status changes
        box.action_permanent_out()
        print(f"  - Status after permanent out: {box.item_status} / {box.state}")
        
        return box
    
    def demo_service_management(env):
        """Demonstrate comprehensive service management"""
        print("\n" + "="*60)
        print("DEMO: Comprehensive Service Management")
        print("="*60)
        
        # Get or create customer
        customer = env['res.partner'].search([('name', '=', 'ACME Corporation')], limit=1)
        if not customer:
            customer = env['res.partner'].create({
                'name': 'ACME Corporation',
                'is_company': True,
                'customer_rank': 1,
            })
        
        # Create various service requests matching O'Neil Stratus types
        service_types = [
            ('access', 'Access - Retrieve file from storage', 25.00),
            ('add', 'Add - New container setup', 15.00),
            ('content_val', 'Content Validation - Verify contents', 35.00),
            ('delivery', 'Delivery - Standard service', 45.00),
            ('destroy', 'Destroy - Secure destruction', 50.00),
            ('pickup', 'Pickup - Collection service', 40.00),
            ('shred_bin_64', 'Shred Bin - 64 Gallon service', 75.00),
            ('labor', 'Special - Labor service', 85.00),
        ]
        
        for service_type, description, base_rate in service_types:
            # Create service request with enhanced billing
            service = env['records.service.request'].create({
                'service_type': service_type,
                'customer_id': customer.id,
                'requested_by': customer.id,
                'description': description,
                'quantity': 2,
                'priority': 'normal',
                'state': 'submitted',
                
                # Enhanced billing fields
                'base_rate': base_rate,
                'additional_amount': 10.00,
                'discount_rate': 5.0,  # 5% discount
                'quantity_break_target': 5,
                'quantity_break_rate': base_rate * 0.9,  # 10% discount for 5+ items
                
                # O'Neil Stratus codes
                'action_code': service_type.upper()[:10],
                'object_code': 'SRV',
                'transaction_type': 'workorder',
            })
            
            print(f"✓ Created service: {service.name}")
            print(f"  - Type: {service_type}")
            print(f"  - Base Rate: ${service.base_rate:.2f}")
            print(f"  - Quantity: {service.quantity}")
            print(f"  - Discount: {service.discount_rate}% = ${service.discount_amount:.2f}")
            print(f"  - Additional: ${service.additional_amount:.2f}")
            print(f"  - Line Total: ${service.line_total:.2f}")
            print(f"  - Action Code: {service.action_code}")
            print(f"  - Transaction Type: {service.transaction_type}")
            print()
        
        # Create a quantity break example
        bulk_service = env['records.service.request'].create({
            'service_type': 'store_box',
            'customer_id': customer.id,
            'requested_by': customer.id,
            'description': 'Bulk Box Storage - Quantity Break Example',
            'quantity': 10,  # Exceeds quantity break target
            'priority': 'normal',
            'state': 'submitted',
            
            # Enhanced billing fields
            'base_rate': 20.00,
            'additional_amount': 0.00,
            'discount_rate': 0.0,
            'quantity_break_target': 5,
            'quantity_break_rate': 18.00,  # Better rate for bulk
            
            # O'Neil Stratus codes
            'action_code': 'STORE',
            'object_code': 'BOX',
            'transaction_type': 'invoice',
        })
        
        print(f"✓ Quantity Break Example: {bulk_service.name}")
        print(f"  - Quantity: {bulk_service.quantity} (exceeds target of {bulk_service.quantity_break_target})")
        print(f"  - Base Rate: ${bulk_service.base_rate:.2f}")
        print(f"  - Quantity Break Rate: ${bulk_service.quantity_break_rate:.2f}")
        print(f"  - Line Total: ${bulk_service.line_total:.2f}")
        print(f"  - Savings: ${(bulk_service.base_rate - bulk_service.quantity_break_rate) * bulk_service.quantity:.2f}")
        
        return [service.id for service in env['records.service.request'].search([('customer_id', '=', customer.id)])]
    
    def demo_barcode_configuration(env):
        """Demonstrate flexible barcode configuration"""
        print("\n" + "="*60)
        print("DEMO: Flexible Barcode Configuration")
        print("="*60)
        
        # Create barcode configurations for different types
        configs = [
            {
                'barcode_type': 'box',
                'barcode_format': 'code128',
                'fixed_length': True,
                'exact_length': 12,
                'prefix': 'BOX',
                'allow_letters': True,
                'allow_numbers': True,
                'auto_generate': True,
                'description': 'Standard box barcode with BOX prefix',
            },
            {
                'barcode_type': 'document',
                'barcode_format': 'code39',
                'fixed_length': False,
                'min_length': 8,
                'max_length': 16,
                'suffix': 'DOC',
                'allow_letters': False,
                'allow_numbers': True,
                'auto_generate': False,
                'description': 'Document barcode with DOC suffix, numbers only',
            },
            {
                'barcode_type': 'pallet',
                'barcode_format': 'qr',
                'fixed_length': True,
                'exact_length': 10,
                'prefix': 'PLT',
                'allow_letters': True,
                'allow_numbers': True,
                'allow_special': True,
                'special_chars': '-_',
                'use_check_digit': True,
                'check_digit_algorithm': 'mod10',
                'description': 'QR code for pallets with check digit',
            },
        ]
        
        for config_data in configs:
            config = env['records.barcode.config'].create(config_data)
            
            print(f"✓ Created barcode config: {config.barcode_type}")
            print(f"  - Format: {config.barcode_format}")
            print(f"  - Length: {'Fixed ' + str(config.exact_length) if config.fixed_length else f'{config.min_length}-{config.max_length}'}")
            print(f"  - Prefix: {config.prefix or 'None'}")
            print(f"  - Suffix: {config.suffix or 'None'}")
            print(f"  - Characters: Letters={config.allow_letters}, Numbers={config.allow_numbers}")
            if config.allow_special:
                print(f"  - Special chars: {config.special_chars}")
            if config.use_check_digit:
                print(f"  - Check digit: {config.check_digit_algorithm}")
            print()
            
            # Test validation
            test_barcodes = [
                'BOX123456789',  # Valid for box config
                'BOX12345678901',  # Too long for box config
                '12345678DOC',  # Valid for document config
                'ABCD1234DOC',  # Invalid for document config (has letters)
                'PLT123456-',  # Valid for pallet config
            ]
            
            for barcode in test_barcodes:
                if config.barcode_type == 'box' and barcode.startswith('BOX'):
                    valid, message = config.validate_barcode(barcode)
                    print(f"    Validation '{barcode}': {'✓' if valid else '✗'} {message}")
                elif config.barcode_type == 'document' and barcode.endswith('DOC'):
                    valid, message = config.validate_barcode(barcode)
                    print(f"    Validation '{barcode}': {'✓' if valid else '✗'} {message}")
                elif config.barcode_type == 'pallet' and barcode.startswith('PLT'):
                    valid, message = config.validate_barcode(barcode)
                    print(f"    Validation '{barcode}': {'✓' if valid else '✗'} {message}")
        
        return [config.id for config in env['records.barcode.config'].search([])]
    
    def demo_enhanced_billing(env):
        """Demonstrate enhanced billing capabilities"""
        print("\n" + "="*60)
        print("DEMO: Enhanced Billing System")
        print("="*60)
        
        # Create a billing period
        period = env['records.billing.period'].create({
            'name': 'January 2024',
            'period_start': datetime.date(2024, 1, 1),
            'period_end': datetime.date(2024, 1, 31),
            'state': 'active',
        })
        
        # Create billing configuration
        config = env['records.billing.config'].create({
            'name': 'Standard Billing 2024',
            'storage_rate': 2.50,
            'minimum_monthly_storage': 100.00,
            'active': True,
        })
        
        # Get customer
        customer = env['res.partner'].search([('name', '=', 'ACME Corporation')], limit=1)
        if not customer:
            customer = env['res.partner'].create({
                'name': 'ACME Corporation',
                'is_company': True,
                'customer_rank': 1,
            })
        
        # Create billing lines with different scenarios
        billing_scenarios = [
            {
                'line_type': 'storage',
                'description': 'Monthly Storage - 45 boxes',
                'quantity': 45,
                'unit_price': 2.50,
                'discount_percent': 0.0,
                'notes': 'Standard storage rate',
            },
            {
                'line_type': 'service',
                'description': 'Document Retrieval - Rush',
                'quantity': 3,
                'unit_price': 35.00,
                'discount_percent': 10.0,
                'notes': 'Rush service with volume discount',
            },
            {
                'line_type': 'minimum_fee',
                'description': 'Minimum Monthly Fee Adjustment',
                'quantity': 1,
                'unit_price': -12.50,  # Negative adjustment
                'discount_percent': 0.0,
                'notes': 'Customer exceeded minimum threshold',
            },
        ]
        
        total_amount = 0.0
        for scenario in billing_scenarios:
            billing_line = env['records.billing.line'].create({
                'period_id': period.id,
                'customer_id': customer.id,
                'billing_config_id': config.id,
                **scenario
            })
            
            line_total = billing_line.quantity * billing_line.unit_price
            if billing_line.discount_percent > 0:
                line_total *= (1 - billing_line.discount_percent / 100)
            
            total_amount += line_total
            
            print(f"✓ Created billing line: {billing_line.description}")
            print(f"  - Type: {billing_line.line_type}")
            print(f"  - Quantity: {billing_line.quantity}")
            print(f"  - Unit Price: ${billing_line.unit_price:.2f}")
            print(f"  - Discount: {billing_line.discount_percent}%")
            print(f"  - Line Total: ${line_total:.2f}")
            print(f"  - Notes: {billing_line.notes}")
            print()
        
        print(f"Total Monthly Bill: ${total_amount:.2f}")
        
        return period.id
    
    def main():
        """Main demonstration function"""
        print("🚀 Starting O'Neil Stratus Compatibility Demo")
        print("="*60)
        
        # Initialize Odoo
        odoo.tools.config.parse_config([])
        odoo.service.db.create_db('demo_db')
        
        with odoo.registry('demo_db').cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            
            try:
                # Install the module
                module = env['ir.module.module'].search([('name', '=', 'records_management')])
                if module.state != 'installed':
                    module.button_immediate_install()
                
                # Run demonstrations
                demo_enhanced_box_management(env)
                demo_service_management(env)
                demo_barcode_configuration(env)
                demo_enhanced_billing(env)
                
                print("\n" + "="*60)
                print("✅ O'Neil Stratus Compatibility Demo Complete!")
                print("="*60)
                print("\nKey Features Demonstrated:")
                print("1. ✓ Enhanced Container/Box Management")
                print("2. ✓ Comprehensive Service Types")
                print("3. ✓ Flexible Barcode Configuration")
                print("4. ✓ Advanced Billing with Quantity Breaks")
                print("5. ✓ Status Tracking and Access Control")
                print("6. ✓ Account Hierarchy Management")
                print("\nThe Records Management module is now fully compatible")
                print("with O'Neil Stratus functionality and provides additional")
                print("modern web-based capabilities!")
                
            except Exception as e:
                print(f"❌ Error during demo: {e}")
                logger.exception("Demo failed")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Error importing Odoo: {e}")
    print("Please ensure Odoo is properly installed and configured.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
