# GitHub Copilot Instructions for Odoo Records Management System

## 🎯 Project Overview

This is a **comprehensive### **Development and Deployment Workflow**enterprise-grade Odoo 18.0 Records Management module** with NAID AAA compliance features. The codebase implements systematic patterns for field management, strict inheritance hierarchies, and comprehensive workflow tracking across 50+ models and 1,400+ fields.

### **Critical Deployment Architecture**
- **Primary Method: Odoo.sh & GitHub** - The most reliable workflow is pushing to GitHub to trigger an automatic build and deployment on Odoo.sh for testing.
- **Cloud Development: GitHub Codespaces** - A fully configured cloud environment is available via GitHub Codespaces for rapid development.
- **Local Development Option**: A minimal local setup is possible but requires a separate Odoo 18.0 installation. The primary testing and validation loop remains through Odoo.sh.
- **GitHub-Driven Deployment**: All changes must be committed and pushed to the GitHub repository to be deployed on Odoo.sh.
- **Testing Workflow**: Code → GitHub → Odoo.sh rebuild → Live testing in cloud environment.

### **Core Architecture Principles**
- **Service-Oriented Architecture**: Clear separation between core records management, compliance tracking, and customer portal services
- **Systematic Model Loading**: Models loaded in dependency order to prevent KeyError exceptions during ORM setup
- **Enterprise Inheritance Pattern**: All workflow models inherit from `['mail.thread', 'mail.activity.mixin']` for audit trails
- **NAID AAA Compliance**: Complete chain of custody tracking with encrypted signatures and audit logging

---

## 🏗️ **ESSENTIAL ARCHITECTURE KNOWLEDGE**

### **1. Service Boundaries & Data Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core Records  │◄──►│ NAID Compliance │◄──►│ Customer Portal │
│   Management    │    │   & Auditing    │    │   & Workflows   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Box/Document              Chain of Custody        Portal Requests
   Lifecycle Mgmt           Destruction Audit         Service Requests
   Location Tracking        Certificate Mgmt          E-Signatures
```

**Core Service Communication:**
- **Records → Compliance**: All box movements trigger NAID audit logs
- **Compliance → Portal**: Certificates and audit trails flow to customer portal  
- **Portal → Records**: Service requests create workflow tasks in records system

### **2. Critical Model Loading Order**

```python
# models/__init__.py follows strict dependency hierarchy
# Base models (Many2one targets) loaded first:
from . import records_tag, records_location, records_department

# Core business models second:  
from . import records_box, records_document, pickup_request

# Compliance models third (depend on core):
from . import naid_audit_log, chain_of_custody

# Portal/UI models last (depend on all others):
from . import portal_request, customer_feedback
```

**Why This Matters**: Odoo 18.0 requires comodel targets to exist before One2many relationships are defined. Breaking this order causes KeyError exceptions during module loading.

### **3. Enterprise Model Template**

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

### **4. Intelligent Barcode Classification System**

```python
# Business Rules Implementation (records_box.py):
def auto_classify_barcode(self, barcode):
    """Auto-detect object type based on barcode length"""
    length = len(barcode.strip())
    
    if length == 5 or length == 15:    # Location barcodes
        return self._assign_to_location(barcode)
    elif length == 6:                   # Container boxes (file storage)
        return self._create_container_box(barcode)
    elif length == 7:                   # File folders (permanent)
        return self._create_permanent_folder(barcode)
    elif length == 10:                  # Shred bin items
        return self._assign_to_shred_bin(barcode)
    elif length == 14:                  # Temporary file folders (portal-created)
        return self._create_temp_folder(barcode)
```

**Integration Points**: This system drives location-based pricing, validates box placements, and enables bulk conversion wizards for operational efficiency.

---

## � **DISCONNECTED DEVELOPMENT WORKFLOW**

### **Critical Deployment Commands** (Always use these)

```bash
# ESSENTIAL: Git workflow for Odoo.sh deployment
git add .
git commit -m "Descriptive commit message"
git push origin main  # Triggers Odoo.sh rebuild

# Module validation (ALWAYS run before committing)
python development-tools/module_validation.py

# Comprehensive field validation (Before major changes)
python development-tools/comprehensive_field_analysis.py

# Check for missing fields/syntax errors
python development-tools/find_all_missing_fields.py

# Auto-sync with enterprise branch (Daily workflow)
./development-tools/auto_sync_main.sh
```

### **Deployment Workflow Process**

1. **Local Development**: Make changes in VS Code workspace
2. **Validation**: Run validation scripts to check syntax and dependencies
3. **Git Commit**: Commit changes with descriptive messages
4. **GitHub Push**: Push to trigger Odoo.sh rebuild
5. **Cloud Testing**: Test functionality in live Odoo.sh environment
6. **Iteration**: Repeat cycle for fixes/enhancements

⚠️ **IMPORTANT**: Since there's no local Odoo instance, all testing must happen after GitHub push when Odoo.sh rebuilds the database.

### **Pre-Commit Validation Checklist**

```bash
# MANDATORY validation before any commit
echo "🔍 Pre-commit validation checklist:"

