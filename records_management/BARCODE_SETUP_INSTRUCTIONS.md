# Barcode Operations Setup Instructions

## ⚠️ IMPORTANT: Manual Setup Required

The barcode nomenclature rules are currently **commented out** in `__manifest__.py` because they require the `barcodes` module to be properly installed.

## 📋 Setup Steps:

### 1. Verify Barcodes Module is Installed

Go to **Apps** → Search for "Barcode" → Install if not already installed

### 2. Enable Barcode Nomenclature Rules

Once the `barcodes` module is confirmed working:

**Edit `__manifest__.py`:**
```python
# Find this section (around line 93):
# "data/barcode_nomenclature_rules.xml",

# Uncomment it to:
"data/barcode_nomenclature_rules.xml",
```

### 3. Upgrade the Module

```bash
# Upgrade records_management module
./odoo-bin -u records_management -d your_database
```

### 4. Verify Barcode Rules Loaded

Go to **Inventory** → **Configuration** → **Barcode Nomenclatures** → **Default Nomenclature**

You should see 14 new rules:
- Convert Temp Container to Storage (WH/STOCK/NEW-IN)
- Mark Container for Pickup (WH/STOCK/PICKUP)
- Move to Shredding Queue (WH/SHRED/QUEUE)
- Complete Shredding Process (WH/SHRED/COMPLETE)
- Archive Container (WH/ARCHIVE/STORE)
- Return Container to Customer (WH/CUSTOMER/RETURN)
- Add to Inventory (INV/ADD/STOCK)
- Remove from Inventory (INV/REMOVE/STOCK)
- Transfer to Main Warehouse (WH/MAIN/TRANSFER)
- Transfer to Offsite Storage (WH/OFFSITE/TRANSFER)
- QC Inspection Required (QC/INSPECT/QUEUE)
- QC Approved (QC/APPROVED/MOVE)
- Retrieval Request Processing (REQ/RETRIEVE/PROCESS)
- Service Request Processing (REQ/SERVICE/PROCESS)

## 🎯 What Works WITHOUT Barcode Rules:

Even without the nomenclature rules, you still get:

✅ **Barcode operation buttons** - They appear on container forms
✅ **Manual barcode scanning** - Can scan containers with barcode hardware
✅ **Container tracking fields** - last_barcode_operation, etc.
✅ **Batch operations wizard** - Process multiple containers

The buttons will create internal transfers, but without the nomenclature rules,
the barcode patterns won't auto-trigger the workflows. You'll need to manually
validate transfers.

## 🔧 Alternative: Manual Barcode Rule Creation

If the XML file doesn't work, you can manually create rules:

1. Go to **Inventory** → **Configuration** → **Barcode Nomenclatures**
2. Open **Default Nomenclature**
3. Click **Add a line** in the Rules tab
4. For each operation, create a rule with:
   - **Name**: Convert Temp Container to Storage
   - **Type**: Location
   - **Barcode Pattern**: WH/STOCK/NEW-IN
   - **Alias**: Convert to Storage Container
   - **Notes**: ⚠️ WARNING: This barcode rule is linked to the "Store Container" button...

Repeat for all 14 patterns listed above.

## 📚 Reference

See `BARCODE_OPERATIONS_SYSTEM.md` for complete documentation on how the system works.

## 🐛 Troubleshooting

**Error: KeyError: 'barcode.nomenclature.rule'**
- Solution: The barcodes module is not installed. Install it first, then uncomment the data file.

**Error: Model 'records.container' does not exist**
- Solution: Import order issue. Ensure barcode_container_operations is imported AFTER records_container in models/__init__.py

**Buttons appear but don't work**
- Check if barcode nomenclature rules are loaded
- Verify the barcode patterns match exactly
- Check Odoo logs for transfer creation errors
