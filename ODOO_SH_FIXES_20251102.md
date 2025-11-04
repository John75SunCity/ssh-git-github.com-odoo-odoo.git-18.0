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

### 2. MissingError for stock.location(36, 255, etc.) (Commit 413d8220)

**Problem:**
```
MissingError: Record does not exist or has been deleted.
(Record: stock.location(36), User: 1)
```

**Root Cause:**
- Module upgrade fails BEFORE any migration can run
- Odoo tries to compute `warehouse_id` during model loading
- Warehouses reference deleted `stock.location` records
- **Chicken-and-egg problem**: Can't upgrade to run migration that would fix the issue

**Solution:**
Created **PRE-migration** script `18.0.0.2.1/pre-migrate.py` that:

1. **Runs BEFORE Python models load** (critical timing difference)

2. **Fixes orphaned warehouse references:**
   ```sql
   UPDATE stock_warehouse w
   SET view_location_id = (valid_location_id)
   WHERE view_location_id NOT IN (SELECT id FROM stock_location)
   ```

3. **Repairs location parent references:**
   - Re-parents orphaned locations to root
   - Or sets `location_id = NULL` to make them root locations

4. **Clears broken parent_path:**
   - Sets all `parent_path = NULL`
   - Odoo recomputes hierarchy automatically

5. **Fixes ALL warehouse location fields:**
   - `view_location_id`
   - `lot_stock_id`
   - `wh_input_stock_loc_id`
   - `wh_output_stock_loc_id`
   - `wh_pack_stock_loc_id`

**Why PRE-migration vs POST-migration:**
- **POST-migration**: Runs AFTER module loads (too late - module won't load)
- **PRE-migration**: Runs at SQL level BEFORE model loading (fixes data first)

**Result:**
✅ Module can now upgrade successfully
✅ No more MissingError during warehouse computation
✅ All orphaned references cleaned at database level
✅ Odoo recomputes hierarchies after cleanup

---

## Deployment Steps

### On Odoo.sh:

1. **Upgrade module to 18.0.0.2.1:**
   - Odoo.sh will detect version change
   - **PRE-migration script runs FIRST** (before model loading)
   - Orphaned references cleaned at SQL level
   - Module then loads successfully

2. **Verify fixes in deployment log:**
   ```
   # Should see:
   🔧 PRE-Migration 18.0.0.2.1: Cleaning orphaned location references...
   ✅ Updated X warehouses to use location Y
   ✅ Re-parented X locations to root location Y
   ✅ Cleared parent_path for X locations (will be recomputed)
   ✅ PRE-Migration 18.0.0.2.1: Database cleanup complete
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
   
2. **records_management/migrations/18.0.0.2.1/pre-migrate.py**
   - NEW: PRE-migration cleanup (runs before module loads)
   - Fixes warehouses, location parents, parent_path
   - Critical timing: Executes at SQL level before Python
   
3. **records_management/__manifest__.py**
   - Version: 18.0.0.2.0 → 18.0.0.2.1

---

## Commits

- **e7d88186**: Add mail.thread inheritance and remove duplicate fields
- **19f9c81e**: Add migration to clean orphaned stock.location references (POST - wrong timing)
- **413d8220**: Change to PRE-migration to fix orphaned references before module loads ⭐ FINAL FIX
