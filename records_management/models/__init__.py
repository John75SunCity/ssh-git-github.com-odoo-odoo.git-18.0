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

# System diagram data (for interactive visualization)
from . import system_diagram_data

# Core structure models
from . import records_tag
from . import records_location
from . import records_department
from . import approval_history
from . import records_department_billing_contact
from . import records_storage_department_user

# Document and policy models
from . import records_document_type
from . import records_retention_policy
from . import records_policy_version
from . import records_approval_workflow
from . import records_approval_step

# Container and storage models (in dependency order)
from . import customer_inventory
from . import records_container_type
from . import records_container
from . import container_contents
from . import records_container_type_converter

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
# SERVICE MANAGEMENT MODELS (Load shredding_service before paper_bale_recycling)
# =============================================================================

# Shredding services (MUST be loaded before paper_bale_recycling due to inverse field)
from . import shredding_team
from . import shredding_equipment
from . import maintenance_extensions
from . import shredding_certificate
from . import shredding_service
from . import shredding_hard_drive
from . import shredding_inventory
from . import shredding_inventory_item
from . import shredding_service_log
from . import shredding_bin_models
from . import destruction_item
from . import shred_bins

# =============================================================================
# PAPER RECYCLING AND BALING MODELS (After shredding services)
# =============================================================================

# Modern paper recycling system (depends on shredding_service.recycling_bale_id)
from . import paper_bale_recycling
from . import paper_load_shipment

# Work orders
from . import work_order_shredding
from . import document_retrieval_work_order
from . import document_retrieval_item
from . import file_retrieval_work_order

# Service rates and billing (consolidated system)
from . import base_rates
from . import customer_negotiated_rates
from . import records_billing_config

# Key management services
from . import bin_key_management
from . import partner_bin_key
from . import bin_key_history
from . import unlock_service_history
from . import photo
from . import mobile_bin_key_wizard
from . import bin_unlock_service
from . import bin_key

# Legacy bale models (for data migration compatibility)
from . import bale
from . import paper_bale
from . import paper_bale_source_document
from . import load

# =============================================================================
# NAID COMPLIANCE AND AUDIT MODELS
# =============================================================================

# Core NAID compliance
from . import naid_compliance
from . import naid_compliance_support_models
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
from . import billing_automation
from . import department_billing

# Advanced billing features
from . import advanced_billing
from . import customer_billing_profile
from . import revenue_forecaster

# Billing support models (new comprehensive system)
from . import billing_support_models

# =============================================================================
# PORTAL AND CUSTOMER INTERACTION
# =============================================================================

# Portal requests and feedback
from . import portal_request
from . import signed_document
from . import portal_feedback
from . import customer_feedback

# Customer portal diagram (interactive organizational visualization)
from . import customer_portal_diagram

# Portal feedback support models (comprehensive system)
from . import portal_feedback_support_models

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
from . import product_template
from . import barcode_product
from . import barcode_models

# Barcode support models (comprehensive system)
from . import barcode_generation_history
from . import barcode_pricing_tier
from . import barcode_storage_box
from . import processing_log
from . import service_item

# =============================================================================
# VISITORS AND ACCESS MANAGEMENT
# =============================================================================

from . import visitor
from . import visitor_pos_wizard
from . import required_document

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
# WIZARDS AND UTILITIES
# =============================================================================

from . import fsm_reschedule_wizard
from . import key_restriction_checker
from . import records_permanent_flag_wizard

# Stock extensions (loaded after core models)
from . import stock_lot

# =============================================================================
# OPTIONAL EXTENSIONS AND INTEGRATIONS
# =============================================================================

import logging

_logger = logging.getLogger(__name__)

try:
    # Check if we can import additional FSM models without errors
    from . import fsm_route_management
    from . import fsm_notification

    _logger.info("Additional FSM modules loaded successfully")
except ImportError as e:
    _logger.warning(
        "FSM module '%s' not available, skipping FSM extensions: %s",
        getattr(e, "name", "unknown"),
        str(e),
    )
