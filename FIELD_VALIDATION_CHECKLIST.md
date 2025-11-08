# Field Validation Checklist for View Generation

## 🎯 Lesson from Error 34

**Error 34 (Mobile Photo Views)** revealed a critical gap in the view generation process:
- Generated views with field names not matching model definitions
- Non-existent fields referenced (image_data, capture_date, mime_type, etc.)
- Should have validated EVERY field before deploying

**Solution:** Implement validation gate before EVERY view file deployment.

---

## ✅ Pre-Deployment Field Validation Process

### STEP 1: Read the Python Model Definition
```bash
# Open the model file
code records_management/models/mobile_photo.py

# Scan for all field definitions (look for fields.*)
# Note EXACT field names: photo_data, photo_date, file_size, resolution, etc.
```

### STEP 2: Extract All Available Fields
Create a list of ACTUAL fields in the model:
```python
# Example from mobile.photo:
ACTUAL_FIELDS = {
    'name': Char,
    'photo_data': Binary,
    'photo_date': Datetime,
    'photo_filename': Char,
    'file_size': Integer,
    'resolution': Char,
    'gps_latitude': Float,
    'gps_longitude': Float,
    'has_gps': Boolean,
    'photo_type': Selection,
    'device_info': Char,
    'fsm_task_id': Many2one,
    'work_order_reference': Reference,
    'container_id': Many2one,
    'destruction_request_id': Many2one,
    'pickup_request_id': Many2one,
    'partner_id': Many2one,
    'bin_issue_id': Many2one,
    'is_compliance_photo': Boolean,
    'compliance_notes': Text,
    'wizard_reference': Reference,
    'project_id': Many2one,
    'active': Boolean,
    'company_id': Many2one,
    'message_follower_ids': Many2many,
    'message_ids': One2many,
    'activity_ids': One2many,
}
```

### STEP 3: Generate View XML Using ONLY These Fields
For each view (Form, List, Search, Kanban, etc.):
- ✅ Reference ONLY fields from the ACTUAL_FIELDS list above
- ❌ NEVER reference fields not in this list
- ❌ NEVER use alternate names (image_data when actual is photo_data)

### STEP 4: Validate Generated XML
Before saving the view file:
```bash
# Check each field reference against model
grep -o 'name="[^"]*"' view_file.xml | \
    grep field | \
    sed 's/.*name="\([^"]*\)".*/\1/' | \
    sort | uniq
```

### STEP 5: Cross-Reference Against Model
For each field in the XML:
1. Open model file in split view
2. Search for `field_name = fields.`
3. If NOT FOUND → REMOVE from view or replace with correct name

### STEP 6: Deploy Only After Validation Passes
```bash
# Commit only after manual inspection
git add views/model_name_views.xml
git commit -m "feat: Add view definitions for model.name

- Validated ALL fields against models/model_name.py
- Fields used: [list 5-10 key fields]
- No non-existent field references"
```

---

## 🚀 PHASE 1: Container & Location Views (NEXT)

### records_container_views.xml
**Model:** records.container (records_management/models/records_container.py)

**BEFORE generating view, extract model fields:**
```bash
grep "= fields\." records_management/models/records_container.py | head -20
```

**THEN validate each field in view matches one of these**

**Key fields likely in model:**
- name, display_name
- status, active, company_id
- container_type_id, container_code
- location_id, department_id
- capacity_liters, current_weight
- container_status
- partner_id (customer)
- retention_date, expiry_date
- document_count

### records_location_views.xml
**Model:** records.location (records_management/models/records_location.py)

**BEFORE generating view, extract model fields:**
```bash
grep "= fields\." records_management/models/records_location.py | head -20
```

### records_department_views.xml
**Model:** records.department (records_management/models/records_department.py)

**BEFORE generating view, extract model fields:**
```bash
grep "= fields\." records_management/models/records_department.py | head -20
```

---

## ⚠️ Common Mistakes (Learned from Error 34)

| ❌ MISTAKE | ✅ FIX |
|-----------|-------|
| Using `image_data` when model has `photo_data` | Search model for correct field name |
| Referencing `capture_date` when model has `photo_date` | Compare field names - look for similar patterns |
| Adding fields like `mime_type` that don't exist | Only use fields from model definition grep |
| Copying field names from CSV export without checking model | CSV is reference only - truth is Python model |
| Not removing non-existent fields before deploying | Always validate before git commit |

---

## 🔄 Validation Workflow Template

Use this for EVERY view file before deployment:

```bash
# Step 1: Open model and view side-by-side
code models/MODEL_NAME.py
code views/MODEL_NAME_views.xml

# Step 2: Extract fields from model
grep "= fields\." models/MODEL_NAME.py | sed 's/.*\(\w\+\) = fields\..*/\1/' > /tmp/model_fields.txt

# Step 3: Extract fields from view
grep -o 'name="[^"]*"' views/MODEL_NAME_views.xml | \
    sed 's/.*name="\([^"]*\)".*/\1/' | \
    grep -v "^$" > /tmp/view_fields.txt

# Step 4: Find mismatches
echo "=== Fields in view but NOT in model ==="
comm -23 <(sort /tmp/view_fields.txt) <(sort /tmp/model_fields.txt)

# Step 5: If ANY output in step 4 → FIX before committing
```

---

## 📋 Pre-Deployment Checklist

Before `git commit` for ANY view file, verify:

- [ ] Read Python model file completely
- [ ] Created list of ACTUAL field names
- [ ] For EVERY field in view XML:
  - [ ] Checked field name against model
  - [ ] Name matches exactly (case-sensitive)
  - [ ] Field type makes sense (Many2one with comodel_name, etc.)
- [ ] Removed ANY non-existent fields
- [ ] Fixed ANY mis-named fields
- [ ] Ran validation commands above
- [ ] NO mismatches found
- [ ] Only THEN committed with clear message

---

## 🎓 Why This Matters

**Error 34 Stats:**
- 11 non-existent field references
- 0 validation before deployment
- Result: Deployment failed, Odoo.sh error

**With This Checklist:**
- 0 errors before deployment
- 100% field validation
- Result: Successful deployments on first try

---

## 🔍 Quick Reference: Extract Model Fields

```bash
# For any model, quickly see all fields:
grep -E "^\s+\w+\s*=\s*fields\." records_management/models/MODEL_NAME.py | \
    sed -E 's/^\s+(\w+).*/\1/' | \
    sort
```

---

**NEXT TASK:** Apply this checklist to records_container_views.xml before generating Phase 1 views.
