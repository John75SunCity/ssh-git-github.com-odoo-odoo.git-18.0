# -*- coding: utf-8 -*-
"""
Configuration Settings Extension for Records Management
"""

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    """
    Configuration Settings Extension for Records Management
    """
    
    _inherit = 'res.config.settings'
    
    # Records Management Configuration
    records_management_enabled = fields.Boolean(
        string='Enable Records Management',
        config_parameter='records_management.enabled',
        default=True
    )
    
    # Default retention policies
    default_retention_years = fields.Integer(
        string='Default Retention Years',
        config_parameter='records_management.default_retention_years',
        default=7
    )
    
    # NAID Compliance Settings
    naid_compliance_enabled = fields.Boolean(
        string='Enable NAID Compliance',
        config_parameter='records_management.naid_compliance_enabled',
        default=True
    )
    
    naid_member_id = fields.Char(
        string='NAID Member ID',
        config_parameter='records_management.naid_member_id'
    )
    
    # Automatic billing settings
    auto_billing_enabled = fields.Boolean(
        string='Enable Automatic Billing',
        config_parameter='records_management.auto_billing_enabled',
        default=True
    )
    
    # POS Integration Settings
    pos_records_integration = fields.Boolean(
        string='Enable POS Records Integration',
        config_parameter='records_management.pos_integration',
        default=False
    )
    
    # Customer display type for POS integration (this fixes the KeyError)
    customer_display_type = fields.Selection([
        ('none', 'No Display'),
        ('basic', 'Basic Display'),
        ('advanced', 'Advanced Display with Services'),
        ('full', 'Full Service Display')
    ], string='Customer Display Type', 
       config_parameter='records_management.customer_display_type',
       default='basic')
    
    pos_customer_display_type = fields.Selection(
        related='customer_display_type',
        readonly=False
    )
    
    # Default service settings
    default_shredding_rate = fields.Float(
        string='Default Shredding Rate',
        config_parameter='records_management.default_shredding_rate',
        default=0.0
    )
    
    default_storage_rate = fields.Float(
        string='Default Storage Rate',
        config_parameter='records_management.default_storage_rate', 
        default=0.0
    )
    
    default_retrieval_rate = fields.Float(
        string='Default Retrieval Rate',
        config_parameter='records_management.default_retrieval_rate',
        default=0.0
    )
    
    # Email notification settings
    email_notifications_enabled = fields.Boolean(
        string='Enable Email Notifications',
        config_parameter='records_management.email_notifications',
        default=True
    )
    
    # Audit trail settings
    audit_trail_retention_days = fields.Integer(
        string='Audit Trail Retention (Days)',
        config_parameter='records_management.audit_retention_days',
        default=2555  # 7 years
    )
    
    # Portal settings
    portal_enabled = fields.Boolean(
        string='Enable Customer Portal',
        config_parameter='records_management.portal_enabled',
        default=True
    )
    
    portal_self_service = fields.Boolean(
        string='Enable Portal Self-Service',
        config_parameter='records_management.portal_self_service',
        default=True
    )
    
    # Digital scanning settings
    digital_scanning_enabled = fields.Boolean(
        string='Enable Digital Scanning',
        config_parameter='records_management.digital_scanning',
        default=False
    )
    
    # Barcode settings
    barcode_enabled = fields.Boolean(
        string='Enable Barcode Management',
        config_parameter='records_management.barcode_enabled',
        default=True
    )
    
    # Advanced features
    ai_classification_enabled = fields.Boolean(
        string='Enable AI Document Classification',
        config_parameter='records_management.ai_classification',
        default=False
    )
    
    sentiment_analysis_enabled = fields.Boolean(
        string='Enable Sentiment Analysis',
        config_parameter='records_management.sentiment_analysis',
        default=True
    )
