# Wizards for Records Management
# This module contains wizard classes for various operations like invoicing, adjustments, etc.

# FSM Wizards
from . import fsm_reschedule_wizard

# Container volume calculator wizard
from . import custom_box_volume_calculator

# Shredding and destruction wizards
from . import hard_drive_scan_wizard  # Hard drive serial number scanner

# Additional wizards (based on available files)
from . import field_label_helper_wizard
from . import records_container_type_converter
from . import visitor_pos_wizard
from . import permanent_flag_wizard
from . import user_management_wizards
from . import key_restriction_checker
from . import location_report_wizard
from . import rate_change_confirmation_wizard
from . import records_permanent_flag_wizard
from . import records_location_report_wizard
from . import work_order_bin_assignment_wizard
from . import system_flowchart_wizard
from . import unlock_service_reschedule_wizard

# Note: records_user_invitation_wizard is in models folder, not wizards
# Note: fsm_reschedule_wizard_placeholder.py does not exist - removed

# Future wizard imports will be added here as they are developed:
# from . import invoice_wizard        # Automated invoicing wizard
# from . import adjustment_wizard     # Inventory adjustment wizard
# from . import bulk_operation_wizard # Bulk operations wizard
# from . import destruction_wizard    # Destruction certificate wizard
