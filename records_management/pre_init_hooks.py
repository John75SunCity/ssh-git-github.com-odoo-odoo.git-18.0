"""Pre-init hooks for the Records Management module.

These hooks run before module installation or upgrade. They are used to
synchronize database schema artifacts that might be missing in existing
deployments prior to the ORM taking control of the upgrade process.

CRITICAL: This runs during BOTH install and upgrade, unlike migrations which
only run during upgrade. This ensures fields exist before view validation.

Fields Added:
1. res_partner transitory configuration fields
2. records.storage.department.user assignment fields (role, state, permissions)

Context:
- Runs automatically before module loads (install or upgrade)
- Prevents "Field does not exist" ParseError during view validation
- Safe to run multiple times (checks for existing columns)
- Creates fields with sensible defaults for backward compatibility
"""

import logging
from psycopg2 import sql

_logger = logging.getLogger(__name__)


# res_partner missing columns (legacy support)
_MISSING_PARTNER_COLUMNS = (
    # column name, SQL type clause, default value (None means no bulk update)
    ("transitory_field_config_id", "INTEGER", None),
    ("field_label_config_id", "INTEGER", None),
    ("allow_transitory_items", "BOOLEAN", True),
    ("max_transitory_items", "INTEGER", 100),
)

# records.storage.department.user missing columns (department user assignment fields)
_MISSING_DEPT_USER_COLUMNS = (
    # column name, SQL type clause, default value (None means no bulk update)
    ("role", "VARCHAR", "viewer"),
    ("state", "VARCHAR", "active"),
    ("can_view_records", "BOOLEAN", False),
    ("can_create_records", "BOOLEAN", False),
    ("can_edit_records", "BOOLEAN", False),
    ("can_delete_records", "BOOLEAN", False),
    ("can_export_records", "BOOLEAN", False),
    ("start_date", "DATE", None),
    ("end_date", "DATE", None),
    ("priority", "VARCHAR", "normal"),
    ("access_level", "VARCHAR", "internal"),
    ("description", "VARCHAR", None),
    ("notes", "TEXT", None),
)


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


def _add_column(cr, table_name, column_name, column_type):
    """Add a column with the provided type definition."""
    query = sql.SQL("ALTER TABLE {table} ADD COLUMN {column} {ctype}").format(
        table=sql.Identifier(table_name),
        column=sql.Identifier(column_name),
        ctype=sql.SQL(column_type),
    )
    cr.execute(query)


def _set_default(cr, table_name, column_name, value):
    """Populate existing rows with a default value when provided."""
    query = sql.SQL("UPDATE {table} SET {column} = %s WHERE {column} IS NULL").format(
        table=sql.Identifier(table_name),
        column=sql.Identifier(column_name),
    )
    cr.execute(query, (value,))


def pre_init_hook(env):
    """
    Ensure legacy databases have all required fields before ORM loads.
    
    This hook runs during BOTH installation and upgrade, ensuring fields exist
    before Odoo validates views. This prevents "Field does not exist" ParseError.
    
    Tables handled:
    1. res_partner - transitory configuration fields
    2. records.storage.department.user - department user assignment fields
    """
    _logger.info("="*80)
    _logger.info("🚀 RUNNING PRE-INIT HOOK FOR RECORDS MANAGEMENT MODULE")
    _logger.info("="*80)
    
    # Extract cursor from environment
    cr = env.cr
    
    # =========================================================================
    # PART 1: res_partner transitory configuration fields
    # =========================================================================
    _logger.info("\n📋 PART 1: Checking res_partner columns...")
    table = "res_partner"
    for column_name, column_type, default_value in _MISSING_PARTNER_COLUMNS:
        if not _column_exists(cr, table, column_name):
            _logger.info(f"➕ Adding missing column: {table}.{column_name} ({column_type})")
            _add_column(cr, table, column_name, column_type)
            _logger.info(f"✅ Column {table}.{column_name} added successfully")
        else:
            _logger.info(f"⏭️  Column {table}.{column_name} already exists, skipping")
            
        if default_value is not None:
            _logger.info(f"🔧 Setting default value {default_value} for {table}.{column_name}")
            _set_default(cr, table, column_name, default_value)
            _logger.info(f"✅ Default value set for {table}.{column_name}")
    
    # =========================================================================
    # PART 2: records.storage.department.user assignment fields
    # =========================================================================
    _logger.info("\n📋 PART 2: Checking records.storage.department.user columns...")
    
    # Check if table exists first (it might not exist on fresh install)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'records_storage_department_user'
        );
    """)
    dept_table_exists = cr.fetchone()[0]
    
    if dept_table_exists:
        table = "records_storage_department_user"
        for column_name, column_type, default_value in _MISSING_DEPT_USER_COLUMNS:
            if not _column_exists(cr, table, column_name):
                _logger.info(f"➕ Adding missing column: {table}.{column_name} ({column_type})")
                _add_column(cr, table, column_name, column_type)
                _logger.info(f"✅ Column {table}.{column_name} added successfully")
            else:
                _logger.info(f"⏭️  Column {table}.{column_name} already exists, skipping")
                
            if default_value is not None:
                _logger.info(f"🔧 Setting default value '{default_value}' for {table}.{column_name}")
                _set_default(cr, table, column_name, default_value)
                _logger.info(f"✅ Default value set for {table}.{column_name}")
    else:
        _logger.info("⏭️  Table records_storage_department_user does not exist yet")
        _logger.info("   → Will be created by Odoo ORM during model initialization")
        _logger.info("   → Fields will be created automatically with model definition")
    
    _logger.info("\n" + "="*80)
    _logger.info("✅ PRE-INIT HOOK COMPLETED SUCCESSFULLY")
    _logger.info("="*80 + "\n")
