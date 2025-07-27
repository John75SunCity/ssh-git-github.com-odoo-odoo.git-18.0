# RECORDS MANAGEMENT - STANDARD ABBREVIATIONS SYSTEM

## 🎯 **TABLE NAME OPTIMIZATION**

Odoo has PostgreSQL table name limitations (63 characters max). Our module has many long model names that could cause conflicts. This document establishes standard abbreviations to create shorter, consistent model names.

---

## 📋 **ABBREVIATION STANDARDS**

### **Core Business Categories**
```
Records Management -> rec_mgmt
Records -> rec
Management -> mgmt
Document -> doc
Shredding -> shred
Destruction -> dest
Certificate -> cert
Inventory -> inv
Customer -> cust
Department -> dept
Billing -> bill
Pickup -> pick
Barcode -> bc
Location -> loc
Retention -> ret
Policy -> pol
Approval -> appr
Request -> req
Contact -> cont
Movement -> move
History -> hist
Transfer -> xfer
Workflow -> wf
Template -> tmpl
Configuration -> config
Validation -> valid
Notification -> notif
Feedback -> fb
Survey -> srv
Report -> rpt
```

### **Technical Categories**
```
Chain of Custody -> coc
NAID Compliance -> naid
Paper Baling -> pb
Trailer Loading -> tl
Work Order -> wo
Service -> svc
Product -> prod
Package -> pkg
Wizard -> wiz
Extension -> ext
Integration -> intg
Monitor -> mon
Security -> sec
Access -> acc
Authentication -> auth
Session -> sess
Attachment -> att
Message -> msg
Activity -> act
```

### **Status & State Terms**
```
Active -> act
Inactive -> inact
Draft -> dft
Confirmed -> conf
Completed -> comp
Cancelled -> canc
Pending -> pend
Processing -> proc
Approved -> appr
Rejected -> rej
Scheduled -> sched
```

---

## 🔧 **MODEL NAME MAPPING**

### **Current Long Names → New Abbreviated Names**

#### **Core Records Models**
```python
# OLD -> NEW
"records.box.movement.log"           -> "rec.box.move.log"
"records.department.billing.contact" -> "rec.dept.bill.cont"
"records.retention.policy.version"   -> "rec.ret.pol.ver"
"records.chain.of.custody"          -> "rec.coc"
"records.deletion.request"          -> "rec.del.req"
"records.approval.step"             -> "rec.appr.step"
"records.document.type"             -> "rec.doc.type"
"records.box.transfer"              -> "rec.box.xfer"
"customer.inventory.report"         -> "cust.inv.rpt"
"document.retrieval.rates"          -> "doc.ret.rates"
"document.retrieval.work.order"     -> "doc.ret.wo"
```

#### **Shredding & Destruction Models**
```python
# OLD -> NEW
"shredding.service"                 -> "shred.svc"
"work.order.shredding"             -> "wo.shred"
"destruction.item"                 -> "dest.item"
"witness.verification"             -> "witness.valid"
"destruction.certificate"          -> "dest.cert"
"paper.bale.recycling"             -> "pb.recycl"
"paper.load.shipment"              -> "pb.ship"
```

#### **NAID & Compliance Models**
```python
# OLD -> NEW
"naid.audit.log"                   -> "naid.audit"
"naid.certificate"                 -> "naid.cert"
"naid.compliance"                  -> "naid.comp"
"naid.custody.event"               -> "naid.coc.event"
"chain.of.custody"                 -> "coc.chain"
```

#### **Portal & Customer Models**
```python
# OLD -> NEW
"portal.request"                   -> "portal.req"
"customer.feedback"                -> "cust.fb"
"customer.inventory"               -> "cust.inv"
"survey.improvement.action"        -> "srv.improve.act"
"survey.user.input"               -> "srv.user.input"
```

#### **Billing & Department Models**
```python
# OLD -> NEW
"department.billing"               -> "dept.bill"
"billing.automation"               -> "bill.auto"
"departmental.billing.contact"     -> "dept.bill.cont"
"records.department"               -> "rec.dept"
```

#### **Barcode & Integration Models**
```python
# OLD -> NEW
"barcode.product"                  -> "bc.prod"
"barcode.models"                   -> "bc.model"
"partner.bin.key"                  -> "partner.bin"
"visitor.pos.wizard"               -> "visitor.pos.wiz"
"mobile.bin.key.wizard"           -> "mobile.bin.wiz"
```

