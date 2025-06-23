import xmlrpc.client

# Define the OpenERP server connection details
url = "http://localhost:8069"
db = "my_database"  # Replace with your database name
username = "admin"  # Replace with your username
password = "admin"  # Replace with your password

# Authenticate with the OpenERP server
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
if uid:
    print(f"Successfully authenticated. User ID: {uid}")
else:
    print("Authentication failed.")
