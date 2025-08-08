# Records Management Development Tools

## 📁 Directory Structure

This directory contains organized development tools, utilities, and documentation for the Records Management System.

### 🐍 **scripts/**
Python development and validation scripts:
- **Field Analysis**: `comprehensive_field_analysis.py`, `find_all_missing_fields.py`
- **Module Validation**: `module_validation.py`, `comprehensive_validation.py` 
- **Syntax Fixers**: `advanced_syntax_fixer.py`, `comprehensive_syntax_fixer.py`
- **Field Completion**: `comprehensive_field_completion.py`, `systematic_field_completion.py`
- **Action Method Tools**: `action_method_validator.py`, `batch_action_method_generator.py`

### 🛠️ **utilities/**
Shell scripts and automation utilities:
- **Session Management**: `keep_session_alive.sh`, `auto_sync_main.sh`
- **Build Tools**: `comprehensive_debugging.sh`, `systematic_view_fixer.sh`
- **Git Automation**: `sync_enterprise_branch.sh`
- **Installation**: `install_extensions.sh`

### 📚 **documentation/**
Project documentation and reports:
- **User Guides**: `USER_MANUAL.md`, `QUICKSTART.md`, `FEATURES.md`
- **Technical Docs**: `COMPREHENSIVE_REFERENCE.md`, `DEVELOPMENT.md`
- **Progress Reports**: Session progress and completion reports
- **Analysis Results**: Field analysis and validation outputs

### ⚙️ **config/**
Configuration files and logs:
- **Odoo Configs**: `odoo.conf`, `odoo_debug.conf`
- **Session Logs**: `session_keepalive.log`
- **Requirements**: `requirements.txt`

### 📊 **analysis-reports/**
JSON analysis reports and audit results:
- **Field Analysis**: Comprehensive field analysis results
- **Module Audits**: Model and relationship audit reports
- **Validation Reports**: Syntax and structure validation results

### 🗄️ **backups/**
Backup files and version history:
- Model file backups
- Configuration backups
- Session state backups

### 🔧 **current-tools/**
Active development tools and current session utilities

### 📖 **docs/**
Additional documentation and guides

### 📡 **monitoring-system/**
System monitoring and health check tools

### 🔧 **syntax_fixers/**
Specialized syntax fixing utilities

## 🚀 Quick Start

### Essential Validation Commands:
```bash
# Complete module validation
python scripts/module_validation.py

# Field analysis and gap detection
python scripts/comprehensive_field_analysis.py

# Find missing fields in views
python scripts/find_all_missing_fields.py

# Syntax validation and fixing
python scripts/comprehensive_syntax_fixer.py
```

### Development Workflow:
```bash
# Keep session alive during development
utilities/keep_session_alive.sh

# Auto-sync with git during development
utilities/auto_sync_main.sh

# Complete debugging suite
utilities/comprehensive_debugging.sh
```

## 📋 Recent Achievements

### ✅ **Customer Shred Bin Management System**
- Complete customer shred bin model with field service operations
- Color-coded dual-view system (internal operations + customer portal)
- Business-specific bin sizing with actual company item codes (23, 3B, 3C, 64, 96)
- Automated upsize/downsize/additional bin request workflows
- Multi-tenant customer portal with department filtering

### ✅ **Portal Customer Actions**
- **action_request_upsize**: Smart bin size upgrade requests
- **action_request_downsize**: Bin size reduction requests  
- **action_request_additional_bins**: Additional capacity for 96-gallon customers
- **action_customer_mark_full**: Collection request workflow

### ✅ **Business Logic Integration**
- Intelligent size hierarchy with business rules
- Automated pickup request generation
- Service billing integration
- Customer notification system

## 🎯 Usage Guidelines

1. **Before Making Changes**: Run module validation scripts
2. **Field Updates**: Use comprehensive field analysis tools  
3. **Syntax Issues**: Use targeted syntax fixers
4. **Session Management**: Use session alive scripts for long development sessions
5. **Documentation**: Update relevant documentation after changes

## 🔄 Development Workflow

1. **Validate**: `python scripts/module_validation.py`
2. **Develop**: Make changes to models/views
3. **Fix**: Use syntax fixers if needed
4. **Test**: Run comprehensive validation
5. **Deploy**: Push to GitHub → Triggers Odoo.sh rebuild
6. **Monitor**: Use monitoring tools for live system health

---

*This organized structure supports efficient development and maintenance of the Records Management System.*
