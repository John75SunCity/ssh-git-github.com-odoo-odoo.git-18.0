# -*- coding: utf-8 -*-
{
    'name': 'Vis.js Network Library',
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Vis.js Network Visualization Library for Odoo',
    'description': """
Vis.js Network Library Integration
===================================

This module provides the vis.js network visualization library for use
in Odoo modules. It bundles the vis.js library as an Odoo asset that
can be included in any module.

Features
--------

* Vis.js network visualization library
* Proper asset bundling for Odoo 18
* Reusable across multiple modules
* CDN fallback support

Usage
-----

Add 'web_vis_network' to your module dependencies, then include the
asset bundle in your views::

    'depends': ['web', 'web_vis_network'],
    
    'assets': {
        'web.assets_backend': [
            'web_vis_network/static/lib/vis-network/vis-network.min.js',
        ],
    }

Or use it in custom Owl components for advanced visualizations.

Note: Library files must be downloaded separately. See README.md for instructions.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            # Vis.js library files (local - no CDN dependency!)
            'web_vis_network/static/lib/vis-network/vis-network.min.js',
            'web_vis_network/static/lib/vis-network/vis-network.min.css',
            # Owl component for network diagrams
            'web_vis_network/static/src/components/network_diagram.js',
            'web_vis_network/static/src/xml/network_diagram.xml',
        ],
        'web.assets_frontend': [
            # Vis.js library for frontend (portal, website, etc.)
            'web_vis_network/static/lib/vis-network/vis-network.min.js',
            'web_vis_network/static/lib/vis-network/vis-network.min.css',
            # Frontend components
            'web_vis_network/static/src/components/network_diagram.js',
            'web_vis_network/static/src/xml/network_diagram.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
