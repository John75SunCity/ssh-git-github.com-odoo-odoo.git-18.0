# -*- coding: utf-8 -*-
{
    'name': 'Records Management - Enterprise Edition',
    'version': '18.0.11.0.0',
    'category': 'Document Management',
    'summary': 'Complete Enterprise Records Management System with NAID AAA Compliance',
    'description': '''
        Records Management - Enterprise Grade DMS Module
        A comprehensive, enterprise-grade Document Management System (DMS) built for Odoo 18.0.
        This module provides advanced functionality for managing physical document boxes, records,
        shredding services, and compliance tracking with NAID AAA and ISO 15489 standards.
    ''',
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'web', 'product', 'stock', 'account', 'sale', 'purchase',
        'portal', 'website', 'point_of_sale', 'sign', 'sms', 'survey',
        'hr', 'hr_timesheet', 'hr_payroll', 'project', 'maintenance',
        'sale_management', 'website_sale', 'industry_fsm', 'quality', 'website_slides',
        'sale_subscription', 'sale_renting', 'multi_branch'
    ],
    'data': [
        'security/*_security.xml',
        'security/ir.model.access.csv',
        'data/advanced_billing_demo.xml',
        'data/base_rates_container_access_data.xml',
        'data/document_retrieval_rates_data.xml',
        'data/feedback_survey_data.xml',
        'data/field_label_demo_data.xml',
        'data/fsm_automated_actions_data.xml',
        'data/fsm_mail_templates_data.xml',
        'data/intelligent_search_demo_data.xml',
        'data/intelligent_search_indexes_data.xml',
        'data/ir_sequence_data.xml',
        'data/load_data.xml',
        'data/model_records_demo.xml',
        'data/naid_certificate_data.xml',
        'data/naid_compliance_data.xml',
        'data/paper_products_data.xml',
        'data/portal_mail_templates_data.xml',
        'data/products_data.xml',
        'data/records_config_mail_templates_data.xml',
        'data/scheduled_actions_data.xml',
        'data/sequence_data.xml',
        'data/storage_fee_data.xml',
        'data/tag_data.xml',
        'data/temp_inventory_configurator_data.xml',
        'data/temp_inventory_sequence_data.xml',
        'data/user_setup_data.xml',
        'reports/account_move_line_reports.xml',
        'reports/additional_reports.xml',
        'views/records_management_dashboard_view.xml',
        'views/records_management_dashboard.xml',
        'views/records_management_menu.xml',
        'views/records_management_form.xml',
        'views/records_management_tree.xml',
        'templates/records_portal_templates.xml',
        'templates/records_dashboard_templates.xml',
        'views/records_management_document_view.xml',
        'views/records_management_shredding_view.xml',
        'views/records_management_settings_view.xml',
        'templates/records_management_portal_templates.xml',
        'templates/records_management_dashboard_templates.xml'
            'templates/records_management_dashboard_templates.xml'
        ],
    # Use glob patterns for views/templates if possible
        'demo': [
            'demo/demo_records.xml'
        ],
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/lib/vis/vis-network.min.js',
            'records_management/static/src/lib/vis/vis-network.min.css',
            'records_management/static/src/scss/records_management.scss',
            'records_management/static/src/js/map_widget.js',
            'records_management/static/src/js/paper_load_progress_field.js',
            'records_management/static/src/js/paper_load_truck_widget.js',
            'records_management/static/src/js/trailer_visualization.js',
            'records_management/static/src/js/truck_widget.js',
            'records_management/static/src/js/field_label_customizer.js',
            'records_management/static/src/js/intelligent_search.js',
            'records_management/static/src/css/intelligent_search.css',
            'records_management/static/src/js/system_flowchart_view.js',
            'records_management/static/src/css/system_flowchart.css',
            'records_management/static/src/js/customer_portal_diagram_view.js',
            'records_management/static/src/css/customer_portal_diagram.css',
            'records_management/static/src/xml/map_widget.xml',
            'records_management/static/src/xml/trailer_visualization.xml',
            'records_management/static/src/xml/intelligent_search_templates.xml',
            'records_management/static/src/xml/system_flowchart_templates.xml',
            'records_management/static/src/xml/customer_portal_diagram_templates.xml'
        ],
        'web.assets_frontend': [
            'records_management/static/src/lib/vis/vis-network.min.js',
            'records_management/static/src/lib/vis/vis-network.min.css',
            'records_management/static/src/css/portal_tour.css',
            'records_management/static/src/css/intelligent_search.css',
            'records_management/static/src/js/portal_tour.js',
            'records_management/static/src/js/portal_docs.js',
            'records_management/static/src/js/portal_inventory_highlights.js',
            'records_management/static/src/js/portal_inventory_search.js',
            'records_management/static/src/js/portal_quote_generator.js',
            'records_management/static/src/js/portal_signature.js',
            'records_management/static/src/js/portal_user_import.js',
            'records_management/static/src/js/intelligent_search.js',
            'records_management/static/src/js/customer_portal_diagram.js',
            'records_management/static/src/css/customer_portal_diagram.css',
            'records_management/static/src/xml/intelligent_search_templates.xml',
            'records_management/static/src/xml/customer_portal_diagram_templates.xml'
        ]
    },
    'external_dependencies': {
        'python': ['qrcode', 'pillow']
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 100,
    'images': ['static/description/icon.png']
}
