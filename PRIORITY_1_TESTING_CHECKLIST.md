# Priority 1 Testing Checklist
**Date**: November 2, 2025  
**Module**: records_management v18.0.0.0.1  
**Test Environment**: Odoo.sh Development

---

## 🎯 Test Objectives

Verify Priority 1 implementation:
1. Container name is editable (no auto-generation)
2. Barcode manual assignment workflow works
3. Stock integration creates proper quants
4. UI shows stock fields correctly
5. Smart buttons navigate properly
6. Index Container button validates and creates quant

---

## ✅ Pre-Test Setup

### Step 1: Deploy Changes
```bash
cd /Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0

# Stage files
git add records_management/models/records_container.py
git add records_management/views/records_container_views.xml

# Commit
git commit -m "feat(UI): Stock integration in container form + Index Container button

- Added Index Container button (validates barcode, creates stock quant)
- Added 2 smart buttons (Stock Quant, Stock Location)
- Added 4 stock fields (stock_location_id, quant_id, owner_id, current_stock_location_id)
- Updated name field (editable with helpful placeholder)
- Updated barcode field (removed auto-gen placeholder)
- Marked location_id DEPRECATED with warning
- Added action_view_stock_quant() and action_view_stock_location() methods

Completes Priority 1 UI integration."

# Push to repository
git push origin main
```

### Step 2: Upgrade Module on Odoo.sh
1. Log in to Odoo.sh development environment
2. Navigate to: **Apps**
3. Search: "records_management"
4. Click: **Upgrade**
5. Wait for upgrade to complete

---

## 📋 Test Cases

### TEST 1: Container Name Editable ✅
**Objective**: Verify customer can name containers

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 1.1 | Open Records Management → Containers | List view shows | [ ] |
| 1.2 | Click **Create** | New form opens in draft state | [ ] |
| 1.3 | Fill name: "HR Personnel Files 2024" | Name field accepts input | [ ] |
| 1.4 | Save container | Name saved as entered (no auto-gen) | [ ] |
| 1.5 | Edit name to "Updated Name 2024" | Change allowed | [ ] |
| 1.6 | Save again | New name saved | [ ] |

**Expected**: ✅ Name field fully editable, no auto-generation  
**Actual**: ___________

---

### TEST 2: Barcode Manual Assignment ✅
**Objective**: Verify barcode not auto-generated

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 2.1 | Create new container | barcode field empty | [ ] |
| 2.2 | Check placeholder text | Shows "Assign from pre-printed barcode sheet" | [ ] |
| 2.3 | Save without barcode | Saves successfully | [ ] |
| 2.4 | Manually enter barcode: "BC-2024-001234" | Accepts input | [ ] |
| 2.5 | Save | Barcode saved as entered | [ ] |
| 2.6 | Check barcode_assigned compute field | Should be True (invisible) | [ ] |

**Expected**: ✅ No auto-generation, manual assignment required  
**Actual**: ___________

---

### TEST 3: Index Container Button ✅
**Objective**: Verify Index Container workflow

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 3.1 | Create container WITHOUT barcode | "Index Container" button HIDDEN | [ ] |
| 3.2 | Assign barcode: "BC-2024-001234" | "Index Container" button VISIBLE | [ ] |
| 3.3 | Click "Index Container" | Processing starts | [ ] |
| 3.4 | Check state | Changed to "Active" | [ ] |
| 3.5 | Check quant_id field | Populated with stock.quant ID | [ ] |
| 3.6 | Check stock_location_id | Assigned default location | [ ] |
| 3.7 | Check owner_id | Shows customer (partner_id) | [ ] |
| 3.8 | Check button after indexing | "Index Container" button HIDDEN | [ ] |

**Expected**: ✅ Button creates quant, assigns location, sets owner, changes state  
**Actual**: ___________

