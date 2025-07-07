#!/usr/bin/env python3
"""
Script to create test data for Records Management Customer Portal
Run this script in Odoo shell to create test customers, departments, and users
"""

import logging

def create_portal_test_data(env):
    """Create comprehensive test data for portal testing"""
    
    # Create test customer company (City of El Paso)
    customer_company = env['res.partner'].create({
        'name': 'City of El Paso',
        'is_company': True,
        'customer_rank': 1,
        'email': 'admin@elpaso.gov',
        'phone': '+1-915-555-0100',
        'street': '300 N Campbell St',
        'city': 'El Paso',
        'state_id': env.ref('base.state_us_48').id,  # Texas
        'zip': '79901',
        'country_id': env.ref('base.us').id,
    })
    
    # Create company admin user
    company_admin = env['res.partner'].create({
        'name': 'Maria Rodriguez',
        'parent_id': customer_company.id,
        'is_company': False,
        'email': 'maria.rodriguez@elpaso.gov',
        'phone': '+1-915-555-0101',
        'function': 'Records Management Director',
        'customer_rank': 1,
    })
    
    # Create departments
    police_dept = env['records.department'].create({
        'name': 'Police Department',
        'code': 'POLICE',
        'company_id': customer_company.id,
        'admin_id': company_admin.id,
    })
    
    fire_dept = env['records.department'].create({
        'name': 'Fire Department', 
        'code': 'FIRE',
        'company_id': customer_company.id,
    })
    
    hr_dept = env['records.department'].create({
        'name': 'Human Resources',
        'code': 'HR', 
        'company_id': customer_company.id,
    })
    
    # Create department admin for Police Department
    police_admin = env['res.partner'].create({
        'name': 'John Smith',
        'parent_id': customer_company.id,
        'is_company': False,
        'email': 'john.smith@elpaso.gov',
        'phone': '+1-915-555-0102',
        'function': 'Police Records Manager',
        'customer_rank': 1,
    })
    
    # Update police department with admin
    police_dept.admin_id = police_admin.id
    
    # Create department users with different access levels
    
    # Police Department Users
    env['records.department.user'].create({
        'department_id': police_dept.id,
        'user_id': police_admin.id,
        'access_level': 'department_admin',
    })
    
    # Police officer (regular user)
    police_user = env['res.partner'].create({
        'name': 'Officer Jane Doe',
        'parent_id': customer_company.id,
        'is_company': False,
        'email': 'jane.doe@elpaso.gov',
        'phone': '+1-915-555-0103',
        'function': 'Police Officer',
        'customer_rank': 1,
    })
    
    env['records.department.user'].create({
        'department_id': police_dept.id,
        'user_id': police_user.id,
        'access_level': 'user',
    })
    
    # Police clerk (viewer only)
    police_viewer = env['res.partner'].create({
        'name': 'Robert Wilson',
        'parent_id': customer_company.id,
        'is_company': False,
        'email': 'robert.wilson@elpaso.gov',
        'phone': '+1-915-555-0104',
        'function': 'Police Clerk',
        'customer_rank': 1,
    })
    
    env['records.department.user'].create({
        'department_id': police_dept.id,
        'user_id': police_viewer.id,
        'access_level': 'viewer',
    })
    
    # Create some test locations
    warehouse_location = env['records.location'].create({
        'name': 'Main Warehouse - A1',
        'code': 'WH-A1',
        'location_type': 'warehouse',
        'capacity': 1000,
    })
    
    # Create test boxes with customer/department assignments
    test_boxes = []
    for i in range(1, 6):
        box = env['records.box'].create({
            'name': f'POLICE-BOX-{i:03d}',
            'customer_id': customer_company.id,
            'department_id': police_dept.id,
            'location_id': warehouse_location.id,
            'capacity': 100,
            'state': 'active',
        })
        test_boxes.append(box)
    
    # Create test documents
    document_type = env['records.document.type'].create({
        'name': 'Police Report',
        'code': 'POLICE_RPT',
    })
    
    for i, box in enumerate(test_boxes[:3]):  # Add docs to first 3 boxes
        for j in range(1, 6):  # 5 documents per box
            env['records.document'].create({
                'name': f'Police Report {i+1}-{j:02d}',
                'box_id': box.id,
                'customer_id': customer_company.id,
                'department_id': police_dept.id,
                'document_type_id': document_type.id,
                'state': 'stored',
                'description': f'Test police report document {i+1}-{j:02d}',
            })
    
    # Create a service request
    env['records.service.request'].create({
        'name': 'Pickup Request - New Evidence Files',
        'customer_id': customer_company.id,
        'department_id': police_dept.id,
        'requested_by': police_admin.id,
        'service_type': 'pickup',
        'priority': 'normal',
        'description': 'Need pickup of 5 new evidence file boxes',
        'estimated_cost': 150.0,
    })
    
    print("✅ Test data created successfully!")
    print("\n🏢 Customer Company:")
    print(f"   - {customer_company.name} (ID: {customer_company.id})")
    print(f"   - Company Admin: {company_admin.name} ({company_admin.email})")
    
    print("\n🏛️ Departments:")
    print(f"   - {police_dept.name} (Admin: {police_admin.name})")
    print(f"   - {fire_dept.name}")
    print(f"   - {hr_dept.name}")
    
    print("\n👥 Test Users:")
    print(f"   - Department Admin: {police_admin.name} ({police_admin.email})")
    print(f"   - Regular User: {police_user.name} ({police_user.email})")
    print(f"   - Viewer: {police_viewer.name} ({police_viewer.email})")
    
    print(f"\n📦 Created {len(test_boxes)} test boxes with documents")
    print("🎯 Ready to test the portal!")
    
    return {
        'customer_company': customer_company,
        'company_admin': company_admin,
        'police_dept': police_dept,
        'police_admin': police_admin,
        'police_user': police_user,
        'police_viewer': police_viewer,
    }

# Instructions for running this script:
print("""
🚀 TO CREATE TEST DATA:

1. Access Odoo shell:
   python3 odoo-bin shell -d your_database --addons-path=addons,records_management

2. Run this script:
   exec(open('create_portal_test_data.py').read())
   test_data = create_portal_test_data(env)

3. Create portal users (in Odoo shell):
   # Enable portal access for test users
   portal_group = env.ref('base.group_portal')
   
   for user_partner in [test_data['company_admin'], test_data['police_admin'], 
                        test_data['police_user'], test_data['police_viewer']]:
       # Create user account for portal access
       user = env['res.users'].create({
           'name': user_partner.name,
           'login': user_partner.email,
           'email': user_partner.email,
           'partner_id': user_partner.id,
           'groups_id': [(6, 0, [portal_group.id])],
       })
       print(f"Created portal user: {user.login}")

4. Access portal at: http://your-odoo-url/my/records
""")
