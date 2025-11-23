# Portal Errors - Complete Fix Guide

**Date**: November 23, 2025  
**Context**: After module reinstall without immediate upgrade + configurator toggles not re-enabled

---

## 🎯 **THREE SEPARATE ISSUES IDENTIFIED**

### **Issue 1: Organization Chart Template Error** ✅ **FIXED**
**Error**: `AttributeError: 'dict' object has no attribute 'search_query'`  
**Status**: ✅ Fixed in commit d1b0cf534  
**Solution**: Changed template to use `dict.get()` instead of dot notation

### **Issue 2: Calendar JavaScript Error** ⏳ **NEEDS CONVERSION**
**Error**: `TypeError: odoo.define is not a function`  
**Status**: ⏳ Needs vanilla JavaScript conversion (like other portal files)  
**Solution**: Convert portal_calendar.js to vanilla JS (add to conversion queue)

### **Issue 3: File Search View Missing** ⏳ **NEEDS MODULE UPGRADE**
**Error**: `ValueError: View 'records_management.portal_file_search_create' in website 1 not found`  
**Status**: ⏳ Same reinstall issue - need module upgrade  
**Solution**: Upgrade module to force view re-indexing

---

## ✅ **ISSUE 1: ORGANIZATION CHART - FIXED**

### **What Was Wrong:**
```xml
<!-- ❌ WRONG - Dot notation on Python dict -->
<input t-att-value="diagram.search_query or ''"/>
```

QWeb templates treat Python dictionaries differently than Odoo recordsets:
- **Odoo Recordset** (ORM object): `record.field_name` ✅ Works
- **Python Dict**: `dict.key` ❌ Fails - use `dict.get('key')` instead

### **The Fix Applied:**
```xml
<!-- ✅ CORRECT - Use .get() for dict access -->
<input t-att-value="diagram.get('search_query', '')"/>
```

**All Fixed Locations** (commit d1b0cf534):
1. Line 56: `diagram.search_query` → `diagram.get('search_query', '')`
2. Line 69: `diagram.layout_type` → `diagram.get('layout_type')`
3. Line 72: `diagram.layout_type` → `diagram.get('layout_type')`
4. Line 75: `diagram.layout_type` → `diagram.get('layout_type')`
5. Line 84: `diagram.show_messaging` → `diagram.get('show_messaging')`
6. Line 254: All JSON data attributes → `diagram.get()` pattern

### **Why This Happened:**
When the controller (portal.py) sends data to the template:
```python
# Controller creates a PLAIN PYTHON DICT
diagram_data = {
    'id': company.id,
    'node_data': nodes,      # Plain Python list
    'edge_data': edges,      # Plain Python list
    'search_query': '',      # Plain string
    ...
}

return request.render("portal_organization_diagram", {'diagram': diagram_data})
```

The `diagram` variable in the template is a **Python dict**, not an Odoo recordset, so:
- ✅ `diagram.get('search_query')` works
- ✅ `diagram['search_query']` works  
- ❌ `diagram.search_query` fails (AttributeError)

### **Testing:**
1. Deploy commit d1b0cf534
2. Navigate to `/my/organization`
3. **Expected**: Organization chart loads without error
4. **Verify**: Can search, change layout, export diagram

---

## ⏳ **ISSUE 2: CALENDAR JAVASCRIPT - NEEDS CONVERSION**

### **Error Details:**
```javascript
TypeError: odoo.define is not a function
```

**Location**: Portal calendar template (inline JavaScript)  
**Root Cause**: Still using Odoo 17 module system (`odoo.define`, `publicWidget`)

### **Current Code** (Broken - Odoo 17 style):
```javascript
odoo.define('records_management.portal_calendar', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    
    publicWidget.registry.PortalCalendar = publicWidget.Widget.extend({
        selector: '#portal-calendar',
        start: function () {
            // FullCalendar initialization
            var calendar = new FullCalendar.Calendar(calendarEl, {
                events: function(info, successCallback, failureCallback) {
                    ajax.jsonRpc('/my/calendar/events', 'call', {...})
                        .then(successCallback)
                        .catch(failureCallback);
                }
            });
        }
    });
});
```

