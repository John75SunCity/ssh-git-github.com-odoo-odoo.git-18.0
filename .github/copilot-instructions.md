# GitHub Copilot Instructions for Odoo Records Management System

## 🎯 Project Overview

This is a **comprehensive enterprise-grade Odoo 18.0 Records Management module** with NAID AAA compliance features. The codebase follows systematic patterns for field implementation, strict inheritance hierarchies, and comprehensive workflow tracking.

### **Core Architecture Principles**
- **Systematic Pattern Recognition**: All fields follow categorized implementation patterns
- **Comprehensive Field Coverage**: 1,400+ field references with 85% error reduction achieved
- **Inheritance-Based Design**: All models inherit from `mail.thread` and `mail.activity.mixin`
- **NAID Compliance**: Strict adherence to destruction and chain of custody requirements

---

## 🏗️ **ESSENTIAL ARCHITECTURE KNOWLEDGE**

### **1. Model Architecture Patterns**

```python
# STANDARD MODEL TEMPLATE - Follow this pattern for ALL new models
class RecordsModel(models.Model):
    _name = 'records.model.name'
    _description = 'Model Description'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # REQUIRED CORE FIELDS (ALL models must have these)
    name = fields.Char(string='Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    
    # WORKFLOW FIELDS (Add based on model requirements)
    state = fields.Selection([...], default='draft', tracking=True)
    
    # COMPUTE METHODS (Follow this naming pattern)
    @api.depends('field_name')
    def _compute_field_name(self):
        # Implementation
        
    # ACTION METHODS (Follow this naming pattern)
    def action_verb_object(self):
        # Implementation
```

### **2. Field Implementation Categories**

**ALWAYS implement fields in these systematic categories:**

#### **Core Workflow Fields** (Required for all models)
```python
# Basic identification and workflow
name = fields.Char(required=True, tracking=True)
description = fields.Text()
state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done')])
company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
active = fields.Boolean(default=True)
```

#### **Timing & Scheduling Fields** (Critical for service models)
```python
# Comprehensive timing tracking
date = fields.Date(default=fields.Date.today)
start_date = fields.Datetime()
end_date = fields.Datetime()
actual_start_time = fields.Datetime()
actual_completion_time = fields.Datetime()
estimated_duration = fields.Float()
```

#### **Personnel & Assignment Fields** (For workflow models)
```python
# Complete personnel tracking
assigned_technician = fields.Many2one('res.users')
supervising_manager = fields.Many2one('res.users')
security_officer = fields.Many2one('res.users')
customer_representative = fields.Many2one('res.partner')
```

#### **Documentation & Verification Fields** (NAID compliance)
```python
# Comprehensive documentation tracking
signature_required = fields.Boolean()
signature_verified = fields.Boolean()
photo_id_verified = fields.Boolean()
verified = fields.Boolean()
verified_by_customer = fields.Boolean()
verification_date = fields.Datetime()
third_party_verified = fields.Boolean()
destruction_photographed = fields.Boolean()
video_recorded = fields.Boolean()
destruction_notes = fields.Text()
```

### **3. Critical Model Relationships**

#### **Shredding Service Model** (Primary workflow hub)
- **145 fields total** - Most comprehensive model
- Links to: `destruction.item`, `witness.verification`, `chain.of.custody`
- Key computed fields: `total_weight`, `destruction_efficiency`

#### **Records Retention Policy** (Policy management)
- **69 fields total** with version control
- Links to: `records.policy.version` (One2many)
- Computed analytics: `_compute_exception_count()`, `_compute_analytics()`

#### **Core Record Models**
```python
# Standard relationship patterns
box_ids = fields.One2many('records.box', 'parent_id')
document_ids = fields.One2many('records.document', 'parent_id')
tag_ids = fields.Many2many('records.tag', string='Tags')
location_id = fields.Many2one('records.location')
retention_policy_id = fields.Many2one('records.retention.policy')
```

---

## 🔧 **DEVELOPMENT WORKFLOW COMMANDS**

### **Essential Development Commands** (Always use these)

```bash
# CRITICAL: Start Odoo in development mode
./odoo-bin --addons-path=addons,/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management --dev=all --log-level=debug

# Module installation/update (ALWAYS update after changes)
./odoo-bin -d records_management -i records_management --stop-after-init

# Database reset (when model changes require it)
./odoo-bin -d records_management --db-filter=records_management --stop-after-init

# Comprehensive field validation (Run after any model changes)
python records_management/comprehensive_field_analysis.py

# Auto-sync with enterprise branch (Daily workflow)
./development-tools/auto_sync_main.sh
```

