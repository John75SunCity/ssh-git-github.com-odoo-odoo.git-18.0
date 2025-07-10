# Installation Instructions for Records Management Module

## ⚠️ CRITICAL: Prerequisites - Install Required Modules First

**MANDATORY INSTALLATION ORDER:**

### Step 1: Install Stock/Inventory Module (REQUIRED)
1. **Go to Apps** in your Odoo.sh instance
2. **Search "Inventory"** 
3. **Install "Inventory" module**
4. **Wait for installation to complete** ✅
5. **Verify** it shows as "Installed"

### Step 2: Install Records Management Module
1. **Go to Apps → Update Apps List** (refresh module registry)
2. **Search "Records Management"**
3. **Click "Activate"**

## ❌ Common Error

If you see this error:
```
TypeError: Model 'stock.production.lot' does not exist in registry
```

**Solution:** You skipped Step 1. Install the Inventory module first!

## 🔧 Auto-Installation Option

For advanced users, you can try installing dependencies automatically:
1. Install Records Management module
2. If it fails, go to Apps → More → Technical → Automated Actions
3. Look for Records Management dependency installer

## ✅ Verification

After successful installation, you should have access to:
- Records Management menu in main navigation
- Stock lot management with customer relationships
- Pickup request functionality
- Shredding service features

## 🆘 Troubleshooting

**Problem:** "stock.production.lot does not exist"
**Solution:** Install Inventory module first

**Problem:** "Module not found"
**Solution:** Go to Apps → Update Apps List

**Problem:** Installation fails
**Solution:** Check that all dependencies are installed:
- base ✅ (always installed)
- stock ✅ (install manually)
- web ✅ (always installed)
- mail ✅ (usually installed)
- portal ✅ (install if needed)
- product ✅ (install if needed)
- contacts ✅ (usually installed)
