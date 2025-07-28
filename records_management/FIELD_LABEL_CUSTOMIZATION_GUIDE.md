# Field Label Customization System

## Overview

The Field Label Customization system allows different admin levels (Global, Customer, Department) to customize field names/labels to match their organization's terminology. This is especially useful since different companies may have different terms for the same concepts.

## Admin Hierarchy

The system supports three levels of customization with priority order:

1. **Department Level** (Priority 30) - Highest priority
2. **Customer Level** (Priority 20) - Medium priority  
3. **Global Level** (Priority 10) - Lowest priority

Higher priority configurations override lower priority ones.

## Key Features

### 1. Industry Presets

- **Corporate Standard**: Standard business terminology
- **Legal Industry**: Legal/law firm terminology
- **Healthcare**: Medical/HIPAA terminology  
- **Financial Services**: Banking/financial terminology

### 2. Customizable Fields

All major transitory item fields can be customized:

- Box Number → File Box ID, Matter Box, etc.
- Item Description → Document Category, Case Documents, etc.
- Date ranges, confidentiality levels, project codes, etc.

### 3. Portal Integration

- Customer portal forms automatically use custom labels
- JavaScript widget dynamically updates field labels
- API endpoints provide label data to frontend

## Setup Instructions

### For Records Center Admins (Global Configuration)

1. **Navigate to Configuration**

   ```
   Records Management → Configuration → Field Label Customization
   ```

2. **Create Global Configuration**
   - Leave Customer and Department fields empty
   - Set priority to 10 (default for global)
   - Apply industry preset or customize individually

3. **Apply Industry Preset**
   - Use preset buttons: Corporate, Legal, Healthcare, Financial
   - Or manually customize each field label

### For Company Admins (Customer-Specific)

1. **From Customer Record**

   ```
   Customers → [Select Customer] → Records Field Configuration tab
   → "Customize Field Labels" button
   ```

2. **Create Customer Configuration**
   - Customer field auto-populated
   - Set priority to 20 (default for customer)
   - Customize labels for your organization

### For Department Admins

1. **From Customer Configuration**
   - Create configuration with both Customer AND Department set
   - Set priority to 30 (highest)
   - Customize for specific department needs

## Usage Examples

### Example 1: Legal Firm

```
Box Number → Matter Box
Item Description → Case Documents  
Date From → Case Start Date
Confidentiality → Attorney-Client Privilege
Project Code → Matter Code
```

### Example 2: Healthcare

```
Box Number → Medical Records Box
Item Description → Patient Records
Confidentiality → HIPAA Classification
Project Code → Department Code
Client Reference → Patient ID
```

### Example 3: Corporate

```
Box Number → File Box ID
Item Description → Document Category
Date From → Period Start
Project Code → Cost Center
Authorized By → Department Head
```

## Technical Integration

### Portal Forms

Add this to portal templates to enable custom labels:

```html
<div class="o_portal_field_customizer" 
     data-customer-id="{{ customer.id }}"
     data-department-id="{{ department.id if department else '' }}">
     
    <label data-field-name="box_number">Box Number</label>
    <input name="box_number" data-field-name="box_number" />
    
</div>
```

### API Endpoints

- `/portal/field-labels/get` - Get custom labels
- `/portal/field-labels/transitory-config` - Get full field config
- `/records/admin/field-labels/preview` - Admin preview

### Python API

```python
# Get labels for customer
labels = env['field.label.customization'].get_labels_for_context(
    customer_id=customer.id,
    department_id=department.id
)

# Get specific field label
label = env['field.label.customization'].get_label_for_field(
    'box_number', customer_id, department_id
)
```

## Benefits

1. **Improved User Experience**: Users see familiar terminology
2. **Industry Compliance**: Match industry-standard terminology
3. **Reduced Training**: Less confusion with field names
4. **Flexible Administration**: Multiple admin levels can customize
5. **Portal Integration**: Seamless portal experience

## Best Practices

1. **Start with Presets**: Use industry presets as starting points
2. **Test with Users**: Validate terminology with actual users
3. **Document Changes**: Keep record of customizations made
4. **Consistent Naming**: Use consistent terminology across organization
5. **Regular Review**: Periodically review and update labels as needed

## Troubleshooting

### Labels Not Appearing

1. Check configuration priority levels
2. Verify customer/department associations
3. Clear browser cache for portal users
4. Check JavaScript console for errors

### Wrong Labels Showing

1. Review configuration hierarchy
2. Check for conflicting configurations
3. Verify priority settings
4. Test with preview function

## Future Enhancements

1. **Translation Support**: Multi-language label support
2. **Field Descriptions**: Custom help text/descriptions
3. **Validation Messages**: Custom validation error messages
4. **Export/Import**: Configuration backup/restore
5. **Template Library**: Shared industry templates
