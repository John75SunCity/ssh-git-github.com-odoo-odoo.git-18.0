# -*- coding: utf-8 -*-
# Import order: Load base models with Many2one fields first (comodels for inverses), 
# then extensions/models with One2many (to avoid KeyError in ORM setup per Odoo 18.0 docs).
# Grouped for clarity: Core/base, compliance, extensions.

# Base/Core Models (Many2one first for inverses)
from . import records_tag
from . import records_location
from . import records_policy_version
from . import records_approval_workflow
from . import records_approval_step
from . import records_retention_policy
from . import records_document_type
from . import customer_inventory_report
from . import records_department
from . import records_department_billing_contact
from . import records_storage_department_user
from . import records_document
from . import records_digital_copy
from . import records_box
from . import box_contents
from . import pickup_request_item
from . import pickup_request
from . import temp_inventory

# New Paper Recycling Models (Business-focused)
from . import paper_bale_recycling
from . import paper_load_shipment

# Legacy bale models (for compatibility)
from . import bale
from . import paper_bale
from . import load

# NAID Compliance Models
from . import naid_compliance
from . import naid_custody_event
from . import naid_audit_log

# Document Related Models (custody, audit, digital copies)
from . import records_chain_of_custody
from . import destruction_item

# Box Related Models (movements, service requests)
from . import records_box_movement
from . import records_box_transfer

# Shredding and Services
from . import shredding_service
from . import shredding_hard_drive

# Bin Key Management System
from . import bin_key_management
from . import partner_bin_key
from . import mobile_bin_key_wizard
from . import shredding_bin_models
from . import work_order_shredding
from . import document_retrieval_work_order
from . import shredding_rates
from . import shredding_inventory

# Billing
from . import billing
from . import department_billing
from . import billing_models
from . import advanced_billing
from . import billing_automation
from . import barcode_models
from . import records_deletion_request

# Portal and FSM
from . import portal_request
from . import fsm_task
from . import pos_config

# HR and Feedback - Load survey models first, then portal_feedback
from . import hr_employee
from . import hr_employee_naid
from . import customer_feedback
from . import survey_user_input
from . import survey_feedback_theme
from . import survey_improvement_action

# Products and Configuration
from . import product
from . import barcode_product
from . import res_config_settings
from . import visitor

# Business Logic
from . import scrm_records_management

# NAID Compliance Models
from . import naid_audit
from . import naid_custody
from . import naid_compliance
from . import naid_certificate
from . import naid_compliance_checklist
from . import naid_destruction_record
from . import naid_performance_history

# Audit and Security Models
from . import records_security_audit
from . import records_location_inspection
from . import records_audit_log
from . import records_access_log
from . import records_chain_custody
from . import shredding_service_log

# Extensions (One2many after bases)
from . import res_partner
from . import stock_lot
from . import stock_move_sms_validation
from . import stock_picking
from . import account_move
from . import project_task

# Portal Feedback (moved later to avoid dependency issues)
from . import portal_feedback

# Wizards/Installers (last, as they depend on models)
from . import visitor_pos_wizard
from . import installer
from . import ir_actions_report
from . import ir_module
