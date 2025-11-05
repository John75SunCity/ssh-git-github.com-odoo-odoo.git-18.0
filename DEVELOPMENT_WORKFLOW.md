# Development & Deployment Workflow

## 🎯 Branch Strategy

### Current Setup:
- **`Enterprise-Grade-DMS-Module-Records-Management`** - Your active development branch (work here!)
- **`main`** - Staging/Development branch (monitored by Odoo.sh for auto-deployment)
- **`main_18.0`** - Production branch (not currently active)

### Workflow Philosophy:
✅ **Safe development** - Work freely on Enterprise branch without affecting Odoo.sh  
✅ **Easy recovery** - `main` stays stable as your safety net  
✅ **Controlled deployment** - Only sync to `main` when ready to deploy to Odoo.sh staging

---

## 📋 Daily Development Workflow

### 1️⃣ **Do Your Work** (on Enterprise branch)
```bash
# Make sure you're on the right branch
git branch --show-current
# Should show: Enterprise-Grade-DMS-Module-Records-Management

# Make your changes, then commit
git add .
git commit -m "feat: Your feature description"
git push origin Enterprise-Grade-DMS-Module-Records-Management
```

### 2️⃣ **Test Locally** (optional)
```bash
# Run validation
python3 development-tools/comprehensive_validator.py

# Or use VS Code task: "Validate Records Management Module"
```

### 3️⃣ **Deploy to Staging** (Odoo.sh)
When you're ready to test on Odoo.sh staging:

**Option A - Use VS Code Task (Recommended):**
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Tasks: Run Task"
3. Select "🚀 Deploy to Staging (Sync Enterprise → main)"
4. Enter a commit message when prompted

**Option B - Use Command Line:**
```bash
./scripts/sync-to-staging.sh "Your deployment message"
```

**Option C - Manual Sync:**
```bash
git checkout main
git pull origin main
git merge Enterprise-Grade-DMS-Module-Records-Management --no-ff -m "sync: Deploy to staging"
git push origin main
git checkout Enterprise-Grade-DMS-Module-Records-Management
```

---

## 🔄 What Happens During Sync

The sync script will:
1. ✅ Check you have no uncommitted changes
2. 📊 Show what commits will be synced
3. ❓ Ask for confirmation
4. 🔄 Merge Enterprise → main
5. 🚀 Push to trigger Odoo.sh deployment
6. 🏠 Return you to Enterprise branch

---

## 🆘 Recovery Scenarios

### "I messed up Enterprise branch and need to recover!"
```bash
# Reset Enterprise to match main (your safety net)
git checkout Enterprise-Grade-DMS-Module-Records-Management
git reset --hard origin/main
git push origin Enterprise-Grade-DMS-Module-Records-Management --force
```

### "I want to undo the last commit on Enterprise"
```bash
git checkout Enterprise-Grade-DMS-Module-Records-Management
git reset --soft HEAD~1  # Keeps changes, undoes commit
# or
git reset --hard HEAD~1  # Removes changes completely
```

### "Odoo.sh deployment failed, need to rollback"
```bash
# Find a good commit from main's history
git log main --oneline -10

# Reset main to that commit
git checkout main
git reset --hard <commit-hash>
git push origin main --force
git checkout Enterprise-Grade-DMS-Module-Records-Management
```

---

## 📌 Key Rules

✅ **DO:**
- Work on `Enterprise-Grade-DMS-Module-Records-Management` branch
- Commit and push frequently to Enterprise branch
- Sync to `main` only when ready to deploy/test on Odoo.sh
- Use the sync script for safety

❌ **DON'T:**
- Work directly on `main` branch
- Force push to `main` unless recovering from emergency
- Forget to commit before syncing

---

## 🚀 Quick Command Reference

```bash
# Check current branch
git branch --show-current

# See what's different between Enterprise and main
git log main..Enterprise-Grade-DMS-Module-Records-Management --oneline

# Deploy to staging (triggers Odoo.sh)
./scripts/sync-to-staging.sh "deployment message"

# Check deployment status
# Visit: https://odoo.sh

# Return to Enterprise branch (if on main)
git checkout Enterprise-Grade-DMS-Module-Records-Management
```

---

## 📚 Additional Notes

- **`main_18.0`** branch is for future production use - don't sync there yet
- Odoo.sh monitors **`main`** branch for auto-deployment to development/staging
- Your Enterprise branch is your playground - experiment safely!
- The `main` branch acts as your stable checkpoint

---

**Last Updated:** November 5, 2025  
**Workflow Status:** Development & Staging Only (Production not active)
