from . import pickup_request_line
from . import location_group
from . import inventory_adjustment_reason
from . import inventory_item
from . import inventory_item_retrieval
from . import inventory_item_destruction
from . import key_inventory
from . import pickup_location
from . import full_customization_name
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
from . import records_tag_category
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
from . import records_approval_workflow_line
from . import records_service_type

# Container and storage models (in dependency order)
from . import customer_inventory
from . import records_container_type
from . import container_content
from . import records_container_type_converter

# =============================================================================
# SERVICE MANAGEMENT MODELS (Load shredding_service before paper_bale_recycling)
# =============================================================================

# Shredding services (MUST be loaded before paper_bale_recycling due to inverse field)
from . import shredding_team
from . import shredding_certificate
from . import shredding_hard_drive
from . import shredding_service_log
from . import destruction_item
from . import shred_bin
from . import shredding_service

# =============================================================================
# CORE BUSINESS MODELS
# =============================================================================

# Document management
from . import naid_custody
from . import records_document
from . import records_digital_scan

# Container operations (in dependency order)
from . import records_container_movement
from . import records_container_transfer
from . import records_container_transfer_line

# Customer and inventory management
from . import customer_inventory_report
from . import temp_inventory
from . import temp_inventory_movement
from . import temp_inventory_audit
from . import temp_inventory_reject_wizard

# Pickup and transportation
from . import pickup_request
from . import pickup_request_item
from . import pickup_route
from . import pickup_route_stop
from . import records_vehicle

# =============================================================================
# PAPER RECYCLING AND BALING MODELS (After shredding services)
# =============================================================================

# Modern paper recycling system (depends on shredding_service.recycling_bale_id)
from . import paper_bale_recycling
from . import paper_load_shipment

# Advanced billing system (base model first)

from . import advanced_billing
from . import advanced_billing_service_line
from . import advanced_billing_storage_line
from . import inventory_item_location_transfer
# Note: advanced_billing_line and sublines imported above to avoid circular dependency
from . import records_advanced_billing_period

# Work orders
from . import work_order_shredding
from . import records_retrieval_work_order
from . import work_order_retrieval

# Document retrieval support models (separate files following Odoo standards)
from . import retrieval_item_base  # ABSTRACT BASE - must be imported first
from . import document_retrieval_item
from . import document_retrieval_team
from . import document_retrieval_equipment

from . import document_search_attempt
from . import file_retrieval_work_order

# Service rates and billing (consolidated system)
from . import base_rate
from . import customer_negotiated_rate
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

# Key management services
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
from . import paper_bale_movement
from . import paper_bale_inspection
from . import generated_model
from . import paper_bale_inspection_wizard
from . import load

# =============================================================================
# NAID COMPLIANCE AND AUDIT MODELS
# =============================================================================

# Core NAID compliance
from . import naidcustody_event
from . import naidaudit_log
from . import naid_certificate
from . import naid_certificate_item
from . import naid_compliance_checklist
from . import naid_compliance_checklist_item
from . import naid_compliance_action_plan
from . import naid_compliance_alert
from . import records_destruction  # New destruction model
from . import naid_performance_history
from . import naid_risk_assessment

# Chain of custody tracking
from . import records_chain_of_custody
from . import chain_of_custody

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
from . import records_billing_service

# Advanced billing features
from . import customer_billing_profile
from . import revenue_forecast
from . import revenue_forecast_line

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
from . import portal_feedback_resolution

# Survey and improvement tracking
from . import records_survey_user_input
from . import survey_feedback_theme
from . import survey_improvement_action
from . import feedback_improvement_area

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
from . import stock_move_smsvalidation
from . import stock_picking

# Project and FSM integration
from . import project_task
from . import fsm_task
from . import fsm_route

# POS integration
from . import pos_config

# HR integration
from . import hr_employee

# =============================================================================
# PRODUCTS AND BARCODE MANAGEMENT
# =============================================================================

from . import product_template
from . import product_product
from . import product_container_type
from . import barcode_product
from . import barcode_models_enhanced

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
from . import required_document
from . import container_access_visitor
from . import container_access_activity

# =============================================================================
# BUSINESS LOGIC AND CRM
# =============================================================================

from . import customer_category

from . import records_deletion_request

# =============================================================================
# CONFIGURATION AND UTILITIES (Load last to avoid circular imports)
# =============================================================================

# Module management
from . import records_installer
from . import location_report_wizard
from . import rm_module_configurator

# =============================================================================
# WIZARDS AND UTILITIES
# =============================================================================
from . import hard_drive_scan_wizard
from . import fsm_reschedule_wizard
from . import key_restriction_checker

# Stock extensions (loaded after core models)
from . import stock_lot
from . import stock_lot_attribute
from . import stock_lot_attribute_option
from . import stock_lot_attribute_value

# Final models
from . import payment_split
from . import payment_split_line
from . import records_usage_tracking
from . import maintenance_equipment
from . import maintenance_team
from . import shredding_inventory_batch

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
        str(e)
    )


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
# NEWLY CREATED MISSING MODELS (10 MODELS)
# =============================================================================

# Digital asset models
from . import scan_digital_asset

# Mobile and photo models
from . import mobile_photo

# Route optimization
from . import route_optimizer

# Chain of custody events
from . import custody_transfer_event

# Certificate template system
from . import certificate_template_data

# =============================================================================
# SUB-MODEL EXTENSIONS (Individual models for One2many relationships)
# =============================================================================

# Billing configuration audit and line sub-models
from . import records_billing_config_audit
from . import records_billing_config_line

# File retrieval metrics sub-models
from . import retrieval_metric

# Shredding service sub-models
from . import shredding_service_photo
from . import shredding_picklist_item

# Customer inventory sub-models
from . import customer_inventory_report_line

from . import shredding_rate
from . import records_billing
from . import file_retrieval_work_order_item
from . import records_location_report_wizard
from . import records_inventory_dashboard

# =============================================================================
# NEWLY IDENTIFIED MISSING IMPORTS
# =============================================================================
from . import bin_key_unlock_service
from . import container_retrieval
from . import container_retrieval_item
from . import file_retrieval
from . import file_retrieval_item
from . import naid_destruction_record
from . import pickup_schedule_wizard
from . import records_bulk_user_import
from . import scan_retrieval
from . import transitory_item
from . import records_destruction_job
from . import records_category
from . import records_series
from . import records_storage_box
from . import records_request
from . import records_request_line
from . import records_request_type
from . import records_billing_contact_role
from . import billing_period
