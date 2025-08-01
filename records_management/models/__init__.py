# -*- coding: utf-8 -*-
"""
Records Management Models Import Order

Import order follows Odoo 18.0 best practices:
1. Base models with Many2one fields first (comodels for inverse relationships)
2. Core business models
3. Compliance and audit models
4. Extensions and integrations
5. Wizards and utilities last

This ensures proper ORM setup and prevents KeyError exceptions during module loading.
"""

# =============================================================================
# BASE MODELS (Many2one targets - must be loaded first)
# =============================================================================

# Configuration settings (foundational)
from . import res_config_settings

# Core structure models
from . import records_tag
from . import records_location
from . import records_department
from . import records_department_billing_contact
from . import records_storage_department_user
from . import customer_rate_profile

# Document and policy models
from . import records_document_type
from . import records_retention_policy
from . import records_policy_version
from . import records_approval_workflow
from . import records_approval_step

# Container and storage models (in dependency order)
from . import records_container
from . import container_contents

# =============================================================================
# CORE BUSINESS MODELS
# =============================================================================

# Document management
from . import records_document
from . import records_digital_scan

# Container operations (in dependency order)
from . import records_container_movement
from . import records_container_transfer

# Customer and inventory management
from . import customer_inventory_report
from . import temp_inventory

# Pickup and transportation
from . import pickup_request_item
from . import pickup_request
from . import pickup_route
from . import records_vehicle

# =============================================================================
# SERVICE MANAGEMENT MODELS
# =============================================================================

# Shredding services
from . import shredding_service
from . import shredding_hard_drive
from . import shredding_inventory
from . import shredding_service_log
from . import shredding_bin_models
from . import destruction_item

# Work orders
from . import work_order_shredding
from . import document_retrieval_work_order
from . import file_retrieval_work_order

# Service rates and billing
from . import shredding_rates
from . import customer_retrieval_rates

# Key management services
from . import bin_key_management
from . import bin_key_history  # Must be before partner_bin_key (One2many target)
from . import unlock_service_history  # Must be before partner_bin_key (One2many target)
from . import photo  # Must be before mobile_bin_key_wizard (One2many target)
from . import partner_bin_key
from . import mobile_bin_key_wizard
from . import bin_unlock_service

# =============================================================================
# PAPER RECYCLING AND BALING MODELS
# =============================================================================

# Modern paper recycling system
from . import paper_bale_recycling
from . import paper_load_shipment

# Legacy bale models (for data migration compatibility)
from . import bale
from . import paper_bale
from . import load

# =============================================================================
# NAID COMPLIANCE AND AUDIT MODELS
# =============================================================================

# Core NAID compliance
from . import naid_compliance
from . import naid_audit
from . import naid_custody
from . import naid_custody_event
from . import naid_audit_log
from . import naid_certificate
from . import naid_compliance_checklist
from . import naid_destruction_record
from . import naid_performance_history

# Chain of custody tracking
from . import records_chain_of_custody

# Security and audit logs
from . import records_security_audit
from . import records_location_inspection
from . import records_audit_log
from . import records_access_log

# =============================================================================
# BILLING AND FINANCIAL MODELS
# =============================================================================

# Core billing system
from . import billing
from . import billing_models
from . import billing_automation
from . import department_billing

# Advanced billing features
from . import advanced_billing
from . import customer_billing_profile

# Revenue forecasting and analytics
from . import revenue_forecaster

# =============================================================================
# PORTAL AND CUSTOMER INTERACTION
# =============================================================================

# Portal requests and feedback
from . import portal_request
from . import portal_feedback
from . import customer_feedback

# Survey and improvement tracking
from . import survey_user_input
from . import survey_feedback_theme
from . import survey_improvement_action

# Transitory items and field customization
from . import transitory_items
from . import transitory_field_config
from . import field_label_customization

# =============================================================================
# INTEGRATIONS AND EXTENSIONS
# =============================================================================

# Odoo core model extensions (base models first)
from . import res_partner
from . import res_partner_key_restriction

# Stock and inventory extensions
from . import stock_lot
from . import stock_move_sms_validation
from . import stock_picking

# Accounting integration
from . import account_move

# Project and FSM integration
from . import project_task
from . import fsm_task

# POS integration
from . import pos_config

# HR integration
from . import hr_employee
from . import hr_employee_naid

# =============================================================================
# PRODUCTS AND BARCODE MANAGEMENT
# =============================================================================

from . import product
from . import barcode_product
from . import barcode_models

# =============================================================================
# VISITORS AND ACCESS MANAGEMENT
# =============================================================================

from . import visitor
from ..wizards import visitor_pos_wizard

# =============================================================================
# BUSINESS LOGIC AND CRM
# =============================================================================

from . import scrm_records_management
from . import records_deletion_request

# =============================================================================
# CONFIGURATION AND UTILITIES (Load last)
# =============================================================================

# Module management
from . import installer
from . import ir_actions_report
from . import ir_module

from . import records_management_base_menus
from . import location_report_wizard

# =============================================================================
# FSM (FIELD SERVICE MANAGEMENT) EXTENSIONS - Conditional Import
# =============================================================================
# FSM models are only loaded if industry_fsm module is available
# This allows the module to work both in full Odoo.sh environment and limited dev environments
import logging

_logger = logging.getLogger(__name__)

try:
    # Check if we can import the fsm models without errors
    from . import fsm_task
    from . import fsm_route_management
    from . import fsm_notification

    _logger.info("FSM extensions loaded successfully")
except Exception as e:
    _logger.warning("FSM modules not available, skipping FSM extensions: %s", str(e))
