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
from . import fsm_reschedule_wizard_placeholder
from . import records_container_type_converter_wizard
from . import records_user_invitation_wizard
from . import visitor_pos_wizard

# Future wizard imports will be added here as they are developed:
# from . import invoice_wizard        # Automated invoicing wizard
# from . import adjustment_wizard     # Inventory adjustment wizard
# from . import bulk_operation_wizard # Bulk operations wizard
# from . import destruction_wizard    # Destruction certificate wizard

# Note: The following imports were removed due to missing files or circular import issues:
# - wizard_template, user_management_wizards, system_flowchart_wizard (unused/missing)
# - records_container_type_converter, work_order_bin_assignment_wizard (unused/missing)
# - rate_change_confirmation_wizard, permanent_flag_wizard (unused/missing)
# - records_permanent_flag_wizard, key_restriction_checker (unused/missing)
# - location_report_wizard, records_location_report_wizard (unused/missing)
# - visitor_pos_wizard (unused/missing)
