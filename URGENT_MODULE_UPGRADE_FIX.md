# 🚨 URGENT: Records Management Module Upgrade Fix

## Problem Summary
The `records_management` module upgrade is failing with:
```
psycopg2.errors.UndefinedColumn: column res_partner.transitory_field_config_id does not exist
```

## Why This Happened
We added 4 new fields to the `res.partner` model in the Python code, but the database columns don't exist yet. When Odoo tries to upgrade the module, it loads the Python model definitions BEFORE running migrations, causing this chicken-and-egg problem.

## ✅ IMMEDIATE SOLUTION (Choose ONE)

### Option A: SQL Console (FASTEST - 2 minutes)
1. Go to your Odoo.sh project dashboard
2. Click "Database" → "SQL Console" or "psql"
3. Copy and paste this entire block:

```sql
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS transitory_field_config_id INTEGER;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS field_label_config_id INTEGER;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS allow_transitory_items BOOLEAN DEFAULT TRUE;
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS max_transitory_items INTEGER DEFAULT 100;
UPDATE res_partner SET allow_transitory_items = TRUE WHERE allow_transitory_items IS NULL;
UPDATE res_partner SET max_transitory_items = 100 WHERE max_transitory_items IS NULL;
```

4. Verify success (should show 4 rows):
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'res_partner' 
AND column_name IN ('transitory_field_config_id', 'field_label_config_id', 'allow_transitory_items', 'max_transitory_items');
```

5. Now click "Upgrade" on the `records_management` module - it should work!

### Option B: Pre-Made SQL File (if you have file upload access)
1. Upload `records_management/migrations/SIMPLE_SQL_PATCH.sql` to your Odoo.sh
2. Run: `psql < SIMPLE_SQL_PATCH.sql`
3. Upgrade the module

### Option C: Odoo Shell Script (if you have shell access)
1. SSH into your Odoo.sh instance
2. Run: `odoo-bin shell -d <your_database>`
3. Paste the contents of `records_management/migrations/add_partner_columns.py`
4. Upgrade the module

## Files Created to Help You

1. **SIMPLE_SQL_PATCH.sql** - Simple SQL commands (copy-paste friendly)
2. **EMERGENCY_SQL_PATCH.sql** - Advanced version with PL/pgSQL
3. **add_partner_columns.py** - Python shell script
4. **MIGRATION_TROUBLESHOOTING.md** - Detailed explanation

All files are in `records_management/migrations/`

## What These Columns Do

- `transitory_field_config_id` - Link to field visibility configuration
- `field_label_config_id` - Link to custom field labels  
- `allow_transitory_items` - Boolean flag (default: TRUE)
- `max_transitory_items` - Limit for items (default: 100)

## After Fixing

Once you run the SQL patch and upgrade successfully:
1. The module will work normally
2. Future upgrades will use proper migration scripts (already created)
3. This is a ONE-TIME fix needed

## Need Help?

Check the detailed guide: `records_management/migrations/MIGRATION_TROUBLESHOOTING.md`

---
**Status:** All code deployed and ready. You just need to run the SQL patch before upgrading.
