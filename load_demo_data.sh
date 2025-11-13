#!/bin/bash
# Script to manually load demo data into existing Records Management installation

echo "🔄 Loading Records Management Demo Data..."

# Replace with your database name
DB_NAME="your_database_name"

# Load demo data files in order
odoo-bin shell -d $DB_NAME --load-language=en_US << EOF
import odoo
env = odoo.api.Environment(odoo.api.Environment.manage(), {}, {})

# Load demo data files
demo_files = [
    "demo/customer_inventory_demo.xml",
    "demo/advanced_billing_demo.xml", 
    "demo/model_records_demo.xml",
    "demo/field_label_demo_data.xml",
    "demo/intelligent_search_demo_data.xml",
    "demo/naid_demo_certificates.xml",
    "demo/records_config_mail_templates_data.xml"
]

for demo_file in demo_files:
    print(f"Loading {demo_file}...")
    env.ref('records_management').__loader__.load_data(demo_file)
    env.cr.commit()

print("✅ Demo data loaded successfully!")
EOF
