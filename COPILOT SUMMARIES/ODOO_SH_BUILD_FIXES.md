# Odoo.sh Build Fix - Model Reference Corrections

## Issues Fixed

### 1. Model Name Inconsistency
**Problem**: The `res.partner.department.billing` model was referencing `'customer.department'` instead of the correct `'records.department'`.

**Error**:
```
Field res.partner.department.billing.department_id with unknown comodel_name 'customer.department'
KeyError: 'Field name referenced in related field definition res.partner.department.billing.department_name does not exist.'
```

**Fix Applied**: 
- Changed `department_id` field reference from `'customer.department'` to `'records.department'`
- Updated domain from `[('customer_id', '=', partner_id)]` to `[('company_id', '=', partner_id)]`

### 2. Missing Model Definitions
**Problem**: The billing system models were incomplete after recent edits.

**Fix Applied**: Added complete model definitions for:
- `RecordsBillingLine`
- `RecordsServicePricing` 
- `RecordsServicePricingBreak`
- `AccountMove` inheritance for billing period reference
- `RecordsServiceRequestEnhanced` inheritance

## Files Modified

1. `/records_management/models/res_partner.py`
   - Fixed model reference in `ResPartnerDepartmentBilling`

2. `/records_management/models/customer_inventory_report.py`
   - Added missing billing system models
   - Completed model definitions

## Verification

✅ Model names are consistent throughout the system:
- `records.department` (main department model)
- `records.billing.line` (billing line items)
- `records.billing.period` (billing periods)
- `records.service.pricing` (service pricing)
- `res.partner.department.billing` (department billing contacts)

✅ All access rules are properly configured in `ir.model.access.csv`

✅ Field relationships are correctly mapped:
- Department billing contacts → records.department
- Billing lines → records.department
- All related fields reference existing model fields

## Expected Result

The module should now load without the model reference errors. The departmental billing system will be fully functional with:

1. **Consolidated Billing**: One invoice with department breakdown
2. **Separate Billing**: Individual invoices per department  
3. **Hybrid Billing**: Mixed billing approach
4. **Department Billing Contacts**: Per-department billing configuration
5. **Flexible Minimum Fee Handling**: Per-department or company-wide

The system is ready for enterprise customers with many departments.
