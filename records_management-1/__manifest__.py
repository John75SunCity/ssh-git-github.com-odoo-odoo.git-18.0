{
    "name": "Records Management",
    "version": "1.0",
    "category": "Inventory",
    "summary": "Module for managing records and shredding services.",
    "description": "This module provides functionalities for managing stock production lots, shredding services, and pickup requests, including customer references and audit logging.",
    "author": "Your Name",
    "website": "https://yourwebsite.com",
    "depends": [
        "base",
        "stock",
        "sale",
        "web"
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/scrm_records_management_data.xml",
        "views/scrm_records_management_views.xml",
        "views/scrm_records_management_templates.xml",
        "views/assets.xml"
    ],
    "installable": true,
    "application": false,
    "auto_install": false
}