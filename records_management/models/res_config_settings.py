# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Records Management Configuration Settings
    module_records_management_setting = fields.Boolean(
        "Enable Records Management Features",
        config_parameter='records_management.setting'
    )
    
    # Document retention default period
    default_retention_period = fields.Integer(
        "Default Retention Period (Years)",
        config_parameter='records_management.default_retention_period',
        default=7
    )
    
    # Automatic shredding configuration
    auto_shredding_enabled = fields.Boolean(
        "Enable Automatic Shredding",
        config_parameter='records_management.auto_shredding_enabled'
    )
    
    # NAID compliance configuration
    naid_compliance_enabled = fields.Boolean(
        "Enable NAID AAA Compliance",
        config_parameter='records_management.naid_compliance_enabled',
        default=True
    )
    
    # Portal configuration
    portal_feedback_enabled = fields.Boolean(
        "Enable Customer Portal Feedback",
        config_parameter='records_management.portal_feedback_enabled',
        default=True
    )
    
    # Billing configuration
    auto_billing_enabled = fields.Boolean(
        "Enable Automatic Billing",
        config_parameter='records_management.auto_billing_enabled',
        default=True
    )
