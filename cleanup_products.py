#!/usr/bin/env python3
"""
Database cleanup script for Records Management module
This script helps clean up duplicate product records that may cause 
constraint violations during module installation.

Usage:
1. Install the module with minimal products.xml first
2. Run this script to clean up any duplicate records
3. Replace products.xml with the full version
4. Upgrade the module

This script should be run in an Odoo environment.
"""

import logging
_logger = logging.getLogger(__name__)

def cleanup_product_duplicates(env):
    """
    Clean up duplicate product records that may interfere with module installation.
    """
    try:
        # Find duplicate product variants
        duplicate_products = env['product.product'].search([
            ('default_code', 'in', ['REC-BOX', 'REC-FILE', 'REC-STOR-SVC', 'REC-SHRED-SVC',
                                   'REC-BOX-001', 'REC-FILE-001', 'REC-STOR-SVC-001', 'REC-SHRED-SVC-001'])
        ])
        
        if duplicate_products:
            _logger.info(f"Found {len(duplicate_products)} potentially duplicate products")
            for product in duplicate_products:
                _logger.info(f"Product: {product.name} (ID: {product.id}, Code: {product.default_code})")
        
        # Find duplicate product templates
        duplicate_templates = env['product.template'].search([
            ('default_code', 'in', ['REC-BOX', 'REC-FILE', 'REC-STOR-SVC', 'REC-SHRED-SVC',
                                   'REC-BOX-001', 'REC-FILE-001', 'REC-STOR-SVC-001', 'REC-SHRED-SVC-001'])
        ])
        
        if duplicate_templates:
            _logger.info(f"Found {len(duplicate_templates)} potentially duplicate product templates")
            for template in duplicate_templates:
                _logger.info(f"Template: {template.name} (ID: {template.id}, Code: {template.default_code})")
        
        # Option to delete duplicates (commented out for safety)
        # UNCOMMENT ONLY IF YOU WANT TO DELETE THE RECORDS
        # for product in duplicate_products:
        #     product.unlink()
        # for template in duplicate_templates:
        #     template.unlink()
        # env.cr.commit()
        
        return True
        
    except Exception as e:
        _logger.error(f"Error during cleanup: {str(e)}")
        return False

def main():
    """
    Main function - this would be called in an Odoo shell session
    Example: 
    $ odoo-bin shell -d your_database
    >>> exec(open('cleanup_products.py').read())
    >>> cleanup_product_duplicates(env)
    """
    # This would be available in an Odoo shell session
    if 'env' in globals():
        return cleanup_product_duplicates(env)
    else:
        print("This script must be run in an Odoo shell environment")
        print("Usage: odoo-bin shell -d your_database")
        print("Then run: exec(open('cleanup_products.py').read())")
        return False

if __name__ == "__main__":
    main()
