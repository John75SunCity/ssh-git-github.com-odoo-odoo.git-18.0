# -*- coding: utf-8 -*-
"""
Records Management Models Import Order

Import order follows Odoo 18.0 best practices:
1. Standard library imports first
2. Base models with Many2one fields first (comodels for inverse relationships)
3. Core business models
4. Compliance and audit models
5. Extensions and integrations
6. Wizards and utilities last

This ensures proper ORM setup and prevents KeyError exceptions during module loading.
"""

# =============================================================================
# STANDARD LIBRARY IMPORTS
# =============================================================================
import logging

_logger = logging.getLogger(__name__)

# =============================================================================
# BASE MODELS (Many2one targets - must be loaded first)
# =============================================================================

# Configuration settings (foundational - but avoid circular imports)
from . import res_config_settings
from . import records_config_settings

# System diagram data (for interactive visualization)
from . import system_diagram_data

# Core structure models
from . import records_tag
from . import records_location
from . import records_department
from . import records_container
from . import approval_history
from . import records_department_billing_contact
from . import records_storage_department_user

# Document and policy models
from . import records_document_type
from . import records_retention_policy
from . import records_retention_rule
from . import records_policy_version
from . import records_approval_workflow
from . import records_approval_step

# Container and storage models (in dependency order)
from . import customer_inventory
from . import records_container_type
from . import container_content
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
from . import temp_inventory_movement
from . import temp_inventory_audit
from . import temp_inventory_reject_wizard

# Pickup and transportation
from . import pickup_request_item
from . import pickup_request
from . import pickup_route
from . import pickup_route_stop
from . import records_vehicle

# =============================================================================
# SERVICE MANAGEMENT MODELS (Load shredding_service before paper_bale_recycling)
# =============================================================================

# Shredding services (MUST be loaded before paper_bale_recycling due to inverse field)
from . import shredding_team
from . import shredding_equipment
from . import shredding_certificate
from . import shredding_service
from . import shredding_hard_drive
from . import shredding_inventory_item
from . import shredding_service_log
from . import destruction_item
from . import shred_bin

# =============================================================================
# PAPER RECYCLING AND BALING MODELS (After shredding services)
# =============================================================================

# Modern paper recycling system (depends on shredding_service.recycling_bale_id)
from . import paper_bale_recycling
from . import paper_load_shipment

# Advanced billing system (base model first)
from . import advanced_billing
# Note: advanced_billing_line imported later to avoid circular dependency
from . import records_advanced_billing_period

# Work orders
from . import work_order_shredding
from . import document_retrieval_work_order
from . import records_retrieval_work_order
from . import work_order_retrieval

# Document retrieval support models (separate files following Odoo standards)
from . import document_retrieval_item
from . import document_retrieval_team
from . import document_retrieval_pricing
from . import document_retrieval_equipment
from . import document_retrieval_metric
from . import document_retrieval_support_models

from . import document_search_attempt
from . import file_retrieval_work_order

# Service rates and billing (consolidated system)
from . import base_rates
from . import customer_negotiated_rates

# Billing profiles (MUST be loaded before records_billing_contact)
from . import records_billing_profile
from . import records_customer_billing_profile

from . import records_billing_config
from . import records_billing_line
from . import records_billing_contact

# Individual billing support models
from . import invoice_generation_log
from . import discount_rule
from . import revenue_analytic
from . import records_promotional_discount
from . import billing_support_models

# Key management services
from . import bin_key_management
from . import partner_bin_key
from . import bin_key_history
from . import unlock_service_history
from . import unlock_service_part
from . import photo
from . import mobile_bin_key_wizard
from . import bin_unlock_service
from . import bin_key

# Legacy bale models (for data migration compatibility)
from . import bale
from . import paper_bale
from . import paper_bale_source_document
from . import paper_bale_movement
from . import paper_bale_inspection
from . import paper_bale_weigh_wizard
from . import paper_bale_inspection_wizard
from . import load

# =============================================================================
# NAID COMPLIANCE AND AUDIT MODELS
# =============================================================================

# Core NAID compliance
from . import naid_compliance
from . import naid_custody
from . import naid_custody_event
from . import naid_audit_log
from . import naid_certificate
from . import naid_compliance_checklist_item
from . import naid_compliance_action_plan
from . import naid_compliance_alert
from . import naid_destruction_record
from . import records_destruction  # New destruction model
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
from . import customer_billing_profile
from . import revenue_forecaster

# =============================================================================
# PORTAL AND CUSTOMER INTERACTION
# =============================================================================

# Portal requests and feedback
from . import portal_request
from . import signed_document
from . import signed_document_audit
from . import portal_feedback
from . import customer_feedback

# Customer portal diagram (interactive organizational visualization)
from . import customer_portal_diagram

# Portal feedback support models (comprehensive system)
from . import portal_feedback_escalation
from . import portal_feedback_action
from . import portal_feedback_communication
from . import portal_feedback_analytic

# Survey and improvement tracking
from . import records_survey_user_input
from . import survey_feedback_theme
from . import survey_improvement_action

# Transitory items and field customization
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

# Project and FSM integration
from . import project_task
from . import fsm_task

# POS integration
from . import pos_config

# HR integration
from . import hr_employee
from . import hremployee_naid

# =============================================================================
# =============================================================================
# PRODUCTS AND BARCODE MANAGEMENT
# =============================================================================

from . import product_template
from . import product_product
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

from . import customer_category
from . import scrm_records_management
from . import records_deletion_request

# =============================================================================
# CONFIGURATION AND UTILITIES (Load last to avoid circular imports)
# =============================================================================

# Module management
from . import installer
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
from . import stock_lot_attribute
from . import stock_lot_attribute_option
from . import stock_lot_attribute_value

# Final models
from . import payment_split
from . import records_usage_tracking
from . import maintenance_equipment
from . import shredding_inventory_batch
from . import wizard_template

# =============================================================================
# OPTIONAL EXTENSIONS AND INTEGRATIONS
# =============================================================================

try:
    # Check if we can import additional FSM models without errors
    from . import fsm_route_management
    from . import fsm_notification_manager
    from . import fsm_notification  # Individual notification records
    _logger.info("Additional FSM modules loaded successfully")
except (ImportError, AttributeError) as e:
    _logger.warning(
        "FSM extensions not available, skipping: %s",
        str(e),
    )

# =============================================================================
# CONDITIONAL IMPORTS FOR EXTENSION MODELS
# =============================================================================

# Note: records_deletion_request already imported at line 285

from . import records_user_invitation_wizard
from . import records_bulk_user_import

# Work Order Integration System (load mixin first)
from . import work_order_coordinator
from . import scan_retrieval_work_order
from . import scan_retrieval_item
from . import container_destruction_work_order
from . import container_access_work_order

# Model extensions for work order integration (project_task already imported above)
from . import account_move_line
from . import container_retrieval_work_order

# =============================================================================
# LATE-LOADING MODELS (to avoid circular dependencies)
# =============================================================================

# Note: records_billing_line already imported at line 133

# =============================================================================
# MISSING MODELS THAT NEED TO BE IMPORTED
# =============================================================================

# RM Module Configurator (if not already imported)
try:
    from . import rmmodule_configurator
    _logger.info("RM module configurator loaded successfully")
except (ImportError, AttributeError) as e:
    _logger.warning("RM module configurator not available: %s", str(e))

# File retrieval work order item (correct name)
from . import file_retrieval_work_order_item
from . import records_location_report_wizard
from . import records_inventory_dashboard
from . import customer_negotiated_rate
from . import base_rate
from . import product_container_type
from . import feedback_improvement_area
