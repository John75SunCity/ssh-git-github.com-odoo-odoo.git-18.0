# Updated file: Added imports for new models (portal_request, temp_inventory, fsm extensions).

from . import installer
from . import ir_actions_report
from . import ir_module
from . import records_tag
from . import records_location
from . import records_retention_policy
from . import records_document_type
from . import records_box
from . import records_document
from . import pickup_request
from . import pickup_request_item
from . import res_partner
from . import scrm_records_management
from . import shredding_service
from . import stock_lot
from . import stock_move_sms_validation
from . import stock_picking
from . import customer_inventory_report
from . import paper_bale
from . import trailer_load
from . import portal_request  # New: Model for portal requests (destruction, services)
from . import temp_inventory  # New: Model for temporary inventory additions
from . import fsm_task  # New: Extension for FSM tasks from portal
from . import hr_employee  # Updated: For user access imports
