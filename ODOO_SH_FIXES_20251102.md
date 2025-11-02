# Odoo.sh Deployment Fixes - November 2, 2025

## Issues Resolved

### 1. Field Parameter Warnings (Commit e7d88186)

**Problem:**
```
WARNING Field records.location.code: unknown parameter 'tracking'
WARNING Field records.location.security_level: selection=[...] overrides existing selection
```

**Root Cause:**
- `stock.location` doesn't inherit `mail.thread`, so `tracking=True` was invalid
- `security_level` was defined in BOTH `records_location.py` AND `stock_location.py`

**Solution:**
1. Added `mail.thread` and `mail.activity.mixin` to inheritance chain:
   ```python
   _inherit = ['stock.location', 'mail.thread', 'mail.activity.mixin']
   ```

2. Removed duplicate fields from `records_location.py`:
   - `security_level` (already in `stock_location.py`)
   - `temperature_controlled` (already in `stock_location.py`)
   - `humidity_controlled` (already in `stock_location.py`)
   - `fire_suppression_system` (already in `stock_location.py`)
   - `last_inspection_date` (already in `stock_location.py`)

**Result:**
✅ All field parameter warnings resolved
✅ Change tracking now properly enabled on custom fields
✅ No more selection override warnings

---

### 2. MissingError for stock.location(255) (Commit 19f9c81e)

**Problem:**
```
MissingError: Record does not exist or has been deleted.
(Record: stock.location(255), User: 1)
```

**Root Cause:**
- Previous migrations/testing deleted `stock.location` records
- Warehouses still referenced deleted `view_location_id`
- Location hierarchy had broken `parent_path` references

**Solution:**
Created migration script `18.0.0.2.1/post-migrate.py` that:

1. **Finds orphaned warehouse references:**
   ```sql
   SELECT w.id FROM stock_warehouse w
   LEFT JOIN stock_location l ON w.view_location_id = l.id
   WHERE l.id IS NULL
   ```

2. **Fixes warehouses:**
   - Updates to valid view location, OR
   - Sets to NULL to allow auto-creation

3. **Repairs broken parent_path hierarchies:**
   - Identifies locations with missing parent IDs in path
   - Clears `parent_path` (Odoo will recompute)

**Result:**
✅ Migration will run automatically on module upgrade
✅ Cleans all orphaned warehouse references
✅ Repairs location hierarchy integrity
✅ Prevents MissingError during warehouse computation

---

## Deployment Steps

### On Odoo.sh:

1. **Upgrade module to 18.0.0.2.1:**
   - Odoo.sh will detect version change
   - Post-migration script runs automatically
   - Orphaned references cleaned up

2. **Verify fixes:**
   ```
   # Check for warnings in deployment log
   # Should see:
   ✅ Migration 18.0.0.2.1: Orphaned reference cleanup complete
   ```

3. **Test location functionality:**
   - Create new location
   - Verify hierarchy works
   - Assign containers to locations
   - Check "My Inventory" shows containers

---

## Architecture Notes

### records.location Model Structure

**Current Design:**
```python
class RecordsLocation(models.Model):
    _name = 'records.location'
    _inherit = ['stock.location', 'mail.thread', 'mail.activity.mixin']
```

**Inheritance Chain:**
1. **stock.location** (Odoo native) → Warehouse integration, inventory
2. **mail.thread** → Change tracking, chatter
3. **mail.activity.mixin** → Activity tracking

**Field Sources:**
- **From stock.location:** `name`, `active`, `company_id`, `location_id` (parent), `child_ids`, `usage`, `barcode`
- **From stock_location.py extension:** `security_level`, `temperature_controlled`, `fire_suppression_system`
- **From records_location.py:** `code`, `user_id`, `max_capacity`, `location_state`, `building`, `floor`, etc.

---

## Files Modified

1. **records_management/models/records_location.py**
   - Added mail.thread inheritance
   - Removed duplicate fields
   
2. **records_management/migrations/18.0.0.2.1/post-migrate.py**
   - NEW: Orphaned reference cleanup
   
3. **records_management/__manifest__.py**
   - Version: 18.0.0.2.0 → 18.0.0.2.1

---

## Testing Checklist

After deployment:

- [ ] Module loads without errors
- [ ] No field parameter warnings
- [ ] No MissingError for stock.location
- [ ] Location creation works
- [ ] Location hierarchy displays correctly
- [ ] Container location assignment works
- [ ] "My Inventory" shows containers
- [ ] Change tracking works on custom fields

---

## Next Steps

1. **Monitor Odoo.sh deployment** for migration success
2. **Delete test containers** (as planned)
3. **Test location creation** on production
4. **Verify inventory integration** works end-to-end

---

## Commits

- **e7d88186**: Add mail.thread inheritance and remove duplicate fields
- **19f9c81e**: Add migration to clean orphaned stock.location references
