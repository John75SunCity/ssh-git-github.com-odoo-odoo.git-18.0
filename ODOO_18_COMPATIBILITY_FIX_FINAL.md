# Odoo 18.0 Compatibility Fix - Records Management Module

## Issue Summary
The Records Management module was experiencing database constraint violations when installing on Odoo 18.0/Odoo.sh, specifically:
- `ValueError` for invalid `product.template.type` field values
- `IntegrityError` for duplicate key violations on product variants

## Root Causes Identified

### 1. Invalid Product Type Field Values
**Problem**: The module was using deprecated field names and values from older Odoo versions:
- Field `detailed_type` instead of `type`
- Values like `storable` and `goods` which are invalid in Odoo 18.0

**Solution**: Updated products.xml to use correct Odoo 18.0 field names and values:
- Changed `detailed_type` to `type`
- Used valid values: `consu` (consumable) and `service`

### 2. Duplicate Product Variant Creation
**Problem**: The module was explicitly defining both `product.template` and `product.product` records, but Odoo 18.0 automatically creates product variants when templates are created, causing constraint violations.

**Solution**: Removed all explicit `product.product` records from products.xml, keeping only `product.template` records.

## Files Modified

### 1. /records_management/data/products.xml
- **Changed**: Field names from `detailed_type` to `type`
- **Changed**: Field values to valid Odoo 18.0 values (`consu`, `service`)
- **Removed**: All explicit `product.product` variant records
- **Added**: Unique external IDs with module prefix
- **Added**: `forcecreate="False"` attributes to prevent forced creation

### 2. Backup Files Created
- `/records_management/data/products_full.xml` - Full product definitions for future use
- `/records_management/data/products_minimal.xml` - Empty file for testing
- `/cleanup_products.py` - Database cleanup script

## Current State

The module now loads with a minimal products.xml file (no product records) to avoid database conflicts. This allows the module to install successfully while we ensure the database is clean.

## Next Steps for Complete Resolution

### Option 1: Gradual Installation (Recommended)
1. Install module with current minimal products.xml
2. Verify module loads without errors
3. Clean database of any existing duplicate products
4. Replace products.xml with products_full.xml
5. Upgrade module to load product data

### Option 2: Database Cleanup (If needed)
If duplicate records persist from previous failed installs:
1. Use the cleanup_products.py script in an Odoo shell
2. Manually remove conflicting product records via database
3. Restore products.xml and upgrade module

## Technical Details

### Valid Product Types in Odoo 18.0
- `consu` - Consumable product (tracked as stock but no inventory)
- `product` - Storable product (full inventory tracking)
- `service` - Service (no stock tracking)

### Database Constraints
The `product_product_combination_unique` constraint ensures that each product template can only have one variant with the same attribute combination. The conflict occurred because:
1. Manual product.product records were created with specific IDs
2. Odoo auto-generation tried to create variants with the same template+combination
3. Database rejected the duplicate

## Verification Steps
1. Check Odoo.sh logs for successful module installation
2. Verify no database constraint errors
3. Test module functionality in Odoo interface
4. Gradually restore product data as needed

## Contact
For questions about these changes, refer to the git commit history or create an issue in the repository.
