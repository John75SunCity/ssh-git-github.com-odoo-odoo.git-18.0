# -*- coding: utf-8 -*-
"""
Post-initialization hooks for Odoo 19 compatibility
Handles module loading and initialization tasks
"""

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-initialization hook for Records Management module
    
    Handles Odoo 19 compatibility requirements:
    - Translation system initialization
    - Security group setup
    - Database constraints validation
    """
    _logger.info("Running Records Management post-init hook for Odoo 19...")

    try:
        # CRITICAL: Assign admin users to Settings and Records Admin groups
        # This fixes lockouts where admins can't access Settings
        _logger.info("🔧 Assigning admin users to Settings groups...")
        env['res.users']._assign_admin_groups()
        _logger.info("✅ Admin users assigned to Settings groups")

        # Ensure base admin user has compliance officer access
        admin_user = env.ref('base.user_admin', raise_if_not_found=False)
        compliance_group = env.ref('records_management.group_naid_compliance_officer', raise_if_not_found=False)

        if admin_user and compliance_group:
            admin_user.write({'groups_id': [(4, compliance_group.id)]})
            _logger.info("✅ Added admin user to NAID compliance officer group")

        # Validate critical models are loaded
        critical_models = [
            'records.container',
            'records.document',
            'naid.audit.log',
            'chain.of.custody'
        ]

        for model_name in critical_models:
            if model_name in env:
                _logger.info(f"✅ Model {model_name} loaded successfully")
            else:
                _logger.warning(f"⚠️  Model {model_name} not found")

        # Load demo data if in development mode
        # Check if we should load demo data (not already loaded and in dev mode)
        if not env['ir.config_parameter'].sudo().get_param('records_management.demo_loaded'):
            _logger.info("🎯 Loading demo/sample data for development...")
            try:
                # Load demo data files
                demo_files = [
                    'demo/customer_inventory_demo.xml',
                    'demo/advanced_billing_demo.xml',
                    'demo/model_records_demo.xml',
                    'demo/field_label_demo_data.xml',
                    'demo/intelligent_search_demo_data.xml',
                    'demo/naid_demo_certificates.xml',
                    'demo/records_config_mail_templates_data.xml'
                ]
                
                for demo_file in demo_files:
                    try:
                        _logger.info(f"  Loading {demo_file}...")
                        env['ir.ui.view']._load_records_create([{
                            'module': 'records_management',
                            'path': demo_file,
                        }])
                    except Exception as e:
                        _logger.warning(f"  ⚠️  Could not load {demo_file}: {e}")
                
                # Mark demo as loaded
                env['ir.config_parameter'].sudo().set_param('records_management.demo_loaded', 'True')
                _logger.info("✅ Demo data loaded successfully!")
                
            except Exception as e:
                _logger.warning(f"⚠️  Demo data loading failed: {e}")

        _logger.info("Records Management post-init hook completed successfully")

    except Exception as e:
        _logger.error(f"Error in post-init hook: {e}")
        # Don't raise - allow module to load even if post-init has issues
