# Odoo 18.0 Records Management - AI Coding Instructions

Enterprise NAID AAA-compliant Document Management System. **Stable production codebase** – preserve patterns, minimize diffs.

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Validate before EVERY commit
python3 development-tools/comprehensive_validator.py

# Check field relationships
python3 development-tools/analysis-reports/comprehensive_field_analysis.py

# Verify security rules
grep "model_YOUR_MODEL" records_management/security/ir.model.access.csv

# Standard deployment
git add . && git commit -m "fix: description" && git push origin main
```

### VS Code Tasks (Keyboard: Cmd+Shift+B)
- **Validate Records Management Module** - Syntax + schema validation (ALWAYS before commit)
- **Run Comprehensive Field Analysis** - Detect field/model inconsistencies
- **RM System Integrity Checklist** - Pre-commit guardrail verification
- **Deploy to GitHub (Git Push)** - Push after validation passes

### ⚠️ CRITICAL POLICY
**DO NOT run local Odoo server in this workspace.** Use Odoo.sh staging for functional testing. This prevents local-only config commits.

---

## 📐 Architecture Overview

### Core Model Domains (230+ models)
```python
# Container Lifecycle
records.container → records.location → chain.of.custody → naid.audit.log

# Billing Pipeline
records.billing → billing.period → customer.negotiated.rate → account.move

# NAID Compliance
naid.certificate → destruction.certificate → naid.custody → naid.audit.log

# Portal Interface
portal.request → customer.inventory → portal.feedback → signed.document
```

### Key Architectural Patterns

**RM Module Configurator** (`models/rm_module_configurator.py`)
- Central control for ALL feature visibility toggles
- New features MUST register here (mandatory)
- Enables enterprise-grade configurability

**Department-Based Security**
- Record rules filter by `partner_id.user_ids` or `department.user_ids`
- Granular access via `security/ir.model.access.csv` (user + manager ACLs)
- Example: `security/portal_container_rules.xml`

**Barcode-Driven Workflows** (`models/barcode_container_operations.py`)
- Standard commands: ACTIVATE, INDEX, RETRIEVE, DESTROY
- Scan triggers → state transition → audit log creation
- UI buttons: `views/barcode_standard_commands_buttons.xml`

---

## 🛠️ Odoo Coding Standards (Project-Specific)

### File Organization - STRICT
```
records_management/
├── models/          # ONE model per file, named after primary model
├── controllers/     # HTTP routes for portal/API
├── views/           # XML views: {model}_views.xml
├── templates/       # QWeb portal templates
├── security/        # ir.model.access.csv + XML rules
├── data/            # Default data, sequences, cron jobs
├── report/          # Report templates (174 files)
├── static/src/      # JS/CSS (no minified libs in repo)
└── wizards/         # Transient model wizards
```

### Python Conventions
```python
# Imports (alphabetical within groups)
from odoo import Command, _, api, fields, models  # ASCII order
from odoo.exceptions import UserError, ValidationError

# Model structure
class RecordsContainer(models.Model):
    _name = 'records.container'  # Singular
    _description = 'Records Container Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    # Section order: private attrs → defaults → fields → 
    # compute/inverse → constraints → CRUD → actions → business methods
    
    # Relations MUST specify comodel_name
    partner_id = fields.Many2one(comodel_name='res.partner', required=True)
    
    # Batch-safe create
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_audit_log('created')
        return records
```

### XML Conventions
```xml
<!-- View XML IDs: {model_name}_view_{form|tree|search} -->
<record id="records_container_view_form" model="ir.ui.view">
    <field name="name">records.container.view.form</field>
    <field name="model">records.container</field>
    <field name="arch" type="xml">
        <form>
            <!-- Odoo 18: Use invisible/readonly attrs, not legacy attrs= -->
            <field name="state" invisible="state == 'draft'"/>
        </form>
    </field>
</record>

<!-- Actions: {model_name}_action -->
<record id="records_container_action" model="ir.actions.act_window">
    <field name="name">Containers</field>
    <field name="res_model">records.container</field>
</record>
```

### Translation Policy (Project Override)
```python
# ✅ CORRECT - Interpolation AFTER translation
_("Container %s activated") % container.name
_("Found %d items") % len(items)