#### **Technical & Extension Models**
```python
# OLD -> NEW
"stock.move.sms.validation"        -> "stock.sms.valid"
"stock.lot.attribute"              -> "stock.lot.attr"
"stock.report_reception_report_label" -> "stock.recv.label"
"box.type.converter"               -> "box.type.conv"
"permanent.flag.wizard"            -> "perm.flag.wiz"
```

#### **Monitoring Models**
```python
# OLD -> NEW
"records.management.monitor"       -> "rec.mgmt.mon"
```

---

## 🔄 **IMPLEMENTATION STRATEGY**

### **Phase 1: Update Model Names**
1. Update `_name` attributes in Python files
2. Update security rules (`ir.model.access.csv`)
3. Update view references in XML files
4. Update menu actions and references

### **Phase 2: Update View IDs**
1. Shorten view IDs to match model names
2. Update action IDs
3. Update menu IDs
4. Update report IDs

### **Phase 3: Update References**
1. Update Many2one/One2many field references
2. Update domain filters
3. Update computed field references
4. Update workflow transitions

---

## 📝 **NAMING CONVENTION RULES**

### **Model Names**
```python
# Pattern: category.subcategory.type
# Max length: 25 characters (safe PostgreSQL limit)
# Examples:
_name = "rec.box.move"      # Records Box Movement
_name = "shred.svc"         # Shredding Service  
_name = "naid.cert"         # NAID Certificate
_name = "cust.fb"           # Customer Feedback
```

### **View IDs**
```xml
<!-- Pattern: view_model_name_type -->
<!-- Examples: -->
<record id="view_rec_box_tree" model="ir.ui.view">
<record id="view_shred_svc_form" model="ir.ui.view">
<record id="view_naid_cert_search" model="ir.ui.view">
```

### **Action IDs**
```xml
<!-- Pattern: action_model_name -->
<!-- Examples: -->
<record id="action_rec_box" model="ir.actions.act_window">
<record id="action_shred_svc" model="ir.actions.act_window">
<record id="action_naid_cert" model="ir.actions.act_window">
```

### **Menu IDs**
```xml
<!-- Pattern: menu_category_item -->
<!-- Examples: -->
<menuitem id="menu_rec_box" name="Boxes">
<menuitem id="menu_shred_svc" name="Shredding">
<menuitem id="menu_naid_cert" name="Certificates">
```

---

## 🚀 **BENEFITS**

### **Technical Benefits**
- ✅ **No Table Name Conflicts**: All names under PostgreSQL limits
- ✅ **Faster Database Operations**: Shorter table names = better performance
- ✅ **Cleaner Code**: Consistent, predictable naming
- ✅ **Easier Debugging**: Shorter names in logs and traces

### **Development Benefits**
- ✅ **Faster Typing**: Shorter model references
- ✅ **Better Readability**: Clear, consistent abbreviations
- ✅ **Reduced Errors**: Standardized naming reduces typos
- ✅ **Easier Maintenance**: Systematic naming makes changes easier

### **Deployment Benefits**
- ✅ **Cross-Platform Compatibility**: Works on all database systems
- ✅ **Migration Safety**: No table name length issues
- ✅ **Backup Efficiency**: Shorter names in backup files
- ✅ **Log Clarity**: Cleaner, more readable logs

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Model Files** (87 files to update)
- [ ] Update `_name` attributes
- [ ] Update `_inherit` references where needed
- [ ] Update Many2one/One2many comodel references
- [ ] Update computed field model references

### **View Files** (40+ files to update)
- [ ] Update model references in `<record model="">`
- [ ] Update view IDs for consistency
- [ ] Update action model references
- [ ] Update domain filters

### **Security Files**
- [ ] Update `ir.model.access.csv` model names
- [ ] Update security group rules
- [ ] Update record rules model references

### **Data Files**
- [ ] Update sequence model references
- [ ] Update demo data model references
- [ ] Update mail template model references

### **Reports**
- [ ] Update report model references
- [ ] Update report template model references

---

## 🎯 **EXECUTION PLAN**

1. **Create automated script** to update all model names
2. **Update security files** with new model names
3. **Update view files** with new model and view IDs
4. **Update data files** with new references
5. **Test module installation** to verify no conflicts
6. **Update documentation** with new naming conventions

This systematic abbreviation approach will solve table name conflicts and create a much cleaner, more maintainable codebase! 🚀
