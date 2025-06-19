{
    'name': 'Records Management',
    'version': '18.0.1.0.0',
    'summary': 'Manage records efficiently within Odoo. Centralized storage, search, permissions, and audit trails.',
    'description': """
Records Management
==================
A comprehensive module for managing records, integrating with stock and web modules.
Features include custom models, views, demo data, and scheduled actions.
""",
    'author': 'John Cope',
    'website': 'https://suncityshred.com',
    'category': 'Tools',
    'license': 'OPL-1',  # Odoo Proprietary License v1.0
    'icon': 'records_management/static/description/records_management_icon.png',
    'depends': [
        'base',        # Core Odoo module, always required
        'stock',       # Inventory/stock management
        'web',         # Web client features
        'mail',        # Messaging and chatter
        'portal',      # Portal access for external users
        'board',       # Dashboards (if you use them)
        'product',     # Product management (if you use products)
        'contacts',    # Partner/contact management
    ],
    'data': [
        'views/inventory_template.xml',
        'views/pickup_request.xml',
        'views/my_portal_inventory.xml',
        'views/shredding_views.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/products.xml',
        'data/scheduled_actions.xml',
    ],
    'installable': True,
    'application': True,
    'live_test_url': 'https://probable-space-fishstick-x54pvrqvrwq9f6xp5-8069.app.github.dev/',  # Replace with your actual demo URL
    'price': 2000,  # USD
    'currency': 'USD',
    'support': 'john@suncityshred.com',  # Replace with your support email
    'odoo_version': '18.0',
    'test_db': 'johncope-testdev',
    # Optional: To define a theme, add 'theme' or 'themes' to category, e.g. 'category': 'Tools,theme'
    # Optional: To hide a module, add 'hidden' or 'setting' to category, e.g. 'category': 'Tools,hidden'
}