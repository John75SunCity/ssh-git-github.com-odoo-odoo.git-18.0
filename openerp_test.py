import xmlrpc.client

# Configuration
url = "http://localhost:8069"
db = "my_database"  # Replace with your database name
username = "admin"  # Replace with your username
password = "admin"  # Replace with your password

# Authenticate
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"Authenticated to Odoo as {username} (uid: {uid})")
    # Example: search for partners
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    partners = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_read',
        [[]], {'fields': ['name'], 'limit': 5}
    )
    print("First 5 partners:", partners)
else:
    print("Failed to authenticate to Odoo. Check your credentials.")
