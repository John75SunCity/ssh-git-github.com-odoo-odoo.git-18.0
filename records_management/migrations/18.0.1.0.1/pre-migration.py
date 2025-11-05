"""Pre-migration script for Records Management 18.0.1.0.1

This migration ensures critical database fields exist BEFORE the ORM attempts
to load models and validate views. This prevents "Field does not exist" errors
during module installation/upgrade.

Migrations Included:
1. res_partner transitory field configuration (allow_transitory_items, etc.)
2. records.storage.department.user assignment fields (role, state, permissions)

Context:
- Runs automatically when upgrading to version 18.0.1.0.1
- Safe to run multiple times (checks for existing columns)
- Applies sensible defaults for existing records
- Works across all environments (dev, staging, production)

Migration Strategy:
- Uses IF NOT EXISTS checks to avoid duplicate column errors
- Sets appropriate default values for backward compatibility
- Logs all operations for audit trail
"""

import logging

_logger = logging.getLogger(__name__)


def _column_exists(cr, table_name, column_name):
    """Check whether a column exists on the given table."""
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
        """,
        (table_name, column_name),
    )
    return bool(cr.fetchone())


def _add_column_if_missing(cr, table_name, column_name, column_type, default_value=None):
    """Add a column if it doesn't exist, optionally setting defaults."""
    if not _column_exists(cr, table_name, column_name):
        _logger.info(
            "Adding column %s.%s (%s)", table_name, column_name, column_type
        )
        cr.execute(
            f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}'
        )

        # Set default value for existing rows if provided
        if default_value is not None:
            _logger.info(
                "Setting default value %s for existing rows in %s.%s",
                default_value,
                table_name,
                column_name,
            )
            cr.execute(
                f'UPDATE "{table_name}" SET "{column_name}" = %s WHERE "{column_name}" IS NULL',
                (default_value,),
            )
    else:
        _logger.info("Column %s.%s already exists, skipping", table_name, column_name)


def migrate(cr, version):
    """Add missing fields to res_partner and records.storage.department.user."""
    _logger.info("=" * 80)
    _logger.info("Running pre-migration for records_management 18.0.1.0.1")
    _logger.info("=" * 80)

    # ============================================================================
    # PART 1: res_partner transitory configuration fields
    # ============================================================================
    _logger.info("Adding res_partner transitory configuration fields...")
    
    # Add the new Many2one fields (nullable foreign keys)
    _add_column_if_missing(
        cr, "res_partner", "transitory_field_config_id", "INTEGER"
    )
    _add_column_if_missing(
        cr, "res_partner", "field_label_config_id", "INTEGER"
    )

    # Add the Boolean field with default
    _add_column_if_missing(
        cr, "res_partner", "allow_transitory_items", "BOOLEAN", default_value=True
    )

    # Add the Integer field with default
    _add_column_if_missing(
        cr, "res_partner", "max_transitory_items", "INTEGER", default_value=100
    )

    # ============================================================================
    # PART 2: records.storage.department.user assignment fields
    # ============================================================================
    _logger.info("Adding records.storage.department.user assignment fields...")
    
    # Check if the department user table exists yet
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'records_storage_department_user'
        );
    """)
    table_exists = cr.fetchone()[0]
    
    if table_exists:
        # Add role field (Selection stored as VARCHAR)
        _add_column_if_missing(
            cr, "records_storage_department_user", "role", "VARCHAR", default_value='viewer'
        )
        
        # Add state field (Selection stored as VARCHAR)
        _add_column_if_missing(
            cr, "records_storage_department_user", "state", "VARCHAR", default_value='active'
        )
        
        # Add permission boolean fields
        permission_fields = [
            'can_view_records',
            'can_create_records',
            'can_edit_records',
            'can_delete_records',
            'can_export_records'
        ]
        
        for field_name in permission_fields:
            _add_column_if_missing(
                cr, "records_storage_department_user", field_name, "BOOLEAN", default_value=False
            )
        
        # Add date and metadata fields
        _add_column_if_missing(
            cr, "records_storage_department_user", "start_date", "DATE"
        )
        _add_column_if_missing(
            cr, "records_storage_department_user", "end_date", "DATE"
        )
        _add_column_if_missing(
            cr, "records_storage_department_user", "priority", "VARCHAR", default_value='normal'
        )
        _add_column_if_missing(
            cr, "records_storage_department_user", "access_level", "VARCHAR", default_value='internal'
        )
        _add_column_if_missing(
            cr, "records_storage_department_user", "description", "VARCHAR"
        )
        _add_column_if_missing(
            cr, "records_storage_department_user", "notes", "TEXT"
        )
        
        _logger.info("✅ Department user assignment fields added successfully")
    else:
        _logger.info("Table records_storage_department_user does not exist yet - will be created by ORM")

    _logger.info("=" * 80)
    _logger.info("Pre-migration completed successfully!")
    _logger.info("=" * 80)
