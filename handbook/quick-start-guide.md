# Quick Start Guide - Records Management System

> Get up and running in **15 minutes**.

---
## 🚀 Prerequisites Checklist
- Odoo 18.0 Enterprise Edition installed
- PostgreSQL 12+ running
- 4GB+ RAM available
- Administrator access to Odoo

---
## ⚡ Fast Track Installation
### Step 1: Install Modules (≈3 min)
1. Go to Apps
2. Search "Records Management"
3. Click Install (auto-installs dependencies)
4. (Optional) Install "Records Management FSM" for field service/mobile features

### Step 2: Basic Configuration (≈5 min)
Navigate: Settings > Records Management
- ✓ Activate Records Management Features
- ✓ Auto-generate Barcodes
- ✓ Enable NAID Audit Logging

Company Settings:
- NAID Member ID: `RM-12345`
- Enable Records Management: ✓

### Step 3: Create First Customer (≈3 min)
Contacts > Create:
- Name: `Acme Corporation`
- ☑ Is a Company
- ☑ Customer
- ☑ Is a Records Management Customer

Add Department:
- Department Name: `Legal Department`

### Step 4: Set Up Portal User (≈2 min)
Add Contact under Acme Corporation:
- Name: `John Smith`
- Email: `john@acme.com`
- Job Title: `Records Administrator`

Grant Portal Access:
- Actions > Grant Portal Access
- Assign Groups: ☑ Portal Customer Company Admin

### Step 5: Test the System (≈2 min)
Create a Container:
- Records Management > Containers > Create
  - Customer: Acme Corporation
  - Department: Legal Department
  - Container Type: Bankers Box
  - Location: A1-001

Upload a Document:
- Documents > Create
  - Title: Contract File
  - Container: (select container above)
  - Document Type: Legal

---
## 🎯 Essential First Steps After Installation
### Configure Locations
Records Management > Configuration > Locations
- Hierarchy: Warehouse A > Section A1 > Spot A1-001

### Set Up Container Types
Configuration > Container Types:
- Bankers Box (15"x12"x10")
- Legal Box (15"x24"x10")
- Digital Media Box

### Create Document Types
Configuration > Document Types:
- Legal Documents
- Financial Records
- Medical Records
- Business Documents

---
## 👨‍💼 Portal User Quick Test
1. Open incognito/private browser
2. Go to portal URL
3. Login with `john@acme.com`
4. Navigate to Records Management section
5. Test:
   - Browse inventory
   - Submit pickup request
   - Upload documents
   - Generate barcode labels

---
## ⚙️ Essential Settings (Configurator)
RM Module Configurator:
- Enable Advanced Search: **True**
- Auto-assign Storage Location: **True**
- Enable Container Weight Tracking: **True**
- Require Dual Authorization: **True** (for compliance)

### Configure Billing (Optional)
Billing > Billing Configuration:
- Base storage rate: `$2.50 / month`
- Billing cycle: `Monthly`
- Auto-invoicing: **Enabled**

---
## 🔧 Quick Troubleshooting
| Problem | Check |
|---------|-------|
| Portal user can't see containers | User groups (Portal Customer Company Admin); contact linked as child of company |
| Barcodes not generating | Settings > Technical > Sequences; auto-generation enabled |
| Module installation fails | Dependencies installed; restart Odoo; inspect server logs |

---
## 📱 Mobile Access
1. Install **Records Management FSM** (Apps > Search)
2. Configure: FSM > Configuration > Mobile Settings

---
## 🎓 Next Steps
| Goal | Resource |
|------|----------|
| Full Reference | `RECORDS_MANAGEMENT_HANDBOOK.md` |
| Admin Training | TRAINING_ADMIN.md |
| User Training | TRAINING_USER.md |
| Portal Training | TRAINING_PORTAL.md |

### Suggested Sequence
1. Complete this Quick Start
2. Review full handbook
3. Configure advanced workflows
4. Integrate external systems
5. Plan go-live & training

---
## 📞 Need Help?
- Documentation: Full handbook in repository root
- Community: GitHub issues/discussions
- Support: Internal support channel / email
- Training: Schedule implementation assistance

---
🎉 **Congratulations!** Your Records Management System is ready. Continue with the User Guide or Admin Guide for deeper operations and configuration.
