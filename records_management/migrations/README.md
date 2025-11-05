# Records Management - Migration Guide

## 📋 Overview

This directory contains **automated migration scripts** that handle database schema changes across different versions of the Records Management module. These scripts ensure smooth upgrades without manual SQL intervention.

## 🎯 Why Migrations Matter

### ❌ **The Old Way (Manual SQL)**
```sql
-- You had to run these manually on each new branch/environment:
ALTER TABLE records_storage_department_user ADD COLUMN role VARCHAR;
ALTER TABLE records_storage_department_user ADD COLUMN state VARCHAR;
ALTER TABLE records_storage_department_user ADD COLUMN can_view_records BOOLEAN;
-- ... etc.
```

**Problems:**
- 🔴 Manual work required for each deployment
- 🔴 Easy to forget fields
- 🔴 Different environments get out of sync
- 🔴 No version control of schema changes
- 🔴 Risk of typos/errors

### ✅ **The New Way (Automated Migrations)**
```python
# Migration script runs automatically during module upgrade
def migrate(cr, version):
    _add_column_if_missing(cr, "records_storage_department_user", "role", "VARCHAR")
    # ... all fields added automatically with proper defaults
```

**Benefits:**
- ✅ **Zero manual intervention** - runs automatically
- ✅ **Version controlled** - tracked in Git
- ✅ **Consistent** - same schema across all environments
- ✅ **Safe** - checks for existing columns (idempotent)
- ✅ **Auditable** - full logging of all changes

---

## 🏗️ How Odoo Migrations Work

### **Migration Lifecycle**

```
┌─────────────────────────────────────────────────────────┐
│  1. User clicks "Upgrade" button in Odoo Apps menu     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  2. Odoo checks module version: 18.0.1.0.0 → 18.0.1.0.1 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  3. Looks for migration directory: migrations/18.0.1.0.1│
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  4. Runs pre-migration.py (BEFORE loading models)       │
│     - Adds missing database columns                     │
│     - Sets default values for existing rows             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  5. Odoo loads Python models (ORM validates fields)     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  6. Odoo loads XML views (validates field references)   │
│     ✅ Fields exist! No ParseError!                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  7. Runs post-migration.py (AFTER module loaded)        │
│     - Data transformations                              │
│     - Cleanup old data                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  8. Module upgrade complete! 🎉                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure

```
records_management/
├── migrations/
│   ├── README.md (this file)
│   ├── 18.0.1.0.1/
│   │   ├── pre-migration.py    ← Runs BEFORE module loads
│   │   └── post-migration.py   ← Runs AFTER module loads (optional)
│   ├── 18.0.1.0.2/             ← Future version migrations
│   │   └── pre-migration.py
│   └── ...
```

### **Naming Convention**
- Directory name = **target version** (e.g., `18.0.1.0.1`)
- `pre-migration.py` = SQL/schema changes **before** ORM loads
- `post-migration.py` = Data transformations **after** ORM loads

---

## 🔧 Current Migrations

### **Version 18.0.1.0.1**

**File:** `migrations/18.0.1.0.1/pre-migration.py`

**Purpose:** Add missing fields to prevent "Field does not exist" errors

**Changes Applied:**

#### 1. **res_partner Transitory Fields**
```python
- transitory_field_config_id (Many2one)
- field_label_config_id (Many2one)
- allow_transitory_items (Boolean, default=True)
- max_transitory_items (Integer, default=100)
```

#### 2. **records.storage.department.user Assignment Fields**
```python
- role (Selection: viewer/editor/manager, default='viewer')
- state (Selection: active/inactive, default='active')
- can_view_records (Boolean, default=False)
- can_create_records (Boolean, default=False)
- can_edit_records (Boolean, default=False)
- can_delete_records (Boolean, default=False)
- can_export_records (Boolean, default=False)
- start_date (Date)
- end_date (Date)
- priority (Selection, default='normal')
- access_level (Selection, default='internal')
- description (Char)
- notes (Text)
```

**Safety Features:**
- ✅ Checks if columns exist before adding (prevents errors)
- ✅ Sets sensible defaults for existing records
- ✅ Handles missing tables gracefully
- ✅ Full logging for troubleshooting

---

## 🚀 Usage Guide

### **For Developers: Adding New Migrations**

When you add new fields to a model that need to exist before views load:

#### **Step 1: Create Migration Directory**
```bash
mkdir -p records_management/migrations/18.0.X.X.X
```

#### **Step 2: Create pre-migration.py**
```python
# records_management/migrations/18.0.X.X.X/pre-migration.py

import logging

_logger = logging.getLogger(__name__)

