# Portal Template-Controller Field Audit - Fix Summary

**Date**: November 23, 2025  
**Version**: 18.0.1.0.26  
**Total Issues Found**: 34  

## Critical Issues by Template

### 1. portal_containers.xml (6 issues)
**Template ID**: `portal_container_form`  
**Controller Route**: Should be `/my/inventory/containers/create` (currently `/my/containers/create`)  
**Controller File**: `portal.py` @ line 1915

**Issues**:
- ✗ t-foreach variable `container_types` - **FIXED** (already in controller line 1941)
- ✗ t-foreach variable `locations` - **FIXED** (already in controller line 1938)
- ✗ Form action URL mismatch - **NEEDS FIX**
- ✗ POST field `custom_barcode` not handled - **NEEDS FIX**
- ✗ POST field `generate_barcode` not handled - **NEEDS FIX**
- ✗ POST field `department_id` - **ALREADY HANDLED** (line 1953)
- ✗ POST field `container_type_id` - **ALREADY HANDLED** (line 1952)

**Fixes Required**:
1. Change form action in `portal_containers.xml` line 18:  
   FROM: `action="/my/containers/create"`  
   TO: `action="/my/inventory/containers/create"`

2. Add POST handling in `portal.py` at line ~1998:
   ```python
   # Handle barcode generation
   if post.get('generate_barcode'):
       container_vals['barcode'] = request.env['ir.sequence'].next_by_code('records.container') or '/'
   elif post.get('custom_barcode'):
       container_vals['barcode'] = post.get('custom_barcode')
   ```

---

### 2. portal_document_bulk_upload.xml (3 issues)
**Controller File**: `portal_document_bulk_upload.py`  
**Controller Route**: `/my/bulk-upload`

**Issues**:
- ✗ POST field `upload_file` not handled - **NEEDS FIX**
- ✗ POST field `has_header` not handled - **NEEDS FIX**
- ✗ POST field `partner_id` not handled - **NEEDS FIX**

**Fixes Required**:
Add POST handling after line 35 in `portal_document_bulk_upload.py`:
```python
if request.httprequest.method == 'POST':
    try:
        upload_file = request.httprequest.files.get('upload_file')
        has_header = post.get('has_header', False)
        partner_id = post.get('partner_id')
        
        if not upload_file:
            values['error'] = _('No file uploaded')
            return request.render('records_management.portal_document_bulk_upload', values)
        
        # Process CSV file
        file_content = upload_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(file_content)) if has_header else csv.reader(StringIO(file_content))
        
        # Process rows...
        
    except Exception as e:
        values['error'] = str(e)
```

---

### 3. portal_file_create.xml (8 issues)
**Controller Route**: `/my/inventory/files/create`  
**Controller File**: `portal.py`

**Issues**:
- ✗ POST field `name` not handled
- ✗ POST field `barcode` not handled
- ✗ POST field `container_id` not handled
- ✗ POST field `department_id` not handled
- ✗ POST field `file_category` not handled
- ✗ POST field `date_created` not handled
- ✗ POST field `received_date` not handled
- ✗ POST field `state` not handled

**Fixes Required**:
Need to find/create the `/my/inventory/files/create` route and add POST handling.

---

### 4. portal_work_order_templates.xml (9 issues)
**Controller File**: `work_order_portal.py`  
**Controller Route**: `/my/work-orders/create`

**Issues**:
- ✗ POST field `service_type` not handled
- ✗ POST field `priority` not handled
- ✗ POST field `preferred_date` not handled
- ✗ POST field `preferred_time` not handled
- ✗ POST field `contact_name` not handled
- ✗ POST field `contact_phone` not handled
- ✗ POST field `contact_email` not handled
- ✗ POST field `photo_upload` not handled
- ✗ POST field `document_upload` not handled

**Fixes Required**:
Add complete POST handling in `work_order_portal.py` for work order creation.

---

### 5. portal_staging_location_forms.xml (4 issues)
**Controller Route**: `/my/inventory/locations/create`

**Issues**:
- ✗ POST field `name` not handled
- ✗ POST field `location_type` not handled
- ✗ POST field `department_id` not handled
- ✗ POST field `parent_id` not handled

**Fixes Required**:
Create/verify location creation route with full POST handling.

---

### 6. portal_staging_location_edit.xml (4 issues)
**Controller Route**: `/my/inventory/location/<id>/edit`

**Issues**:
- Same 4 fields as creation form

**Fixes Required**:
Add POST handling for location edit route.

---

## Implementation Priority

### HIGH PRIORITY (Breaking Functionality)
1. **portal_containers.xml** - Fix form action URL
2. **portal_containers.xml** - Add barcode generation handling
3. **portal_document_bulk_upload.xml** - Add file upload processing

### MEDIUM PRIORITY (Forms Don't Submit)
4. **portal_file_create.xml** - Create file creation route
5. **portal_work_order_templates.xml** - Complete work order creation
6. **portal_staging_location_forms.xml** - Location creation

### LOW PRIORITY (Edit Forms)
7. **portal_staging_location_edit.xml** - Location editing

---

## Testing Checklist

After fixes, test each form:
- [ ] Container creation form submits successfully
- [ ] Bulk upload processes CSV files
- [ ] File creation form works
- [ ] Work order creation submits
- [ ] Location creation works
- [ ] Location editing works
- [ ] All dropdowns populate correctly
- [ ] No 500 errors on form submission

---

## Next Steps

1. Apply HIGH PRIORITY fixes first
2. Test each fix individually
3. Commit incrementally with clear messages
4. Run `python3 development-tools/portal_field_audit.py` after each fix to verify

