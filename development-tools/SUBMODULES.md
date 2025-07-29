# Adding External Modules to Records Management

## ✅ **SOLVED: Submodule Build Error**

The error "Could not determine the revision of the submodule addons/server_tools" has been fixed by cleaning the `.gitmodules` file.

## 🚀 **How to Add External Modules (When Needed)**

### Option 1: Via Odoo.sh Dashboard (Recommended)
1. Go to your Odoo.sh project
2. Navigate to **Settings** → **Submodules**  
3. Click **Add Submodule**
4. Enter details:
   - **URL**: `https://github.com/OCA/queue.git`
   - **Branch**: `18.0`
   - **Path**: `addons/queue_job`
5. **Deploy** → Module auto-installs

### Option 2: Via Git Commands (Advanced)
```bash
# Add submodule
git submodule add -b 18.0 https://github.com/OCA/queue.git addons/queue_job

# Commit changes
git add .gitmodules addons/queue_job
git commit -m "Add queue_job submodule for async processing"

# Push to trigger Odoo.sh rebuild
git push origin Enterprise-Grade-DMS-Module-Records-Management
```

## 📋 **Recommended External Modules**

### For Enhanced Records Management:
- **queue_job** - Async baling and invoicing
- **server_tools** - Additional utilities
- **document** - Document management integration
- **stock_lot_scrap** - Enhanced inventory features

### Installation Order:
1. Start with **core dependencies** (already in manifest)
2. Add **one external module at a time**
3. Test thoroughly before adding more
4. Keep branch lean and focused

## 🎯 **Current Status: Clean & Ready**

Your branch is now optimized for:
- ✅ Fast Odoo.sh builds
- ✅ No submodule conflicts  
- ✅ Dynamic module addition
- ✅ Production-ready deployment
