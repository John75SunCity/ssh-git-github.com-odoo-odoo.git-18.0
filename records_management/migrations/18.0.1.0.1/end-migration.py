"""End migration script - runs after module upgrade completes.

This ensures any cleanup or post-upgrade tasks are handled.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration cleanup and verification."""
    _logger.info("End-migration for records_management 18.0.1.0.1 - verifying columns exist")
    
    # Verify all columns were created
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' 
        AND column_name IN (
            'transitory_field_config_id',
            'field_label_config_id',
            'allow_transitory_items',
            'max_transitory_items'
        )
    """)
    
    existing_columns = [row[0] for row in cr.fetchall()]
    expected_columns = [
        'transitory_field_config_id',
        'field_label_config_id',
        'allow_transitory_items',
        'max_transitory_items'
    ]
    
    for col in expected_columns:
        if col in existing_columns:
            _logger.info(f"✅ Column res_partner.{col} exists")
        else:
            _logger.error(f"❌ Column res_partner.{col} is MISSING!")
    
    _logger.info("End-migration completed")