### **Required Fix** (Vanilla JS - Odoo 18 compatible):
```javascript
(function() {
    'use strict';
    
    class PortalCalendar {
        constructor(containerElement) {
            this.container = containerElement;
            this.calendar = null;
            this.init();
        }
        
        init() {
            if (!this.container) {
                console.error('[PortalCalendar] Container element not found');
                return;
            }
            
            this._initializeCalendar();
        }
        
        _initializeCalendar() {
            this.calendar = new FullCalendar.Calendar(this.container, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                },
                events: async (info, successCallback, failureCallback) => {
                    try {
                        const response = await fetch('/my/calendar/events', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                start: info.startStr,
                                end: info.endStr
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        
                        const events = await response.json();
                        
                        // Hide loading, show calendar
                        const loading = document.getElementById('calendar-loading');
                        if (loading) loading.style.display = 'none';
                        this.container.style.display = 'block';
                        
                        successCallback(events);
                    } catch (error) {
                        console.error('[PortalCalendar] Error fetching events', error);
                        
                        const loading = document.getElementById('calendar-loading');
                        if (loading) {
                            loading.innerHTML = `
                                <div class="alert alert-danger">
                                    Failed to load calendar events. Please try again later.
                                </div>
                            `;
                        }
                        
                        failureCallback(error);
                    }
                },
                eventClick: (info) => {
                    info.jsEvent.preventDefault();
                    this._showEventDetails(info.event);
                }
            });
            
            this.calendar.render();
        }
        
        _showEventDetails(event) {
            const props = event.extendedProps;
            
            // Build modal content
            let modalBody = '<dl class="row">';
            modalBody += `<dt class="col-sm-4">Title:</dt><dd class="col-sm-8">${event.title}</dd>`;
            modalBody += `<dt class="col-sm-4">Date:</dt><dd class="col-sm-8">${event.start.toLocaleDateString()}</dd>`;
            
            if (event.end) {
                modalBody += `<dt class="col-sm-4">End:</dt><dd class="col-sm-8">${event.end.toLocaleDateString()}</dd>`;
            }
            
            // Type-specific details
            if (props.type === 'shredding') {
                modalBody += `<dt class="col-sm-4">Frequency:</dt><dd class="col-sm-8">${props.frequency || 'N/A'}</dd>`;
                modalBody += `<dt class="col-sm-4">Location:</dt><dd class="col-sm-8">${props.location || 'N/A'}</dd>`;
            } else if (props.type === 'service') {
                modalBody += `<dt class="col-sm-4">Type:</dt><dd class="col-sm-8">${props.work_order_type || 'N/A'}</dd>`;
                modalBody += `<dt class="col-sm-4">Stage:</dt><dd class="col-sm-8">${props.stage || 'N/A'}</dd>`;
            } else if (props.type === 'request') {
                modalBody += `<dt class="col-sm-4">Request Type:</dt><dd class="col-sm-8">${props.request_type || 'N/A'}</dd>`;
                modalBody += `<dt class="col-sm-4">Status:</dt><dd class="col-sm-8">${props.state || 'N/A'}</dd>`;
            }
            
            modalBody += '</dl>';
            
            // Update modal
            document.getElementById('eventModalTitle').textContent = event.title;
            document.getElementById('eventModalBody').innerHTML = modalBody;
            
            // Show/hide details button
            const detailsBtn = document.getElementById('eventViewDetailsBtn');
            if (event.url) {
                detailsBtn.href = event.url;
                detailsBtn.style.display = 'block';
            } else {
                detailsBtn.style.display = 'none';
            }
            
            // Show modal (Bootstrap 5)
            const modal = new bootstrap.Modal(document.getElementById('eventDetailsModal'));
            modal.show();
        }
    }
    
    // Auto-initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPortalCalendar);
    } else {
        initPortalCalendar();
    }
    
    function initPortalCalendar() {
        const calendarEl = document.getElementById('portal-calendar');
        if (calendarEl) {
            new PortalCalendar(calendarEl);
        }
    }
})();
```

### **Action Required:**
1. **Find the calendar template** with inline JavaScript
2. **Extract to separate file**: `records_management/static/src/js/portal/portal_calendar.js`
3. **Convert** to vanilla JavaScript (pattern above)
4. **Add to manifest**: Include in `web.assets_frontend` bundle
5. **Test**: Navigate to `/my/calendar` and verify events load

**Priority**: Medium (calendar is optional feature, not core)

---

## ⏳ **ISSUE 3: FILE SEARCH VIEW MISSING - MODULE UPGRADE REQUIRED**

### **Error Details:**
```
ValueError: View 'records_management.portal_file_search_create' in website 1 not found
```

**Location**: `/my/request/new/file_search` route  
**Root Cause**: Same as before - module reinstalled without upgrade

### **Solution (Immediate):**

**Option 1: Upgrade Module via UI (EASIEST)**
```
1. Apps → Search "Records Management"
2. Click "Upgrade" button
3. Wait for completion
4. Test /my/request/new/file_search
```