# ❌ WRONG - Never pass arguments to _()
_("Container %s activated", container.name)  # WRONG!
```

---

## 🔒 System Integrity Checklist (MANDATORY)

### When Creating/Modifying Models

**STEP 0: Model Structure Validation**
```bash
# Search existing models FIRST - avoid duplication
grep -r "_name.*container" records_management/models/
grep -r "_description.*inventory" records_management/models/

# ONE model per file rule - verify before creating
# ✅ models/records_container.py → class RecordsContainer
# ❌ models/records_container.py → class RecordsContainer + class RecordsLocation
```

**STEP 1-4: Required File Updates**
1. **Python Model** - `models/YOUR_MODEL.py`
2. **Models Init** - Add to `models/__init__.py` (correct dependency order)
3. **Security CSV** - Add to `security/ir.model.access.csv`:
   ```csv
   access_your_model_user,your.model.user,model_your_model,records_management.group_records_user,1,1,1,0
   access_your_model_manager,your.model.manager,model_your_model,records_management.group_records_manager,1,1,1,1
   ```
4. **XML Views** - Create `views/YOUR_MODEL_views.xml` (form, tree, search)

**STEP 5-7: Integration Points**
5. **RM Configurator** - Add visibility toggle to `models/rm_module_configurator.py`
6. **Menus** - Update `views/records_management_menus.xml`
7. **Portal** (if needed) - Add routes to `controllers/portal.py` + templates

### Common Failure Modes
❌ Missing `comodel_name` in Many2one/One2many/Many2many  
❌ Empty Selection fields (must have choices + default)  
❌ Monetary field relating to Float field (type mismatch)  
❌ View referencing non-existent model fields  
❌ Forgetting security CSV entries → module won't load  
❌ Multiple models in one file → import conflicts  

---

## 🌐 Portal Architecture (200+ Routes)

### Route Organization
```python
# controllers/portal.py - Main portal controller
@http.route(['/my/inventory'], type='http', auth="user", website=True)
def portal_my_inventory(self, **kw):
    # Customer inventory CRUD operations
    
@http.route(['/my/containers'], type='http', auth="user", website=True)
def portal_containers(self, **kw):
    # Container lifecycle management (create/edit/delete)
    
@http.route(['/my/requests/create'], type='http', auth="user", website=True)
def portal_request_create(self, **kw):
    # Service requests (retrieval, destruction, scanning)
```

### Frontend Stack
- **Backend**: Odoo HTTP controllers (standard patterns)
- **Frontend**: Vanilla JavaScript (NO jQuery/ESM in portal per Odoo 18 guidelines)
- **Assets**: `web.assets_frontend` bundle (see `__manifest__.py`)
- **Templates**: QWeb in `templates/` directory

### Key Portal Templates
```
templates/portal_my_menu.xml          # Unified portal home (10 sections, 50+ routes)
templates/portal_inventory_detail.xml # Inventory CRUD with AJAX
templates/portal_container_detail.xml # Container edit/delete
templates/portal_document_center.xml  # Centralized document hub
templates/portal_certificates.xml     # NAID compliance downloads
```

---

## 🔍 Model Discovery & Reuse

### Before Creating ANY New Model
```bash
# 1. Search by business domain
grep -r "_name.*billing" records_management/models/
grep -r "_name.*location" records_management/models/

# 2. Check descriptions for similar functionality
grep -r "_description.*" records_management/models/ | grep -i "container"

