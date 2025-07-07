# Manual Steps to Test Customer Portal

## Option 1: Quick Manual Setup (Recommended)

### Step 1: Create Test Customer Company
1. Go to **Contacts** app
2. Click **Create** 
3. Fill in:
   - **Name**: City of El Paso
   - **Is a Company**: ✓ (checked)
   - **Email**: admin@elpaso.gov
   - **Phone**: +1-915-555-0100
4. Click **Save**

### Step 2: Create Company Admin User
1. Go to **Contacts** app
2. Click **Create**
3. Fill in:
   - **Name**: Maria Rodriguez  
   - **Company**: City of El Paso (select from dropdown)
   - **Email**: maria.rodriguez@elpaso.gov
   - **Job Position**: Records Management Director
4. Click **Save**

### Step 3: Create Portal User Account
1. Go to **Settings** > **Users & Companies** > **Users**
2. Click **Create**
3. Fill in:
   - **Name**: Maria Rodriguez
   - **Email**: maria.rodriguez@elpaso.gov  
   - **Login**: maria.rodriguez@elpaso.gov
4. In **Access Rights** tab:
   - **Groups**: Select "Portal" (uncheck Internal User if selected)
5. Click **Save**

### Step 4: Create Department and Assign User  
1. Go to **Records Management** app
2. Navigate to **Configuration** > **Departments** (or find the Departments menu)
3. Click **Create**
4. Fill in:
   - **Department Name**: Police Department
   - **Department Code**: POLICE
   - **Company**: City of El Paso
   - **Department Admin**: Maria Rodriguez
5. Click **Save**

### Step 5: Create Test Boxes and Documents
1. Go to **Records Management** > **Boxes**
2. Click **Create** and add several boxes:
   - **Customer**: City of El Paso
   - **Department**: Police Department
   - **Location**: (select any available location)
   - **State**: Active
3. For each box, create some test documents

### Step 6: Access the Portal
1. **Logout** from your admin account
2. Go to your Odoo login page
3. Login with: `maria.rodriguez@elpaso.gov` (password set during user creation)
4. Navigate to: `/my/records` or `/my/inventory`

## Option 2: Automated Setup (Using Script)

### Prerequisites
- SSH/terminal access to your Odoo server
- Odoo shell access

### Steps
1. Copy the `create_portal_test_data.py` script to your server
2. Run Odoo shell:
   ```bash
   python3 odoo-bin shell -d your_database_name --addons-path=addons,records_management
   ```
3. In the shell, run:
   ```python
   exec(open('create_portal_test_data.py').read())
   test_data = create_portal_test_data(env)
   
   # Create portal users
   portal_group = env.ref('base.group_portal')
   
   for user_partner in [test_data['company_admin'], test_data['police_admin'], 
                        test_data['police_user'], test_data['police_viewer']]:
       user = env['res.users'].create({
           'name': user_partner.name,
           'login': user_partner.email,
           'email': user_partner.email,
           'partner_id': user_partner.id,
           'groups_id': [(6, 0, [portal_group.id])],
       })
       print(f"Created portal user: {user.login}")
   
   env.cr.commit()
   ```

## Portal URLs to Test

Once logged in as a portal user, visit these URLs:

- **Main Portal**: `/my`
- **Records Dashboard**: `/my/records` 
- **Inventory View**: `/my/inventory`
- **Service Requests**: `/my/records/services/new`
- **User Management**: `/my/records/users/bulk_import` (admin only)

## Different Access Levels to Test

Create users with different access levels:

1. **Company Admin** (maria.rodriguez@elpaso.gov)
   - Can see all departments and billing
   - Can approve deletions
   - Can manage all users

2. **Department Admin** (john.smith@elpaso.gov)  
   - Can see department inventory and billing
   - Can approve department deletions
   - Can invite department users

3. **Regular User** (jane.doe@elpaso.gov)
   - Can add boxes/documents
   - Can request services
   - Can request deletions (needs approval)

4. **Viewer** (robert.wilson@elpaso.gov)
   - Can only view inventory
   - Can request services
   - Cannot add or delete

## Expected Portal Features

✅ **Dashboard**: Shows inventory summary, recent activity  
✅ **Inventory**: List of boxes and documents with filtering  
✅ **Service Requests**: Form to request pickup, delivery, shredding  
✅ **Billing**: Department costs (based on access level)  
✅ **User Management**: Invite users, set access levels  
✅ **Approvals**: Deletion request workflow  

## Troubleshooting

- **Cannot access portal**: Check user has Portal group, not Internal User
- **No data visible**: Ensure customer_id and department_id are set on boxes/documents  
- **Permission denied**: Check user's department assignment and access level
- **Portal not loading**: Check that records_management module is properly installed
