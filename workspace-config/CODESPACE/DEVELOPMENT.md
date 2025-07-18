# Records Management - Development Setup
# Minimal guide for fast development without bloated files

## Option 1: Odoo.sh Development (Recommended)
1. Push your branch to GitHub
2. Odoo.sh auto-builds with dependencies
3. Access via Odoo.sh dashboard
4. No local setup needed!

## Option 2: GitHub Codespaces (Cloud Development)
1. Open repository in GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. Auto-configures from .devcontainer/devcontainer.json
4. Instant Odoo 18.0 environment

## Option 3: Local Development (Minimal)
```bash
# Clone your branch
git clone -b Enterprise-Grade-DMS-Module-Records-Management https://github.com/John75SunCity/odoo.git

# Install Python dependencies
pip install -r requirements.txt

# Run with Odoo 18.0 (install Odoo separately)
odoo -d test_db -i records_management --addons-path=.
```

## Dynamic Module Loading
- Core dependencies auto-install in Odoo.sh
- Optional modules: Enable in Odoo Apps as needed
- No need to include heavy files in branch

## Fast Development Tips
1. Edit files directly in Codespaces/Odoo.sh
2. Use `-u records_management` for quick module updates
3. Git push triggers automatic Odoo.sh rebuild
4. Keep branch focused on your module only
