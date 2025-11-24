# -*- coding: utf-8 -*-
"""Force update of wizard view that was causing ParseError"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Force reload the wizard view to fix cached inline tree issue"""
    _logger.info("🔄 Migration: Force updating add_to_work_order_wizard view...")
    
    # Delete the old cached view from the database
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE model = 'add.to.work.order.wizard' 
        AND name = 'add.to.work.order.wizard.view.form'
    """)
    
    _logger.info("✅ Old wizard view deleted - will be recreated on module load")