# 1. Module syntax validation
python development-tools/module_validation.py
echo "✅ Module syntax validated"

# 2. Field dependency check
python development-tools/comprehensive_field_analysis.py
echo "✅ Field dependencies validated"

# 3. Missing field detection
python development-tools/find_all_missing_fields.py
echo "✅ Missing fields checked"

# 4. Git status check
git status
echo "✅ Git status reviewed"

# 5. Ready for commit
echo "🚀 Ready for GitHub push → Odoo.sh deployment"
```

### **Essential Development Tools** (No Odoo connection needed)

```bash
# Critical validation scripts (run locally)
python development-tools/module_validation.py
python development-tools/comprehensive_field_analysis.py
python development-tools/find_all_missing_fields.py
python development-tools/fix_all_missing_fields.py

# Git workflow for deployment
git add .
git commit -m "feat: Add missing compute methods for portal integration"
git push origin main  # Triggers Odoo.sh rebuild

# Session management (keep workspace alive)
./development-tools/keep_session_alive.sh

# Auto-sync and maintain workspace
./development-tools/auto_sync_main.sh
```

### **Comprehensive Debugging System** (Local validation only)

```bash
# Validate without live Odoo instance
./development-tools/comprehensive_debugging.sh validate

# Analyze potential installation errors
./development-tools/comprehensive_debugging.sh analyze

# Generate pre-deployment report
./development-tools/comprehensive_debugging.sh report

# Syntax and structure validation
./development-tools/comprehensive_debugging.sh syntax
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

### **2. Common Error Resolution Patterns**

#### **ParseError in Views**
- **Cause**: Missing fields in Python models
- **Solution**: Add fields following systematic patterns above
- **Validation**: Run field analysis scripts

#### **KeyError in Model Loading**
- **Cause**: Incorrect model loading order in `__init__.py`
- **Solution**: Load Many2one targets before One2many inverse models
- **Validation**: Check models/__init__.py dependency order

#### **Access Rights Errors**
- **Cause**: Missing entries in `security/ir.model.access.csv`
- **Solution**: Add both user and manager access rules
- **Pattern**: Follow existing access rule naming

#### **Import Errors**
- **Cause**: Missing dependencies or circular imports
- **Solution**: Check `__manifest__.py` dependencies
- **Validation**: Test module installation from scratch

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

1. **`development-tools/COMPREHENSIVE_REFERENCE.md`** - 481 lines documenting all models and fields
2. **`development-tools/SYSTEMATIC_FIELD_IMPLEMENTATION_COMPLETE.md`** - Field implementation patterns
3. **`README.md`** - 401 lines of setup and usage documentation
4. **`__manifest__.py`** - 154 lines defining module dependencies

### **Development Tools Directory**

```
development-tools/
├── comprehensive_debugging.sh      # Complete debugging toolchain
├── auto_sync_main.sh               # Automated Git workflow
├── keep_session_alive.sh          # VS Code session maintenance
├── systematic_view_fixer.sh       # Batch view file processing
├── find_all_missing_fields.py     # Field validation scripts
└── workspace-config/              # Session management and guides
```

---

## 🔍 **DEBUGGING & VALIDATION WORKFLOW**

### **Step-by-Step Pre-Deployment Process**

1. **Field Validation** (After any model changes)
   ```bash
   python development-tools/comprehensive_field_analysis.py
   ```

2. **Module Validation** (Check all Python and XML files)
   ```bash
   python development-tools/module_validation.py
   ```

3. **Missing Field Check** (Verify view-model consistency)
   ```bash
   python development-tools/find_all_missing_fields.py
   ```

4. **Git Deployment** (Push to trigger Odoo.sh rebuild)
   ```bash
   git add .
   git commit -m "Descriptive message"
   git push origin main
   ```

5. **Cloud Testing** (Test in live Odoo.sh environment after rebuild)

### **Systematic Error Resolution** (Local validation only)

The project uses a proven iterative debugging methodology:

1. **Error Identification**: Run comprehensive validation to capture issues
2. **Root Cause Analysis**: Use field analysis scripts to identify missing dependencies  
3. **Targeted Fixes**: Address specific errors (KeyError, ParseError, Access violations)
4. **Local Validation**: Verify fixes don't introduce regressions
5. **GitHub Deployment**: Push to trigger Odoo.sh rebuild and live testing

### **Available Debugging Tools** (No Odoo connection required)

```bash
# Complete validation suite (local only)
python development-tools/module_validation.py           # Full module validation
python development-tools/comprehensive_field_analysis.py # Field dependency check
python development-tools/find_all_missing_fields.py     # Missing field detection

# Session management  
./development-tools/keep_session_alive.sh               # Prevent timeouts
./development-tools/auto_sync_main.sh                   # Auto Git sync

# Deployment workflow
git add . && git commit -m "feat: Description" && git push origin main
```

