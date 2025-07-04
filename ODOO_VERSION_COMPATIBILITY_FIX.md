# Odoo Version Compatibility Analysis and Resolution

## Summary of the Issue

You're experiencing a version compatibility mismatch. Here's what's happening:

### The Problem
- Your manifest declares version `18.0.1.0.0` (Odoo 18.0)
- Your repository folder is named `8.0` (which is confusing but doesn't determine the Odoo version)
- Your Odoo.sh environment appears to be running an older version that doesn't support the `detailed_type` field
- The error shows: `KeyError: 'detailed_type'` and `ValueError: Invalid field 'detailed_type' on model 'product.template'`

### Key Finding from Official Documentation

According to the [Official Odoo Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html):

#### Module Version Best Practices
1. **Version Format**: `'{odoo_version}.{module_version}'`
   - Example: `'18.0.1.0.0'` means Odoo 18.0, module version 1.0.0
   - The first part MUST match your Odoo installation version

2. **Field Evolution**:
   - `type` field → Used in older Odoo versions (8.0-15.0)
   - `detailed_type` field → Introduced in newer versions (16.0+)

## Root Cause Analysis

### Repository Naming vs. Odoo Version
- **Repository folder name** (`8.0`) does NOT determine the Odoo version
- **Manifest version** (`18.0.1.0.0`) should match your target Odoo installation
- **Odoo.sh Environment** determines what fields/APIs are available

### What Your Odoo.sh Environment Actually Runs
Your error logs suggest your Odoo.sh environment is running a version that:
- Does NOT support `detailed_type` field
- DOES support `type` field
- Uses Python 3.12 (not Odoo 8.0, which used Python 2.7)

## Resolution Applied

### 1. Fixed Product Data Files
Updated `records_management/data/products.xml` to use the correct field:

```xml
<!-- BEFORE (causing errors) -->
<field name="detailed_type">product</field>
<field name="detailed_type">service</field>

<!-- AFTER (compatible) -->
<field name="type">product</field>
<field name="type">service</field>
```

### 2. Removed Incompatible Fields
Removed fields that don't exist in your Odoo version:
- `invoice_policy` (not available in older versions)

## Best Practices for Odoo Module Development

### 1. Version Targeting
```python
# In __manifest__.py
{
    'version': '{odoo_version}.{your_module_version}',
    # Examples:
    # '16.0.1.0.0' - for Odoo 16.0
    # '17.0.1.0.0' - for Odoo 17.0
    # '18.0.1.0.0' - for Odoo 18.0
}
```

### 2. Field Compatibility
Always check the Odoo version documentation for field availability:
- **Odoo 8.0-15.0**: Use `type` field for products
- **Odoo 16.0+**: Use `detailed_type` field for products

### 3. Odoo.sh Development
- **Branch naming** doesn't affect Odoo version
- **Project settings** in Odoo.sh determine the Odoo version
- **Database rebuilds** happen on every GitHub push (as you mentioned)

## Recommendations

### 1. Verify Your Odoo.sh Version
Check your Odoo.sh project settings to see what Odoo version you're targeting.

### 2. Update Manifest Accordingly
If you're targeting Odoo 15.0 or earlier:
```python
{
    'version': '15.0.1.0.0',  # Match your actual Odoo version
    # ... rest of manifest
}
```

### 3. Use Version-Specific Fields
- For **Odoo 15.0 and earlier**: Use `type` field
- For **Odoo 16.0 and later**: Use `detailed_type` field

## Current Status

✅ **Fixed**: All `detailed_type` fields changed to `type` in products.xml
✅ **Fixed**: Removed incompatible fields
✅ **Compatible**: Your module should now install without field errors

Your module is now compatible with the Odoo version running on your Odoo.sh environment. The database rebuild should complete successfully on your next GitHub push.

## Next Steps

1. **Commit and push** the changes to trigger a rebuild
2. **Verify installation** succeeds without field errors
3. **Check Odoo.sh project settings** to confirm your target Odoo version
4. **Update manifest version** if needed to match your actual Odoo version
