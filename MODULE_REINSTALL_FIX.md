# Module Reinstall Recovery Guide

## 🚨 ISSUE: View Not Found After Module Reinstall

**Error**: `ValueError: View 'records_management.portal_file_search_create' in website 1 not found`

**Root Cause**: When you uninstalled and reinstalled the module without activating RM configurator toggles, some views were not properly loaded into the database.

---

## ✅ IMMEDIATE FIX (Choose One)

### Option 1: Upgrade Module (RECOMMENDED)

**In Odoo.sh Interface**:
1. Go to **Apps** menu
2. Search for "Records Management"
3. Click **Upgrade** button
4. Wait for upgrade to complete
5. Refresh browser
6. Test the problematic route again

**Via Command Line** (if you have shell access):
```bash
odoo-bin -u records_management -d your_database --stop-after-init
```

### Option 2: Force View Reload via SQL (ADVANCED)

**Only if upgrade fails** - this forces a view reload:

```sql
-- Connect to your Odoo database
DELETE FROM ir_ui_view WHERE name = 'Create File Search Request' AND model IS NULL;
```

Then restart Odoo server to trigger view recreation.

### Option 3: Force Module Update via UI

1. Go to **Settings** → **Technical** → **Database Structure** → **Views**
2. Search for: `portal_file_search_create`
3. If not found, go to **Apps** → **Update Apps List**
4. Then upgrade **Records Management** module

---

## 🔧 PREVENT FUTURE ISSUES

### After Any Module Reinstall:

1. **IMMEDIATELY Enable RM Configurator Toggles**
   - Go to Settings → Records Management → Configuration
   - Enable ALL feature toggles that were previously active
   - **Save** configuration

2. **Verify All Views Loaded**
   ```sql
   -- Check view count for records_management
   SELECT COUNT(*) FROM ir_ui_view WHERE name LIKE '%portal%' AND model IS NULL;
   ```
   Should return 30+ views

3. **Test Critical Routes**
   - `/my/home` - Portal home
   - `/my/containers` - Inventory
   - `/my/requests` - Request list
   - `/my/request/new/file_search` - File search (the failing route)
   - `/my/organization` - Organization chart

---

## 🎯 WHAT HAPPENED (Technical Explanation)

### Normal Module Installation Flow:
```
1. Install module → Load XML templates → Create ir.ui.view records
2. Enable RM configurator toggles → Show/hide features
3. Views remain in database (even if features disabled)
```

### What Went Wrong:
```
1. Uninstall module → Delete all ir.ui.view records ✓
2. Reinstall module → Load XML templates → Create ir.ui.view records ✓
3. ❌ MISSED: Enable RM configurator toggles
4. Access route → Controller tries to render view → View exists in XML but not in website context
```

### Why Configurator Matters:
- RM Module Configurator doesn't control **view creation** (that's automatic)
- It controls **feature visibility** and **business logic toggles**
- BUT: After reinstall, some views may not be indexed for website context
- Solution: **Upgrade module** forces full re-indexing

---

## 📋 POST-FIX CHECKLIST

After applying the fix:

- [ ] Module upgraded successfully
- [ ] All RM configurator toggles re-enabled
- [ ] Portal home page loads (`/my/home`)
- [ ] Can create new request (`/my/request/new/file_search`)
- [ ] Organization chart displays data (`/my/organization`)
- [ ] No more "View not found" errors
- [ ] Check Odoo logs for any other missing views

---

## 🔍 DEBUGGING COMMANDS

### Check if view exists in database:
```sql
SELECT id, name, key, active, website_id 
FROM ir_ui_view 
WHERE key = 'records_management.portal_file_search_create';
```

**Expected**:
- Should return 1 row
- `active` should be `true`
- `website_id` should be `NULL` or `1`

### Check all portal views:
```sql
SELECT key, name, active 
FROM ir_ui_view 
WHERE key LIKE 'records_management.portal_%' 
ORDER BY key;
```

**Expected**: 30+ views with `active = true`

### Force view update via Python:
```python
# In Odoo shell
env['ir.ui.view'].search([('key', '=', 'records_management.portal_file_search_create')]).write({'active': True})
env.cr.commit()
```

---

## 🚀 RELATED TO ORGANIZATION CHART FIX

**Good News**: The organization chart fix (commit 7b0a1852e) is independent of this issue.

**Why This Doesn't Affect Org Chart**:
- Organization chart view (`portal_organization_diagram`) exists in database
- Double-encoding fix only changed controller logic (not view registration)
- Organization chart should work once views are reloaded

**After Module Upgrade**:
1. Organization chart data rendering should work (double-encoding fixed)
2. File search view should load (view registration fixed)
3. All portal routes should work

---

## 💡 KEY TAKEAWAY

**When reinstalling Odoo modules**:
1. ✅ **DO**: Immediately upgrade module after reinstall
2. ✅ **DO**: Re-enable ALL configurator toggles before testing
3. ✅ **DO**: Test critical routes before deploying
4. ❌ **DON'T**: Assume reinstall = working (views may not index)
5. ❌ **DON'T**: Skip the upgrade step

---

## 📞 NEXT STEPS

1. **Apply the fix** (upgrade module)
2. **Re-enable RM configurator toggles**
3. **Test organization chart** (`/my/organization`)
   - Verify department/user hierarchy displays
   - Confirm double-encoding fix worked
4. **Test file search** (`/my/request/new/file_search`)
   - Should load without errors
5. **Report back** - let me know if both issues are resolved

---

**Status**: Awaiting module upgrade + testing
**Expected Outcome**: Both organization chart AND file search views working correctly