**Error Cases to Test**:
| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 3.9 | Try clicking without barcode | Error: "Barcode required before indexing" | [ ] |
| 3.10 | Try indexing already-indexed container | Button hidden (can't re-index) | [ ] |

---

### TEST 4: Smart Buttons - Stock Quant ✅
**Objective**: Verify Stock Quant smart button

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 4.1 | Open container WITHOUT quant | Smart button HIDDEN | [ ] |
| 4.2 | Index container (creates quant) | Smart button VISIBLE | [ ] |
| 4.3 | Check smart button label | Shows "Stock" / "Quant" | [ ] |
| 4.4 | Click smart button | Opens stock.quant form view | [ ] |
| 4.5 | Verify quant details | Quantity = 1 | [ ] |
| 4.6 | Check quant owner | Same as container partner_id | [ ] |
| 4.7 | Check quant location | Same as container stock_location_id | [ ] |

**Expected**: ✅ Smart button navigates to correct quant record  
**Actual**: ___________

---

### TEST 5: Smart Buttons - Stock Location ✅
**Objective**: Verify Stock Location smart button

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 5.1 | Open container WITHOUT stock_location_id | Smart button HIDDEN | [ ] |
| 5.2 | Assign stock location | Smart button VISIBLE | [ ] |
| 5.3 | Check smart button label | Shows "Stock" / "Location" | [ ] |
| 5.4 | Click smart button | Opens stock.location form view | [ ] |
| 5.5 | Verify location details | Shows complete location name | [ ] |
| 5.6 | Check window title | Shows "Stock Location: [complete_name]" | [ ] |

**Expected**: ✅ Smart button navigates to correct location record  
**Actual**: ___________

---

### TEST 6: Stock Integration Fields ✅
**Objective**: Verify all 4 stock fields display correctly

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 6.1 | Open indexed container | All stock fields visible (internal user) | [ ] |
| 6.2 | Check stock_location_id | Editable, shows assigned location | [ ] |
| 6.3 | Check current_stock_location_id | Readonly, shows same location as quant | [ ] |
| 6.4 | Check quant_id | Readonly, shows quant ID | [ ] |
| 6.5 | Check owner_id | Readonly, shows customer name | [ ] |
| 6.6 | Check field help text | All fields have helpful descriptions | [ ] |

**Expected**: ✅ All stock fields visible with correct values  
**Actual**: ___________

---

### TEST 7: Deprecated Location Field ✅
**Objective**: Verify location_id deprecation warning

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 7.1 | Open container form | location_id field visible | [ ] |
| 7.2 | Hover over help icon | Shows "⚠️ DEPRECATED - Use stock_location_id instead" | [ ] |
| 7.3 | Try selecting location_id | Still functional (backward compatible) | [ ] |
| 7.4 | Compare with stock_location_id | stock_location_id is primary field | [ ] |

**Expected**: ✅ Deprecation warning shown, field still works  
**Actual**: ___________

---

### TEST 8: Real-Time Location Updates ✅
**Objective**: Verify current_stock_location_id auto-updates

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 8.1 | Index container at Location A | current_stock_location_id = Location A | [ ] |
| 8.2 | Navigate to Inventory → Stock Moves | Find container's quant | [ ] |
| 8.3 | Create internal transfer (Location A → Location B) | Transfer created | [ ] |
| 8.4 | Validate transfer | Transfer completed | [ ] |
| 8.5 | Return to container form | current_stock_location_id = Location B | [ ] |
| 8.6 | Check stock_location_id | Still shows Location A (original assignment) | [ ] |

**Expected**: ✅ current_stock_location_id follows quant movements  
**Actual**: ___________

---

### TEST 9: Portal User View ✅
**Objective**: Verify portal users don't see stock fields

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 9.1 | Log in as portal user | Access portal | [ ] |
| 9.2 | Navigate to My Containers | List view shows | [ ] |
| 9.3 | Open container | Form view opens | [ ] |
| 9.4 | Check visibility | Stock fields HIDDEN | [ ] |
| 9.5 | Check name field | Editable for portal user | [ ] |
| 9.6 | Check barcode field | HIDDEN from portal user | [ ] |
| 9.7 | Check smart buttons | Stock buttons HIDDEN | [ ] |

**Expected**: ✅ Portal users see simplified view, can edit name  
**Actual**: ___________

---

### TEST 10: Workflow Integration ✅
**Objective**: Verify full container lifecycle with stock

| Step | Action | Expected Result | Status |
|------|--------|----------------|--------|
| 10.1 | Create container as customer (portal) | Name: "Tax Records 2023" | [ ] |
| 10.2 | Staff assigns barcode | Barcode: "BC-2024-001234" | [ ] |
| 10.3 | Staff clicks "Index Container" | Creates quant, state → Active | [ ] |
| 10.4 | Staff clicks "Store" button | State → Stored | [ ] |
| 10.5 | Check current_stock_location_id | Shows storage location | [ ] |
| 10.6 | Staff clicks "Retrieve" button | State → Retrieved | [ ] |
| 10.7 | Check current_stock_location_id | Shows retrieval location | [ ] |
| 10.8 | Complete destruction workflow | Stock quant updated | [ ] |

**Expected**: ✅ Stock system tracks all container movements  
**Actual**: ___________

---

## 🐛 Bug Tracking

### Issue Log
| # | Date | Description | Severity | Status |
|---|------|-------------|----------|--------|
| 1 | | | | |
| 2 | | | | |

---

## 📊 Test Results Summary

### Overall Status: [ ] PASS / [ ] FAIL

| Test Case | Status | Notes |
|-----------|--------|-------|
| TEST 1: Container Name Editable | [ ] | |
| TEST 2: Barcode Manual Assignment | [ ] | |
| TEST 3: Index Container Button | [ ] | |
| TEST 4: Smart Button - Stock Quant | [ ] | |
| TEST 5: Smart Button - Stock Location | [ ] | |
| TEST 6: Stock Integration Fields | [ ] | |
| TEST 7: Deprecated Location Field | [ ] | |
| TEST 8: Real-Time Location Updates | [ ] | |
| TEST 9: Portal User View | [ ] | |
| TEST 10: Workflow Integration | [ ] | |

---

## 🚀 Post-Test Actions

### If Tests Pass ✅:
1. [ ] Update production planning document
2. [ ] Schedule Priority 2 implementation (migration)
3. [ ] Create user training materials
4. [ ] Update module documentation
5. [ ] Plan list/kanban view updates

### If Tests Fail ❌:
1. [ ] Document all failures in Bug Log
2. [ ] Prioritize critical issues
3. [ ] Create fix plan
4. [ ] Retest after fixes
5. [ ] Hold production deployment

---

## 📝 Testing Notes

### Environment Details:
- **Odoo Version**: ___________
- **Database**: ___________
- **Branch**: ___________
- **Commit**: ___________

### Tester Information:
- **Name**: ___________
- **Date**: ___________
- **Duration**: ___________ minutes

### Additional Observations:
___________________________________________
___________________________________________
___________________________________________

---

## 🎓 Testing Tips

### Best Practices:
1. Test as both internal user AND portal user
2. Use real-world data (customer names, barcode patterns)
3. Test error cases (missing barcode, already indexed, etc.)
4. Verify stock movements create audit trail
5. Check field visibility for different user groups

### Common Issues to Watch For:
- Smart buttons not appearing when they should
- Fields visible to portal users when they shouldn't be
- Barcode validation not working
- Stock quant not created on indexing
- Location not auto-assigned
- Error messages not helpful

### Quick Validation Commands:
```python
# In Odoo shell (for debugging):

# 1. Check if quant was created
container = env['records.container'].browse(CONTAINER_ID)
print(f"Quant ID: {container.quant_id.id if container.quant_id else 'None'}")

# 2. Check stock location
print(f"Stock Location: {container.stock_location_id.complete_name}")

# 3. Check real-time location
print(f"Current Location: {container.current_stock_location_id.complete_name}")

# 4. Check owner
print(f"Owner: {container.owner_id.name}")
```

---

*Testing Checklist Generated: November 2, 2025*  
*Module: records_management v18.0.0.0.1*
