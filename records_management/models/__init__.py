# -*- coding: utf-8 -*-
# Import order: Load base models with Many2one fields first (comodels for inverses), then extensions/models with One2many (to avoid KeyError in ORM setup per Odoo 18.0 docs).
# Grouped for clarity: Core/base, compliance, extensions.

# Base/Core Models (Many2one first for inverses)
from . import records_tag  # Basic tags
from . import records_location  # Locations
from . import records_retention_policy  # Policies (used in documents)
from . import records_document_type  # Types (used in documents)
from . import customer_inventory_report  # MOVED EARLY: Contains records.storage.department.user model needed by records_department
from . import records_department  # Department hierarchy (Many2one partner_id, parent_id)
from . import records_document  # Key: Has partner_id, department_id (Many2one) - load early
from . import records_box  # Boxes (links to documents)
from . import pickup_request_item  # Items (for requests)
from . import pickup_request  # Requests (links to items)
from . import temp_inventory  # Temporary inventory
from . import bale  # Bale management for recycling
from . import load  # Load management for transportation
from . import trailer_load  # Trailer loads (suggest PuLP optimization for efficiency)
from . import paper_bale  # Paper bales

# Shredding and Services
from . import shredding_service  # Shredding (documents/hard drives/uniforms - NAID compliant)

# Portal and FSM
from . import portal_request  # Portal requests (destruction/services)
from . import portal_request_fixed  # Fixed portal request model
from . import fsm_task  # FSM extensions for field actions

# HR and Feedback
from . import hr_employee  # Employee access/training (NAID certifications)
from . import hr_employee_naid  # NAID-specific employee tracking
from . import customer_feedback  # Feedback with sentiment (innovative: Integrate torch for AI analysis via code_execution)
from . import survey_user_input  # Survey user input extensions for feedback management

# Products and Configuration
from . import product  # Product extensions
from . import res_config_settings  # Configuration settings
from . import visitor  # Visitor management

# Business Logic
from . import scrm_records_management  # Core SCRM business logic

# NAID Compliance Models
from . import naid_audit  # Audit logging (ISO 27001 integrity)
from . import naid_custody  # Chain of custody (timestamps/hashes per NAID 2025)

# Extensions (One2many after bases)
from . import department_billing  # Department billing contacts (fixes missing models)
from . import res_partner  # Partner extensions (One2many to documents/departments)
from . import stock_lot  # Stock lots (barcodes/inventory)
from . import stock_move_sms_validation  # SMS validations for moves
from . import stock_picking  # Pickings (integrate with fleet for trucks)
from . import account_move  # Invoices (department_id Many2one for billing inverse)
# customer_inventory_report MOVED EARLIER in loading order
# from . import pos_config  # Commented to fix circular import; uncomment after resolving cycles in pos_config.py (e.g., move imports inside methods like def some_method: from . import other_model)

# Wizards/Installers (last, as they depend on models)
from . import visitor_pos_wizard  # POS wizard for visitor transactions
from . import installer  # Module installer
from . import ir_actions_report  # Custom reports
from . import ir_module  # Module overrides if needed