### **Critical Development Tools**

#### **Field Audit Scripts** (Use before making changes)
```bash
# Check for missing fields across all views
python records_management/find_all_missing_fields.py

# Comprehensive field analysis
python records_management/comprehensive_field_analysis.py

# Advanced field analysis for specific models
python records_management/advanced_field_analysis.py
```

#### **Session Management**
```bash
# Keep development session alive
./development-tools/keep_session_alive.sh

# Auto-sync and maintain workspace
./development-tools/auto_sync_main.sh
```

---

## 📋 **CODING STANDARDS & PATTERNS**

### **1. Field Naming Conventions**

```python
# CORRECT field naming patterns
certificate_number = fields.Char()           # Descriptive, underscore-separated
chain_of_custody_ids = fields.One2many()     # Plural for One2many/Many2many
pre_destruction_weight = fields.Float()      # Clear temporal indicators
naid_member_id = fields.Many2one()          # Standard abbreviations (NAID)

# INCORRECT naming
cert_num = fields.Char()                     # Avoid abbreviations
chainCustody = fields.One2many()             # Avoid camelCase
weight1 = fields.Float()                     # Avoid numeric suffixes
```

### **2. Method Implementation Patterns**

#### **Compute Methods** (Always use @api.depends)
```python
@api.depends('destruction_item_ids', 'destruction_item_ids.weight')
def _compute_total_weight(self):
    for record in self:
        record.total_weight = sum(record.destruction_item_ids.mapped('weight'))

@api.depends('policy_exception_ids')
def _compute_exception_count(self):
    for record in self:
        record.exception_count = len(record.policy_exception_ids)
```

#### **Action Methods** (Follow naming pattern: action_verb_object)
```python
def action_confirm_shredding(self):
    """Confirm shredding service - follows systematic action pattern"""
    self.ensure_one()
    if self.state != 'draft':
        raise UserError(_('Can only confirm draft services'))
    self.write({'state': 'confirmed'})
    
def action_complete_destruction(self):
    """Complete destruction workflow with verification"""
    self.ensure_one()
    # Verification logic here
    self.write({'state': 'done', 'completion_date': fields.Datetime.now()})
```

### **3. Security Implementation**

```python
# ALWAYS implement security groups for new models
# File: security/ir.model.access.csv
access_model_name_user,model.name.user,model_model_name,records_management.group_records_user,1,1,1,0
access_model_name_manager,model.name.manager,model_model_name,records_management.group_records_manager,1,1,1,1
```

---

## 🚨 **CRITICAL ERROR PREVENTION**

### **1. Missing Field Patterns** (ALWAYS check for these)

When creating views, ensure these field categories exist in models:
- **Core fields**: `name`, `company_id`, `user_id`, `active`
- **Timing fields**: `date`, `start_date`, `end_date`
- **Personnel fields**: `assigned_technician`, `supervising_manager`
- **State management**: `state`, tracking fields
- **Documentation**: Certificate, verification, and notes fields

### **2. Common View Field Errors** (Prevent these)

```xml
<!-- WRONG: Field doesn't exist in model -->
<field name="missing_field"/>

<!-- CORRECT: Verify field exists in Python model first -->
<field name="verified_field"/>
```

### **3. Model Inheritance Requirements**

```python
# ALWAYS include both inheritance types for workflow models
_inherit = ['mail.thread', 'mail.activity.mixin']

# REQUIRED for proper functionality
_order = 'name'  # Or appropriate sorting field
_rec_name = 'name'  # Or field that represents the record
```

---

## 📁 **PROJECT STRUCTURE UNDERSTANDING**

### **Key Directories & Their Purposes**

```
records_management/
├── models/                    # 50+ Python models (PRIMARY WORK AREA)
│   ├── shredding_service.py  # 145 fields - Most complex model
│   ├── records_retention_policy.py  # 69 fields - Policy management
│   └── [other models]        # Follow same patterns
├── views/                     # 40+ XML view files (FIELD VALIDATION CRITICAL)
├── data/                      # Configuration data and sequences
├── security/                  # ir.model.access.csv (100+ access rules)
├── wizards/                   # User interaction wizards
├── tests/                     # Unit tests (test_records_management.py)
└── COMPREHENSIVE_REFERENCE.md # 481 lines - ESSENTIAL reading
```

### **Critical Reference Files**

1. **`COMPREHENSIVE_REFERENCE.md`** - 481 lines documenting all models and fields
2. **`SYSTEMATIC_FIELD_IMPLEMENTATION_COMPLETE.md`** - Field implementation patterns
3. **`README.md`** - 401 lines of setup and usage documentation
4. **`__manifest__.py`** - 154 lines defining module dependencies