# 3. List all models (230+ files)
ls records_management/models/*.py | wc -l
```

### Model Capability Matrix (Top 20)
| Model | Purpose | Key Relations |
|-------|---------|---------------|
| `records.container` | Box/container lifecycle | `location_id`, `partner_id`, `container_type_id` |
| `records.location` | Storage location hierarchy | `parent_id`, `container_ids` |
| `records.billing` | Invoice generation | `partner_id`, `billing_line_ids` |
| `chain.of.custody` | NAID audit trail | `container_id`, `from_user_id`, `to_user_id` |
| `portal.request` | Customer service requests | `partner_id`, `request_line_ids`, `signed_document_ids` |
| `naid.certificate` | Compliance certificates | `partner_id`, `certificate_item_ids` |
| `customer.inventory` | Portal inventory view | `partner_id`, `inventory_line_ids` |
| `records.document` | Document metadata | `container_id`, `file_id`, `document_type_id` |
| `destruction.certificate` | Destruction proof | `partner_id`, `destruction_event_ids` |
| `barcode.storage.box` | Barcode operations | `container_id`, `generation_history_ids` |

**Rule**: If similar model exists, use `_inherit` or extend it. Only create new model if NO overlap exists.

---

## 🧪 Development Workflow

### Pre-Commit Checklist
```bash
# 1. Run comprehensive validator (catches 95% of issues)
python3 development-tools/comprehensive_validator.py

# 2. Check for new model imports
grep "from . import" records_management/models/__init__.py | tail -5

# 3. Verify security rules exist
grep "model_YOUR_NEW_MODEL" records_management/security/ir.model.access.csv

# 4. Test views reference real fields
# Manual: Open view file, verify field names match model definition

# 5. Run system integrity checklist
# VS Code: Cmd+Shift+B → "RM System Integrity Checklist"
```

### Deployment Strategy
1. **Local validation** - Run `comprehensive_validator.py`
2. **Git commit** - Use conventional commits: `fix:`, `feat:`, `refactor:`
3. **Push to GitHub** - Triggers Odoo.sh staging deployment
4. **Monitor staging** - Check Odoo.sh logs for runtime errors
5. **Iterate** - Fix errors one at a time, redeploy

**Proven Pattern**: Fix one error → commit → deploy → get next error (live error detection)

---

## 📦 Module Dependencies & Integration

### Critical Dependencies (`__manifest__.py`)
```python
'depends': [
    'base', 'mail', 'web', 'portal',          # Core
    'account', 'sale', 'stock', 'product',     # Business
    'industry_fsm',  # Field Service (REQUIRED)
    'sign',          # E-signatures (REQUIRED)
    'maintenance',   # Equipment tracking (REQUIRED)
    'quality',       # Inspections (REQUIRED)
    'barcodes',      # Barcode scanning (REQUIRED)
    'survey',        # Feedback system
    'web_vis_network',  # Diagram visualization
]
```

### Integration Patterns
```python
# FSM Integration (industry_fsm module)
# - Work orders for container retrieval/destruction
# - Technician assignment and tracking
# See: models/container_retrieval_work_order.py

# Sign Integration (sign module)  
# - E-signatures on destruction requests
# - Portal certificate signing
# See: models/portal_request.py, models/destruction_certificate.py

# Accounting Integration (account module)
# - Automated invoice generation from billing records
# - Payment reconciliation
# See: models/records_billing.py
```

---

## 🚨 Critical Anti-Patterns (NEVER DO THIS)

### ❌ Multiple Models Per File
```python
# ❌ WRONG - models/records_management.py
class RecordsContainer(models.Model):
    _name = 'records.container'
    
class RecordsLocation(models.Model):  # WRONG! Separate file!
    _name = 'records.location'
```

### ❌ Missing Comodel Names
```python
# ❌ WRONG
partner_id = fields.Many2one('res.partner')  # Missing comodel_name=

# ✅ CORRECT
partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
```

### ❌ Unsafe Create Operations
```python
# ❌ WRONG - Not batch-safe
def create(self, vals):
    record = super().create(vals)
    return record

# ✅ CORRECT - Batch-safe
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    for record in records:
        # Process each record
    return records
```

### ❌ View Fields Without Model Definitions
```xml
<!-- ❌ WRONG - Field doesn't exist in model -->
<field name="some_field_not_in_model"/>

<!-- Check model first:
grep "some_field" records_management/models/YOUR_MODEL.py
-->
```

---

## 💡 Pro Tips

### Odoo.sh Commands
```bash
# Update module after deploy
odoosh-restart --update records_management

# VS code push triggers auto-deploy, no manual update needed
```

### Field Type Compatibility
```python
# ✅ Compatible pairs
Monetary ↔ Monetary
Float ↔ Float  
Integer ↔ Integer
Selection(string) ↔ Selection(string)

# ❌ Incompatible - will cause deployment errors
Monetary ↔ Float  # Type mismatch!
Selection(string) ↔ Selection(integer)  # Different selection types!
```

### Debug View Issues
```bash
# Find all references to a field
grep -r "field_name" records_management/views/

# Check if model is registered
grep "model_name" records_management/models/__init__.py

# Verify security access
grep "model_name" records_management/security/ir.model.access.csv
```

### Translation Tips
```python
# Dynamic values - use % after translation
msg = _("Processing %s items") % count

# Pluralization
if count == 1:
    msg = _("1 item")
else:
    msg = _("%d items") % count

# Never use .format() or f-strings with _()
# ❌ WRONG: _(f"Count: {count}")
# ✅ CORRECT: _("Count: %s") % count
```

---

## 📚 Additional Resources

### Key Files to Reference
- `models/rm_module_configurator.py` - Feature toggle patterns
- `models/records_container.py` - Model structure example
- `controllers/portal.py` - Portal route patterns  
- `views/records_container_views.xml` - View XML patterns
- `security/ir.model.access.csv` - Security rule patterns

### Documentation
- `.github/copilot-instructions.md` - This file
- `handbook/RECORDS_MANAGEMENT_HANDBOOK.md` - User guide
- `handbook/custom-fields-reference.md` - Field customization
- `development-tools/README_VALIDATOR.md` - Validation tool docs

### Common Searches
```bash
# Find model by name
grep -r "_name = 'records.container'" records_management/models/

# Find all portal routes  
grep -r "@http.route" records_management/controllers/

# Find all wizards
ls records_management/wizards/*.py

# Count total models
find records_management/models -name "*.py" -not -name "__init__.py" | wc -l

# Find views for a model
grep -l "records.container" records_management/views/*.xml
```

---

## 🎓 Learning by Example

### Creating a New Model (Complete Workflow)

**1. Search for existing similar models**
```bash
grep -r "_name.*certification" records_management/models/
# Found: naid_operator_certification.py - different purpose, create new
```

**2. Create model file** - `models/technician_certification.py`
```python
from odoo import api, fields, models

class TechnicianCertification(models.Model):
    _name = 'technician.certification'
    _description = 'Technician Certifications'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc'
    
    name = fields.Char(required=True, tracking=True)
    technician_id = fields.Many2one(comodel_name='res.users', required=True)
    certification_type = fields.Selection([
        ('naid', 'NAID AAA'),
        ('forklift', 'Forklift Operator'),
    ], default='naid', required=True)
    issue_date = fields.Date(required=True)
    expiry_date = fields.Date()
    active = fields.Boolean(default=True)
```

**3. Add to models init** - `models/__init__.py`
```python
# Add in alphabetical order
from . import technician_certification
```

**4. Add security rules** - `security/ir.model.access.csv`
```csv
access_technician_certification_user,technician.certification.user,model_technician_certification,records_management.group_records_user,1,1,1,0
access_technician_certification_manager,technician.certification.manager,model_technician_certification,records_management.group_records_manager,1,1,1,1
```

**5. Create views** - `views/technician_certification_views.xml`
```xml
<odoo>
    <record id="technician_certification_view_form" model="ir.ui.view">
        <field name="name">technician.certification.view.form</field>
        <field name="model">technician.certification</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="technician_id"/>
                        <field name="certification_type"/>
                        <field name="issue_date"/>
                        <field name="expiry_date"/>
                    </group>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>
    
    <record id="technician_certification_action" model="ir.actions.act_window">
        <field name="name">Certifications</field>
        <field name="res_model">technician.certification</field>
        <field name="view_mode">tree,form</field>
    </record>
    
    <menuitem id="technician_certification_menu"
              name="Certifications"
              parent="records_management.menu_records_configuration"
              action="technician_certification_action"
              sequence="45"/>
</odoo>
```

**6. Add to manifest** - `__manifest__.py`
```python
'data': [
    # ... existing entries ...
    'views/technician_certification_views.xml',  # Add in views section
]
```

**7. Add RM Configurator toggle** - `models/rm_module_configurator.py`
```python
show_technician_certifications = fields.Boolean(
    string="Show Technician Certifications",
    default=True,
    help="Display technician certification tracking"
)
```

**8. Validate before commit**
```bash
python3 development-tools/comprehensive_validator.py
# ✅ All checks passed

git add .
git commit -m "feat: Add technician certification model"
git push origin main
```

---

**Last Updated**: November 26, 2025  
**Odoo Version**: 18.0  
**Module Version**: 18.0.1.0.26
