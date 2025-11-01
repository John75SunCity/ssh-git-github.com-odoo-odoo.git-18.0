"""Migration script to add missing res_partner fields before ORM loads.

This migration adds the transitory field configuration columns to res_partner
that were added in version 18.0.1.0.1 of the records_management module.
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
    """Add missing transitory configuration fields to res_partner."""
    _logger.info("Running pre-migration for records_management 18.0.1.0.1")

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

    _logger.info("Pre-migration completed successfully")