---

## 🔍 **DEBUGGING & VALIDATION WORKFLOW**

### **Step-by-Step Debugging Process**

1. **Field Validation** (After any model changes)
   ```bash
   python records_management/comprehensive_field_analysis.py
   ```

2. **View Validation** (Check all XML files)
   ```bash
   python records_management/find_all_missing_fields.py
   ```

3. **Module Update** (Apply changes)
   ```bash
   ./odoo-bin -d records_management -u records_management --stop-after-init
   ```

4. **Log Analysis** (Check for errors)
   ```bash
   tail -f /var/log/odoo/odoo.log | grep -E "(ERROR|WARNING)"
   ```

### **Common Error Resolution Patterns**

#### **ParseError in Views**
- **Cause**: Missing fields in Python models
- **Solution**: Add fields following systematic patterns above
- **Validation**: Run field analysis scripts

#### **Access Rights Errors**
- **Cause**: Missing entries in `security/ir.model.access.csv`
- **Solution**: Add both user and manager access rules
- **Pattern**: Follow existing access rule naming

#### **Import Errors**
- **Cause**: Missing dependencies or circular imports
- **Solution**: Check `__manifest__.py` dependencies
- **Validation**: Test module installation from scratch

---

## 🎯 **IMPLEMENTATION BEST PRACTICES**

### **1. Before Making Any Changes**

1. **Read COMPREHENSIVE_REFERENCE.md** - Understand existing patterns
2. **Check current field coverage** - Run analysis scripts
3. **Identify missing field patterns** - Look for systematic gaps
4. **Plan implementation** - Group related fields together

### **2. When Adding New Models**

1. **Follow template pattern** - Use standard inheritance and field categories
2. **Implement security rules** - Add to ir.model.access.csv
3. **Create comprehensive fields** - Don't implement minimal field sets
4. **Add computed methods** - Follow _compute_field_name pattern
5. **Include action methods** - Follow action_verb_object pattern

### **3. When Modifying Existing Models**

1. **Preserve existing patterns** - Don't break established conventions
2. **Add fields in categories** - Group related fields together
3. **Update related views** - Ensure all fields are accessible
4. **Test thoroughly** - Run comprehensive validation scripts

### **4. Quality Assurance Checklist**

- [ ] All models inherit from `['mail.thread', 'mail.activity.mixin']`
- [ ] Core fields (name, company_id, user_id, active) present
- [ ] Security rules defined for user and manager groups
- [ ] Computed methods use `@api.depends` decorators
- [ ] Action methods follow naming conventions
- [ ] Field analysis scripts run without errors
- [ ] Module installs/updates successfully

---

## 🚀 **QUICK START FOR NEW CONTRIBUTORS**

### **Immediate Orientation Steps**

1. **Read the comprehensive reference**: `records_management/COMPREHENSIVE_REFERENCE.md`
2. **Check current project status**: `development-tools/workspace-config/CURRENT_SESSION_STATUS.md`
3. **Run field analysis**: `python records_management/comprehensive_field_analysis.py`
4. **Start development server**: Follow development workflow commands above
5. **Review recent changes**: Check systematic field implementation completion report

### **Common Task Patterns**

#### **Adding Missing Fields**
1. Identify missing fields from view files
2. Group fields by category (timing, personnel, documentation, etc.)
3. Add fields following systematic patterns
4. Update security if needed
5. Validate with analysis scripts

#### **Creating New Workflows**
1. Start with standard model template
2. Implement all field categories
3. Add state management with tracking
4. Create action methods for state transitions
5. Implement comprehensive security rules

#### **Debugging Field Issues**
1. Run `find_all_missing_fields.py` to identify problems
2. Check model inheritance patterns
3. Verify field naming conventions
4. Validate with comprehensive analysis
5. Test module installation

---

## 📚 **ESSENTIAL DOCUMENTATION REFERENCES**

- **Primary Architecture**: `records_management/COMPREHENSIVE_REFERENCE.md` (481 lines)
- **Field Implementation**: `records_management/SYSTEMATIC_FIELD_IMPLEMENTATION_COMPLETE.md`
- **Setup Guide**: `records_management/README.md` (401 lines)
- **Current Status**: `development-tools/workspace-config/CURRENT_SESSION_STATUS.md`
- **Development Workflow**: `development-tools/workspace-config/DEVELOPMENT.md`

---

*This document represents the essential knowledge for productive AI agent work on this complex Odoo Records Management system. Follow these patterns for consistency and reliability.*
