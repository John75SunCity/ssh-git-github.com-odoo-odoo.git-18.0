# Deployment Workflow - Records Management Module

## 🚀 Established Deployment Strategy (Option A)

### **Primary Deployment Method: VS Code Source Control**

For all pushes that need to trigger **Odoo.sh database rebuilds**:

1. **Use VS Code Source Control Panel** (`Ctrl+Shift+G`)
2. **Stage changes** → **Commit with clear message** → **Push**
3. **Verify Odoo.sh rebuild** is triggered automatically

### **GitLens Usage: Visualization & Code Analysis**

GitLens is configured for development enhancement, NOT deployment:

- ✅ **Code lens and blame information**
- ✅ **Git history and branch visualization**
- ✅ **Commit exploration and diff analysis**
- ✅ **Repository insights and contributor stats**
- ❌ **NOT for deployment pushes** (may not trigger Odoo.sh rebuilds)

## 🔧 Configuration Summary

### **Removed AI Extensions:**

- ❌ Codeium (uninstalled)
- ❌ Tabnine (uninstalled)  
- ❌ Jupyter (uninstalled)
- ❌ Continue.dev (uninstalled)
- ❌ All AI API keys removed from settings

### **Retained Core Extensions:**

- ✅ GitHub Copilot (AI assistance for coding)
- ✅ GitLens (Git visualization and history)
- ✅ Python development stack
- ✅ Odoo-specific extensions
- ✅ Web development tools

## 📋 Deployment Checklist

### **Before Every Deployment:**

1. **Validate locally**: Run `python development-tools/module_validation.py`
2. **Check field consistency**: Run `python development-tools/comprehensive_field_analysis.py`
3. **Stage in Source Control**: Use VS Code Source Control panel
4. **Write descriptive commit**: Clear, actionable commit messages
5. **Push via Source Control**: Triggers Odoo.sh rebuild automatically

### **Critical Files for Odoo.sh Monitoring:**

- `records_management/__manifest__.py` (version changes)
- `records_management/models/*.py` (model changes)
- `records_management/views/*.xml` (view changes)
- `records_management/security/*.csv` (access changes)

## 🎯 Git Workflow Commands

```bash
# Pre-deployment validation (always run these)
python development-tools/module_validation.py
python development-tools/comprehensive_field_analysis.py

# Use VS Code Source Control Panel for deployment
# OR if using terminal (ensure it triggers Odoo.sh):
export PATH="/usr/bin:$PATH"
git add .
git commit -m "feat: Descriptive commit message"
git push origin main  # THIS triggers Odoo.sh rebuild
```

## ✅ Current Status

- **Deployment Method**: ✅ VS Code Source Control (confirmed Odoo.sh trigger)
- **GitLens Role**: ✅ Development visualization only
- **AI Extensions**: ✅ Cleaned up, only Copilot retained
- **Validation Tools**: ✅ All scripts operational for pre-deployment checks

---

**Last Updated**: August 2, 2025  
**Status**: Production-ready workflow established
