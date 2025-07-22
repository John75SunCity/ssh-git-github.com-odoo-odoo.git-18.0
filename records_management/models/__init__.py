# -*- coding: utf-8 -*-
# Import order: Load base models with Many2one fields first (comodels for inverses), 
# then extensions/models with One2many (to avoid KeyError in ORM setup per Odoo 18.0 docs).
# Grouped for clarity: Core/base, compliance, extensions.

# Base/Core Models (Many2one first for inverses)
from . import records_tag
from . import records_location
from . import records_retention_policy
from . import records_document_type
from . import customer_inventory_report
from . import records_department
from . import records_document
from . import records_box
from . import pickup_request_item
from . import pickup_request
from . import temp_inventory
from . import bale
from . import load
from . import paper_bale

# Shredding and Services
from . import shredding_service

# Portal and FSM
from . import portal_request
from . import portal_request_fixed
from . import fsm_task

# HR and Feedback
from . import hr_employee
from . import hr_employee_naid
from . import customer_feedback
from . import survey_user_input
from . import survey_feedback_theme
from . import survey_improvement_action

# Products and Configuration
from . import product
from . import res_config_settings
from . import visitor

# Business Logic
from . import scrm_records_management

# NAID Compliance Models
from . import naid_audit
from . import naid_custody

# Extensions (One2many after bases)
from . import department_billing
from . import res_partner
from . import stock_lot
from . import stock_move_sms_validation
from . import stock_picking
from . import account_move
from . import project_task

# Wizards/Installers (last, as they depend on models)
from . import visitor_pos_wizard
from . import installer
from . import ir_actions_report
from . import ir_module
from . import is_walk_in
