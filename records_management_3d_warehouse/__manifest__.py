{
    'name': '3D Warehouse Visualization',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Advanced 3D warehouse visualization with interactive blueprints and capacity analytics',
    'description': """
3D Warehouse Visualization for Records Management
==================================================

Features:
---------
* Interactive 3D warehouse visualization using vis.js Graph3d
* Visual blueprint designer with drag-and-drop walls, doors, and offices
* Smart shelving configurator with auto-duplication
* Multiple visualization modes:
  - Capacity utilization heat maps
  - Revenue per container
  - Customer-based coloring
  - Container age (FIFO/LIFO)
  - FSM work order highlighting
  - Metadata visualization
* Time-travel feature to view historical warehouse states
* FSM technician picklist navigation
* Real-time capacity tracking
* Export to PNG/PDF
* Mobile-optimized views

Technical Requirements:
-----------------------
* Depends on web_vis_network module (for vis.js library)
* Requires records_management module
* Uses Owl framework for reactive UI
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'web',
        'web_vis_network',
        'records_management',
        'industry_fsm',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/default_shelving_templates.xml',
        
        # Views
        'views/warehouse_blueprint_views.xml',
        'views/warehouse_shelving_template_views.xml',
        'views/warehouse_3d_view_config_views.xml',
        'views/stock_location_3d_views.xml',
        'views/records_management_3d_menus.xml',
        
        # Wizards
        'wizards/warehouse_3d_quickstart_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'records_management_3d_warehouse/static/src/components/**/*.js',
            'records_management_3d_warehouse/static/src/components/**/*.xml',
            'records_management_3d_warehouse/static/src/components/**/*.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
