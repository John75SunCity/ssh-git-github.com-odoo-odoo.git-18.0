"""Pre-init hooks for the Records Management module.

These hooks run before module installation or upgrade. They are used to
synchronize database schema artifacts that might be missing in existing
deployments prior to the ORM taking control of the upgrade process.
"""

from psycopg2 import sql


_MISSING_COLUMNS = (
    # column name, SQL type clause, default value (None means no bulk update)
    ("transitory_field_config_id", "INTEGER", None),
    ("field_label_config_id", "INTEGER", None),
    ("allow_transitory_items", "BOOLEAN", True),
    ("max_transitory_items", "INTEGER", 100),
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


def pre_init_hook(cr):
    """Ensure legacy databases have the partner fields required by the module."""
    table = "res_partner"
    for column_name, column_type, default_value in _MISSING_COLUMNS:
        if not _column_exists(cr, table, column_name):
            _add_column(cr, table, column_name, column_type)
        if default_value is not None:
            _set_default(cr, table, column_name, default_value)
```
