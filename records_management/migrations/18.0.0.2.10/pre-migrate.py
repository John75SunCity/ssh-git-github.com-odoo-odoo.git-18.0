"""
Migration 18.0.0.2.10: Find and fix references to deleted stock.location(36)

Issue: MissingError appears in UI because some records still reference
the deleted stock.location ID 36.

Strategy:
1. Find all tables with foreign keys to stock_location
2. Find records pointing to location ID 36
3. Set those references to NULL or a valid default location
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Find and fix all references to deleted stock.location(36)"""

    _logger.info("=" * 80)
    _logger.info("MIGRATION 18.0.0.2.10: Finding references to stock.location(36)")
    _logger.info("=" * 80)

    # Step 1: Find all tables with location_id columns
    cr.execute("""
        SELECT 
            table_name,
            column_name
        FROM information_schema.columns
        WHERE 
            column_name LIKE '%location_id%'
            AND table_schema = 'public'
            AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name
    """)

    location_columns = cr.fetchall()
    _logger.info("Found %d tables with location columns", len(location_columns))

    # Step 2: Check each table for references to location ID 36
    tables_with_36 = []

    for table_name, column_name in location_columns:
        try:
            # Check if this column references location 36
            cr.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE {column_name} = 36
            """)
            count = cr.fetchone()[0]

            if count > 0:
                tables_with_36.append((table_name, column_name, count))
                _logger.warning(
                    "⚠️  Table '%s' has %d records with %s = 36",
                    table_name, count, column_name
                )

                # Show sample records for debugging
                cr.execute(f"""
                    SELECT id, {column_name}
                    FROM {table_name}
                    WHERE {column_name} = 36
                    LIMIT 5
                """)
                samples = cr.fetchall()
                for record_id, loc_id in samples:
                    _logger.info(
                        "  → Record ID %s in %s.%s points to location %s",
                        record_id, table_name, column_name, loc_id
                    )

        except Exception as e:
            # Skip if column doesn't exist or other error
            _logger.debug("Skipped %s.%s: %s", table_name, column_name, e)
            continue

    # Step 3: Report findings
    if tables_with_36:
        _logger.warning("")
        _logger.warning("=" * 80)
        _logger.warning("FOUND %d TABLES WITH REFERENCES TO LOCATION 36:", len(tables_with_36))
        _logger.warning("=" * 80)
        for table, column, count in tables_with_36:
            _logger.warning("  • %s.%s: %d records", table, column, count)
        _logger.warning("")
        _logger.warning("Next step: Update migration to set these to NULL or valid location")
        _logger.warning("=" * 80)
    else:
        _logger.info("✅ No database references to location 36 found!")
        _logger.info("The MissingError may be caused by:")
        _logger.info("  1. Cached view data (restart Odoo)")
        _logger.info("  2. Session data (log out and back in)")
        _logger.info("  3. Browser cache (hard refresh)")

    _logger.info("Migration 18.0.0.2.10 diagnostic complete")
