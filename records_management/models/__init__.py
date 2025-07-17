# Import order: Load base models with Many2one fields first (comodels for inverses), then extensions/models with One2many (to avoid KeyError in ORM setup per Odoo 18.0 docs).
# Grouped for clarity: Core/base, compliance, extensions.

# Base/Core Models (Many2one first for inverses)
from . import barcode  # Barcode management for boxes/bales
from . import billing  # Billing views/models
from . import customer_inventory  # Customer inventory tracking
from . import departmental_billing  # Departmental billing
from . import paper_bale  # Paper baling models
from . import pickup_request  # Pickup requests
from . import portal_request  # Portal requests (destruction, services)
# from . import pos_config  # Commented to fix circular import; uncomment after resolving cycles in pos_config.py (e.g., move imports inside methods)
from . import records_box  # Box management
from . import records_document  # Document management
from . import records_document_type  # Document types
from . import records_location  # Locations
from . import records_retention_policy  # Retention policies
from . import records_tag  # Tags
from . import res_partner  # Partner extensions
from . import shredding  # Shredding services
from . import stock_lot  # Stock lots for traceability
from . import trailer_load  # Trailer loading
from . import visitor  # Visitor models (from frontdesk integration)
from . import visitor_pos_wizard  # POS wizard for visitors

# Shredding and Services
from . import shredding_service  # Shredding (documents/hard drives/uniforms - NAID compliant)

# Portal and FSM
from . import portal_request  # Portal requests (destruction/services)
from . import fsm_task  # FSM extensions for field actions

# HR and Feedback
from . import hr_employee  # Employee access/training (NAID certifications)
from . import hr_employee_naid  # NAID-specific employee tracking
from . import customer_feedback  # Feedback with sentiment (innovative: Integrate torch for AI analysis via code_execution)

# NAID Compliance Models
from . import naid_audit  # Audit logging (ISO 27001 integrity)
from . import naid_custody  # Chain of custody (timestamps/hashes per NAID 2025)

# Extensions (One2many after bases)
from . import res_partner  # Partner extensions (One2many to documents/departments)
from . import stock_lot  # Stock lots (barcodes/inventory)
from . import stock_move_sms_validation  # SMS validations for moves
from . import stock_picking  # Pickings (integrate with fleet for trucks)
from . import account_move  # Invoices (department_id Many2one for billing inverse)
from . import customer_inventory_report  # Inventory reports
from . import pos_config  # POS for walk-ins (if separate model)

# Wizards/Installers (last, as they depend on models)
from . import installer  # Module installer
from . import ir_actions_report  # Custom reports
from . import ir_module  # Module overrides if needed
