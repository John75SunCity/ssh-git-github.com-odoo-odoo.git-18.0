# 🚀 How to Test the Customer Portal in Your Odoo Instance

## Quick Start (5 minutes)

### 1. Create a Test Customer Company
```
Go to: Contacts app
Click: Create
Fill:
- Name: City of El Paso  
- ☑️ Is a Company
- Email: admin@elpaso.gov
Save
```

### 2. Create Portal User
```
Go to: Settings > Users & Companies > Users
Click: Create  
Fill:
- Name: Test Admin
- Email: test.admin@elpaso.gov
- Login: test.admin@elpaso.gov
Access Rights tab:
- Groups: ☑️ Portal (uncheck Internal User)
Save & Set Password
```

### 3. Create Department & Link User
```
Go to: Records Management app
Navigate to: Configuration > Customer Inventory or Departments menu
Click: Create
Fill:
- Department Name: Police Department
- Company: City of El Paso  
- Department Admin: (create contact with test.admin@elpaso.gov email)
Save
```

### 4. Create Test Inventory
```
Go to: Records Management > Boxes
Click: Create (create 2-3 boxes)
Fill each box:
- Customer: City of El Paso
- Department: Police Department  
- Location: (any available)
- State: Active
Save each box

For each box, create 2-3 documents:
Go to: Records Management > Documents  
Click: Create
Fill:
- Document Reference: Test Doc 001
- Box: (select the box you created)
- Customer & Department: (should auto-fill)
Save
```

## 🌐 Access the Portal

### Method 1: Direct Login
1. **Logout** from your admin account
2. Go to your Odoo login page  
3. Login with: `test.admin@elpaso.gov`
4. Navigate to these URLs:

```
Main Portal:           https://your-odoo-url/my
Records Dashboard:     https://your-odoo-url/my/records  
Inventory View:        https://your-odoo-url/my/inventory
Service Requests:      https://your-odoo-url/my/records/services/new
```

### Method 2: Portal Menu
1. After login, look for "My Account" or portal menu
2. Should see "Records" or "Inventory" sections

## 📋 What You Should See

### Dashboard (`/my/records`)
- Summary cards showing box count, document count
- Recent activity list  
- Quick action buttons
- Access level indicator

### Inventory (`/my/inventory`) 
- List of your boxes with details
- Search and filter options
- Document counts per box
- Department filtering (if multiple departments)

### Service Requests (`/my/records/services/new`)
- Form to request:
  - 📦 Pickup (new files)
  - 📤 Return (checked out boxes)  
  - 🚚 Delivery (file box delivery)
  - 🗑️ Shredding services
  - 📁 Storage services

## 🔧 Troubleshooting

### "Portal not found" or 404 errors
```bash
# Check if portal templates are properly loaded
Go to: Settings > Technical > Views
Search: "portal_my_inventory"
Should see the template listed
```

### "No inventory data visible"
```sql
-- Check if customer_id is set on boxes (run in database)
SELECT name, customer_id, department_id FROM records_box LIMIT 10;

-- If NULL, update manually:
UPDATE records_box SET customer_id = (SELECT id FROM res_partner WHERE name = 'City of El Paso' LIMIT 1);
```

### "Access denied" errors
```
Go to: Settings > Users & Companies > Users
Find your test user
Check:
- Groups: Should have "Portal" group
- Partner: Should be linked to correct contact
- Active: Should be checked
```

### Portal shows but no records visible
1. Ensure boxes have `customer_id` and `department_id` set
2. Check that portal user's contact is linked to the department
3. Verify department user record exists:
   ```
   Go to: Records Management > Configuration > Department Users
   Should see entry linking your user to department
   ```

## 🎯 Test Different Access Levels

Create multiple users to test different permission levels:

### Company Admin
- Email: `company.admin@elpaso.gov`
- Can see: All departments, full billing, all users
- Can do: Approve deletions, manage all users

### Department Admin  
- Email: `dept.admin@elpaso.gov`
- Can see: Department inventory, department billing
- Can do: Invite users, approve department deletions

### Regular User
- Email: `regular.user@elpaso.gov`  
- Can see: Department inventory
- Can do: Add boxes, request services, request deletions

### Viewer Only
- Email: `viewer@elpaso.gov`
- Can see: Department inventory (read-only)
- Can do: Request services only

## 🔍 Portal URLs Reference

| URL | Description | Access Level |
|-----|-------------|--------------|
| `/my` | Main portal home | All |  
| `/my/records` | Records dashboard | All |
| `/my/inventory` | Inventory listing | All |
| `/my/records/services/new` | New service request | All |
| `/my/records/users/bulk_import` | User management | Admin only |

## 📱 Expected Mobile Experience

The portal should be responsive and work on mobile devices with:
- Touch-friendly buttons
- Responsive tables  
- Mobile-optimized forms
- Collapsible sections

---

🎉 **Success Indicators:**
- ✅ Portal loads without errors
- ✅ Inventory data displays correctly  
- ✅ Service request forms work
- ✅ Access levels respected
- ✅ Responsive design on mobile