**Option 2: Command Line**
```bash
odoo-bin -u records_management -d your_database --stop-after-init
```

**Option 3: Force View Reload**
```sql
-- Delete view cache (forces recreation)
DELETE FROM ir_ui_view 
WHERE key = 'records_management.portal_file_search_create';

-- Restart Odoo to trigger view reload
```

### **Why This Keeps Happening:**

**Normal Flow**:
```
1. Install module → Load XML → Create views in DB
2. Views indexed for website context
3. Routes work ✅
```

**What Happened**:
```
1. Uninstall → Delete views from DB ✅
2. Reinstall → Load XML → Create views ✅
3. ❌ SKIP UPGRADE → Views not indexed for website
4. Routes fail ❌
```

**Prevention**:
- **ALWAYS** upgrade module after reinstall
- **IMMEDIATELY** re-enable RM configurator toggles
- **TEST** critical routes before deploying

---

## 📋 **COMPLETE ACTION PLAN**

### **IMMEDIATE (Critical Issues):**

1. **✅ Deploy Organization Chart Fix** (commit d1b0cf534)
   - Already pushed to main
   - Deploy to staging/production
   - Test `/my/organization`
   - Verify no AttributeError

2. **⏳ Upgrade Module** (fixes file search view)
   ```bash
   # In Odoo UI:
   Apps → Records Management → Upgrade
   
   # Or command line:
   odoo-bin -u records_management -d DB_NAME --stop-after-init
   ```
   - Test `/my/request/new/file_search`
   - Verify view loads without error

3. **⏳ Re-enable RM Configurator Toggles**
   - Settings → Records Management → Configuration
   - Enable ALL previously active toggles
   - Save configuration

### **NEXT (Enhancement - Calendar):**

4. **Convert Portal Calendar to Vanilla JS**
   - Find calendar template with inline JavaScript
   - Extract to separate file: `portal_calendar.js`
   - Convert using pattern above (remove odoo.define, use fetch)
   - Add to manifest `web.assets_frontend` bundle
   - Test `/my/calendar`

---

## 🧪 **TESTING CHECKLIST**

After applying all fixes:

- [ ] **Organization Chart** (`/my/organization`)
  - [ ] Page loads without AttributeError
  - [ ] Diagram displays with nodes/edges
  - [ ] Search functionality works
  - [ ] Layout switching works
  - [ ] Export function works
  - [ ] Department/user hierarchy correct

- [ ] **File Search** (`/my/request/new/file_search`)
  - [ ] Page loads without ValueError
  - [ ] Form displays correctly
  - [ ] Search containers button works
  - [ ] Can submit request
  - [ ] No JavaScript console errors

- [ ] **Calendar** (`/my/calendar`)
  - [ ] Page loads without TypeError
  - [ ] FullCalendar renders
  - [ ] Events load from `/my/calendar/events`
  - [ ] Event click shows modal
  - [ ] No console errors about odoo.define

- [ ] **Portal Home** (`/my/home`)
  - [ ] All counters display correctly
  - [ ] No null reference errors
  - [ ] Document counts load
  - [ ] All menu links work

---

## 🎯 **ROOT CAUSE SUMMARY**

All three issues stem from **improper module reinstall procedure**:

1. **Organization Chart**: Code bug (dict vs recordset) - FIXED
2. **Calendar**: Still using Odoo 17 JavaScript - NEEDS CONVERSION
3. **File Search**: Views not indexed - NEEDS UPGRADE

**Core Problem**: Module reinstalled without:
- Immediate upgrade to re-index views
- Re-enabling configurator toggles
- Testing critical routes

**Permanent Solution**:
1. Document proper reinstall procedure
2. Convert ALL JavaScript to vanilla (8 files + calendar)
3. Add validation tests to catch view indexing issues
4. Create pre-deployment checklist

---

## 📞 **NEXT STEPS FOR USER**

1. **Deploy** commit d1b0cf534 (organization chart fix)
2. **Upgrade** module via Apps UI
3. **Re-enable** RM configurator toggles
4. **Test** all three routes:
   - `/my/organization` - should work
   - `/my/request/new/file_search` - should work after upgrade
   - `/my/calendar` - will work after calendar conversion

5. **Report back**:
   - Confirm organization chart works
   - Confirm file search view loads
   - Note if calendar still has errors (expected - needs conversion)

---

**Status**: 1 of 3 issues fixed, 2 require user action (upgrade + calendar conversion)  
**Priority**: High - affects core portal functionality
