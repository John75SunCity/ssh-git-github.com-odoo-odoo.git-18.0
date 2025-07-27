# -*- coding: utf-8 -*-
# Records Management Module - Enterprise Grade DMS

from . import models
from . import controllers
from . import report
from . import wizards
from . import monitoring  # Live monitoring system

def post_init_hook(cr, registry):
    """
    Post initialization hook for Records Management module.
    This runs AFTER all dependencies are loaded, ensuring proper integration.
    """
    import logging
    from odoo import api, SUPERUSER_ID
    
    _logger = logging.getLogger(__name__)
    
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Verify all required dependencies are loaded
        required_modules = [
            'base', 'mail', 'web', 'portal', 'product', 'stock', 
            'barcodes', 'account', 'sale', 'website', 'point_of_sale',
            'sms', 'sign', 'hr', 'project', 'calendar', 'survey'
        ]
        
        installed_modules = env['ir.module.module'].search([
            ('name', 'in', required_modules),
            ('state', '=', 'installed')
        ])
        
        missing_deps = set(required_modules) - set(installed_modules.mapped('name'))
        if missing_deps:
            _logger.warning("Records Management: Missing dependencies: %s", missing_deps)
        else:
            _logger.info("Records Management: All dependencies verified - module loaded correctly")
        
        # Initialize any cross-module integrations here
        # This ensures other modules are fully loaded before we integrate
        try:
            # Example: Ensure POS integration works properly
            if env['ir.module.module'].search([('name', '=', 'point_of_sale'), ('state', '=', 'installed')]):
                _logger.info("Records Management: POS integration ready")
            
            # Example: Ensure website portal integration works
            if env['ir.module.module'].search([('name', '=', 'website'), ('state', '=', 'installed')]):
                _logger.info("Records Management: Website portal integration ready")
                
        except Exception as e:
            _logger.error("Records Management post_init_hook error: %s", e)