def _add_column_if_missing(cr, table_name, column_name, column_type, default_value=None):
    """Helper function to safely add columns"""
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name=%s AND column_name=%s
    """, (table_name, column_name))
    
    if not cr.fetchone():
        _logger.info(f"Adding {table_name}.{column_name} ({column_type})")
        cr.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
        
        if default_value is not None:
            cr.execute(f'UPDATE {table_name} SET {column_name} = %s WHERE {column_name} IS NULL', (default_value,))
    else:
        _logger.info(f"Column {table_name}.{column_name} already exists - skipping")

def migrate(cr, version):
    """Add new fields before ORM loads"""
    _logger.info("Running pre-migration for version X.X.X")
    
    # Add your fields here
    _add_column_if_missing(cr, "your_table", "your_field", "VARCHAR", default_value='default')
    
    _logger.info("Pre-migration complete!")
```

#### **Step 3: Bump Module Version**
Update `__manifest__.py`:
```python
'version': '18.0.X.X.X',  # Match migration directory name
```

#### **Step 4: Test on Development**
1. Install module on clean database
2. Add some test data
3. Upgrade module → migration should run automatically
4. Verify fields exist and defaults are correct

#### **Step 5: Deploy**
```bash
git add records_management/migrations/18.0.X.X.X/
git commit -m "feat(migrations): Add pre-migration for version X.X.X"
git push
```

On Odoo.sh:
1. Module will automatically upgrade to new version
2. Migration runs automatically (no manual intervention!)
3. Check logs to verify migration success

---

## 🔍 Troubleshooting

### **Migration Not Running?**

**Check 1: Version Number**
```bash
# Migration directory MUST match module version in __manifest__.py
grep version records_management/__manifest__.py
ls records_management/migrations/
```

**Check 2: File Name**
```bash
# Must be exactly "pre-migration.py" (hyphen, not underscore!)
ls records_management/migrations/18.0.1.0.1/
```

**Check 3: Python Syntax**
```bash
python3 -m py_compile records_management/migrations/18.0.1.0.1/pre-migration.py
```

### **Field Still Missing After Migration?**

**Check Logs:**
```bash
# Odoo.sh: Check deployment logs
# Look for lines like:
# INFO records_management.migrations: Adding records_storage_department_user.role (VARCHAR)
```

**Manual Verification:**
```sql
-- SSH into Odoo.sh and check database
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'records_storage_department_user';
```

### **Migration Failed with Error?**

**Common Issues:**

1. **Syntax Error in SQL**
   - Check your ALTER TABLE statements
   - Use proper quoting for table/column names
   - Test SQL manually first

2. **Table Doesn't Exist Yet**
   - Add table existence check (see pre-migration.py example)
   - Table is created by ORM if model is new

3. **Permission Denied**
   - Migration runs as Odoo database user
   - Should have ALTER TABLE permissions
   - Check database user grants

---

## 📊 Best Practices

### ✅ **DO:**
1. **Always use migrations for schema changes**
   - Never commit models with fields missing from database
   - Add migration script in same commit as model changes

2. **Make migrations idempotent**
   - Use `IF NOT EXISTS` checks
   - Safe to run multiple times
   - Won't fail if already applied

3. **Set sensible defaults**
   - Required fields need defaults for existing rows
   - Consider backward compatibility

4. **Test migrations thoroughly**
   - Test on fresh database (install)
   - Test on existing database (upgrade)
   - Test with real data

5. **Log everything**
   - Use `_logger.info()` for normal operations
   - Use `_logger.warning()` for skipped steps
   - Helps debugging production issues

### ❌ **DON'T:**
1. **Don't rely on manual SQL**
   - Won't scale across environments
   - Easy to forget
   - No version control

2. **Don't skip version bumps**
   - Migration won't run if version doesn't change
   - Always bump minor version for schema changes

3. **Don't use post-migration for schema changes**
   - Use pre-migration for ALTER TABLE
   - Post-migration is for data only

4. **Don't forget to test downgrades**
   - Consider how to revert if needed
   - May need separate migration script

---

## 🎓 Learning Resources

### **Odoo Official Documentation**
- [Module Migrations](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html#module-migrations)
- [Database Management](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html)

### **Community Examples**
- Odoo Core: `addons/account/migrations/`
- Enterprise: `enterprise/helpdesk/migrations/`

### **Our Implementation**
- See `migrations/18.0.1.0.1/pre-migration.py` for working example
- Helper function `_add_column_if_missing()` is reusable

---

## 📞 Support

**Questions about migrations?**
- Check this README first
- Review existing migration scripts as examples
- Test on development environment before production

**Deployment Issues?**
- Check Odoo.sh logs for migration execution
- Verify version number matches directory name
- Ensure pre-migration.py is syntactically valid

---

## 📝 Changelog

### **18.0.1.0.1** (Current)
- Added res_partner transitory configuration fields
- Added records.storage.department.user assignment fields
- Prevents "Field does not exist" errors on new deployments
- Eliminates need for manual SQL commands

### **Future Versions**
- New migration directories will be created as needed
- Each version bump gets its own migration path
- Maintains full upgrade path from any version

---

**Last Updated:** November 5, 2025  
**Module:** Records Management - Enterprise Edition  
**Migration System:** Odoo 18.0 Standard Migration Framework
