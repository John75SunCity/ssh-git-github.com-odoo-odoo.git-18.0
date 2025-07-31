# Wizards for Records Management
# This module contains wizard classes for various operations like invoicing, adjustments, etc.

# Template and example wizards
from . import wizard_template  # Template for creating new wizards
from . import user_management_wizards  # User invitation and bulk import wizards

# Container management wizards (updated naming)
from . import records_container_type_converter  # Bulk container type conversion wizard
from . import work_order_bin_assignment_wizard  # Work order bin assignment wizard

# Rate management and forecasting wizards
from . import (
    rate_change_confirmation_wizard,
)  # Rate change confirmation and implementation

# Security wizards
from . import permanent_flag_wizard  # Original permanent flag security wizard
from . import records_permanent_flag_wizard  # Updated permanent flag security wizard
from . import key_restriction_checker  # Key restriction checker for technicians

# Reporting wizards
from . import location_report_wizard  # Original location utilization report wizard
from . import (
    records_location_report_wizard,
)  # Updated location utilization report wizard

# Shredding and destruction wizards
from . import hard_drive_scan_wizard  # Hard drive serial number scanner

# FSM Wizards
from . import fsm_reschedule_wizard

# Future wizard imports will be added here as they are developed:
# from . import invoice_wizard        # Automated invoicing wizard
# from . import adjustment_wizard     # Inventory adjustment wizard
# from . import bulk_operation_wizard # Bulk operations wizard
# from . import destruction_wizard    # Destruction certificate wizard
