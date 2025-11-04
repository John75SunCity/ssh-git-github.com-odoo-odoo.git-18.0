# 🧹 Delete Studio Customizations - Step-by-Step Guide

## 📋 Problem Summary

Studio customizations are blocking module deployment with XPath errors:
```
ValueError: Element '<xpath expr="//field[@name='stock_location_id']">' cannot be located in parent view
```

**Root Cause**: Studio customizations use fragile XPath expressions that break when base views change.

**Solution**: Delete Studio customizations from Odoo.sh database and use the native XML replacements we just added.

---

## ✅ Customizations Already Recreated in Code

We've already added these features to the XML views (commit `cadff0b2`):

### Container Tree View (`records_container_view_list`)
- ✅ `stock_location_id` field now **optional="hide"** (user can toggle visibility)
- ✅ Column available but hidden by default
- ✅ Can be shown via column settings (click gear icon in tree view)

### Container Form View (`records_container_view_form`)
- ✅ `stock_location_id` field visible for `stock.group_stock_user` group
- ✅ Proper label: "Stock Location (Technical)"
- ✅ Help text explaining it's for advanced inventory users
- ✅ Smart buttons for Stock Quant and Stock Location already present

---

## 🗑️ Studio Customizations to Delete

### Method 1: Via Odoo Studio UI (Recommended)

1. **Access Odoo.sh** → Go to your production/staging database
2. **Enter Studio Mode** → Click Studio icon (top right)
3. **Open Customizations Panel**:
   - Studio → Views → Customizations
   - Or: Settings → Technical → Views → Search for "studio_customization"

4. **Delete these 4 customizations**:

   | External ID | View Name | What It Was Doing |
   |------------|-----------|-------------------|
   | `studio_customization.odoo_studio_records__655d7abd-4d5c-4ddf-aeca-24f09efced36` | `records.container.view.form` | Making `stock_location_id` visible (NOW IN CODE) |
   | `studio_customization.odoo_studio_records__a04961c4-3633-4c30-ba68-b59aa48a282d` | `records.container.view.tree.technical` | Possibly adding tree columns (OPTIONAL) |
   | `studio_customization.odoo_studio_records__4b9a07da-d063-4b1b-8e28-b912666983a0` | `records.department.view.form` | Unknown department customization (OPTIONAL) |
   | `studio_customization.odoo_studio_records__eaf68044-be01-498b-b3ad-16a36f29707d` | `records.location.view.tree.technical` | Unknown location customization (OPTIONAL) |

5. **Steps for each customization**:
   - Find the view in the list
   - Click the customization entry
   - Click "Delete" or "Remove"
   - Confirm deletion

### Method 2: Via Database SQL (Advanced)

**⚠️ BACKUP FIRST!** This method is faster but requires database access.

```sql
-- View what will be deleted
SELECT id, name, key, model, inherit_id 
FROM ir_ui_view 
WHERE key LIKE 'studio_customization.odoo_studio_records_%';

-- Delete Studio customizations for records_management module
DELETE FROM ir_ui_view 
WHERE key IN (
    'studio_customization.odoo_studio_records__655d7abd-4d5c-4ddf-aeca-24f09efced36',
    'studio_customization.odoo_studio_records__a04961c4-3633-4c30-ba68-b59aa48a282d',
    'studio_customization.odoo_studio_records__4b9a07da-d063-4b1b-8e28-b912666983a0',
    'studio_customization.odoo_studio_records__eaf68044-be01-498b-b3ad-16a36f29707d'
);
```

### Method 3: Via Odoo Shell (Alternative)

```bash
# SSH into Odoo.sh or use local Odoo shell
odoo-bin shell -d your_database

# In Python shell:
env = Environment(cr, SUPERUSER_ID, {})
customizations = env['ir.ui.view'].search([
    ('key', 'like', 'studio_customization.odoo_studio_records_%')
])
print(f"Found {len(customizations)} Studio customizations")
for custom in customizations:
    print(f"Deleting: {custom.key} - {custom.name}")
customizations.unlink()
env.cr.commit()
```

---

## 🧪 Verification Steps

After deleting Studio customizations:

### 1. **Upgrade the Module**
```bash
# Via Odoo.sh interface:
Apps → Records Management → Upgrade

# Or via command line:
odoo-bin -u records_management -d your_database --stop-after-init
```

### 2. **Check for Errors**
- ✅ Module should load without XPath errors
- ✅ No "Element cannot be located" messages
- ✅ Views should render properly

### 3. **Test Container Views**

**Tree View Test**:
1. Go to: Records Management → Containers
2. Click gear icon (⚙️) in tree view
3. Verify `stock_location_id` is in available columns (optional)
4. Toggle it on/off to verify it works

**Form View Test**:
1. Open any container record
2. As stock user: Should see "Stock Location (Technical)" field
3. As normal user: Should see "Warehouse Location" field
4. Smart buttons for Stock Quant and Stock Location should work

### 4. **Test Portal Service Ordering**
1. Go to: `/my/requests` (as portal user)
2. Click "Request Pickup" → Form should load
3. Click "Request Destruction" → Form should load with container list
4. Create test request → Should auto-submit successfully

---

## 📊 What Was Lost vs What Was Recreated

| Studio Feature | Status | Notes |
|---------------|---------|-------|
| `stock_location_id` visible in tree | ✅ **RECREATED** | Now `optional="hide"` - user toggleable |
| `stock_location_id` visible in form | ✅ **RECREATED** | Visible for `stock.group_stock_user` |
| Stock Quant smart button | ✅ **ALREADY EXISTS** | Native feature, not Studio |
| Stock Location smart button | ✅ **ALREADY EXISTS** | Native feature, not Studio |
| Container tree columns | ⚠️ **MAY BE LOST** | If you had custom columns, re-add via UI settings |
| Department form customizations | ❓ **UNKNOWN** | Check after deletion what broke |
| Location tree customizations | ❓ **UNKNOWN** | Check after deletion what broke |

---

## 🚨 Troubleshooting

### Issue: "Still getting XPath errors after deletion"

**Solution**: Clear Odoo cache and restart server
```bash
# Via Odoo.sh interface:
Database → Restart

# Or manually:
systemctl restart odoo
# Then clear browser cache (Ctrl+Shift+R)
```

### Issue: "Can't find Studio customizations in UI"

**Solution**: They may only exist in database. Use SQL method:
```sql
SELECT key, name FROM ir_ui_view WHERE key LIKE '%studio%' AND key LIKE '%records%';
```

### Issue: "Deleted customizations but something looks different"

**Solution**: Take screenshots before deletion, then report what's missing. We can add it to the XML views.

---

## 📞 Support

If you encounter issues:

1. **Check deployment logs** on Odoo.sh for specific error messages
2. **Screenshot any missing UI elements** after deletion
3. **Report back** what was lost - we can recreate it in code

---

## ✅ Expected Outcome

After following this guide:

- ✅ Module loads successfully on Odoo.sh
- ✅ No XPath errors in deployment logs
- ✅ Container views work normally
- ✅ Portal service ordering features are accessible
- ✅ `stock_location_id` field can be toggled on/off by users
- ✅ Stock users see technical field, normal users see user-friendly field

---

**Created**: 2025-01-08  
**Related Commits**: `cadff0b2` (Studio replacement), `512f856f` (Model import fix)  
**Deployment Status**: Ready for production after Studio deletion