---

## 🎯 **IMPLEMENTATION BEST PRACTICES**

### **1. Before Making Any Changes**

1. **Read architecture documentation** - Understand service boundaries and data flows
2. **Check current field coverage** - Run analysis scripts to identify gaps
3. **Understand model loading order** - Review `models/__init__.py` dependency hierarchy
4. **Validate barcode business rules** - Understand intelligent classification system

### **2. When Adding New Models**

1. **Follow enterprise template** - Use standard inheritance and field categories
2. **Respect loading order** - Add to correct position in `models/__init__.py`
3. **Implement security rules** - Add to `security/ir.model.access.csv`
4. **Add computed methods** - Follow `_compute_field_name` pattern
5. **Include action methods** - Follow `action_verb_object` pattern

### **3. When Modifying Existing Models**

1. **Preserve existing patterns** - Don't break established conventions
2. **Add fields systematically** - Group related fields together
3. **Update related views** - Ensure all fields are accessible via UI
4. **Test thoroughly** - Run comprehensive validation scripts
5. **Respect service boundaries** - Maintain separation between core/compliance/portal

### **4. Pre-Deployment Quality Assurance Checklist**

- [ ] All models inherit from `['mail.thread', 'mail.activity.mixin']`
- [ ] Core fields (name, company_id, user_id, active) present
- [ ] Security rules defined for user and manager groups
- [ ] Computed methods use `@api.depends` decorators
- [ ] Action methods follow naming conventions
- [ ] Model loading order respects dependencies
- [ ] Module validation script runs without errors
- [ ] Field analysis scripts complete successfully
- [ ] Changes committed with descriptive messages
- [ ] Ready for GitHub push → Odoo.sh deployment

---

## 🚀 **QUICK START FOR NEW CONTRIBUTORS**

### **Immediate Orientation Steps**

1. **Read the comprehensive reference**: `development-tools/COMPREHENSIVE_REFERENCE.md`
2. **Check current project status**: `development-tools/workspace-config/CURRENT_SESSION_STATUS.md`
3. **Run module validation**: `python development-tools/module_validation.py`
4. **Understand deployment workflow**: GitHub push → Odoo.sh rebuild → Cloud testing
5. **Review barcode classification**: Understand intelligent business rules in `records_box.py`

### **Common Task Patterns**

#### **Adding Missing Fields**
1. Identify missing fields from view files using analysis scripts
2. Group fields by service boundary (core/compliance/portal)
3. Add fields following enterprise template patterns
4. Update security access rules if needed
5. Validate with module validation scripts
6. Commit and push to GitHub for Odoo.sh deployment

#### **Creating New Workflows**
1. Start with enterprise model template
2. Determine correct service boundary (records/compliance/portal)
3. Add to proper position in model loading order
4. Implement state management with tracking
5. Create action methods for state transitions
6. Add comprehensive security rules
7. Validate locally then deploy via GitHub

#### **Debugging Field Issues**
1. Run `module_validation.py` to identify syntax problems
2. Check model inheritance patterns and loading order
3. Verify field naming conventions and relationships
4. Use comprehensive validation tools for error analysis
5. Fix issues locally, validate, then deploy to Odoo.sh

---

## 📚 **ESSENTIAL DOCUMENTATION REFERENCES**

- **Primary Architecture**: `development-tools/COMPREHENSIVE_REFERENCE.md` (481 lines)
- **Current Session Status**: `development-tools/workspace-config/CURRENT_SESSION_STATUS.md`
- **Setup Guide**: `records_management/README.md` (401 lines)
- **Development Workflow**: `development-tools/workspace-config/DEVELOPMENT.md`
- **Module Validation**: `development-tools/module_validation.py` (comprehensive syntax checker)

---

## ⚠️ **CRITICAL DEPLOYMENT REMINDERS**

### **GitHub → Odoo.sh Workflow**
- **NO Local Odoo**: This environment cannot run Odoo directly
- **Validation Only**: Use local scripts for syntax/structure validation
- **GitHub Triggers**: Every push to main branch triggers Odoo.sh rebuild
- **Cloud Testing**: All functional testing happens in Odoo.sh after deployment
- **Iteration Cycle**: Code → Validate → Commit → Push → Test in Cloud → Repeat

### **Best Practices for Disconnected Development**
1. **Validate Thoroughly**: Run all validation scripts before committing
2. **Descriptive Commits**: Use clear commit messages for easier debugging
3. **Small Iterations**: Make smaller, focused changes for easier testing
4. **Branch Strategy**: Use feature branches for complex changes
5. **Documentation**: Update documentation with each significant change

---

*This document represents the essential knowledge for productive AI agent work on this complex Odoo Records Management system in a disconnected development environment with GitHub-driven deployment to Odoo.sh.*
