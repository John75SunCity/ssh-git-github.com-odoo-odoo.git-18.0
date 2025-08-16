# -*- coding: utf-8 -*-

Records Retention Rule Management Module

This module provides individual retention rules that can be applied to specific
document types, categories, or conditions under a retention policy framework.


from odoo import models, fields, api, _

from odoo.exceptions import ValidationError




class RecordsRetentionRule(models.Model):

        Individual retention rules within a retention policy

    _name = "records.retention.rule"
    _description = "Records Retention Rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "policy_id, sequence, name"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Rule Name",
        required=True,
        tracking=True,
        help="Name of the retention rule"
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of rule application"
    
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,

    # ============================================================================
        # POLICY RELATIONSHIP
    # ============================================================================
    policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        required=True,
        ondelete="cascade",
        help="Parent retention policy"
    

        # ============================================================================
    # RULE CONDITIONS
        # ============================================================================
    document_type_id = fields.Many2one(
        "records.document.type",
        string="Document Type",
        help="Specific document type this rule applies to"
    
    
    condition_type = fields.Selection([)]
        ('document_type', 'Document Type'),
        ('tag', 'Document Tag'),
        ('category', 'Category'),
        ('custom', 'Custom Condition')
    
    
    condition_value = fields.Char(
        string="Condition Value",
        help="Value to match against (tag name, category, etc.)"
        

    # ============================================================================
        # RULE ACTIONS
    # ============================================================================
    retention_years = fields.Integer(
        string="Retention Years",
        default=0,
        help="Years to retain documents"
    
    retention_months = fields.Integer(
        string="Retention Months", 
        default=0,
        help="Additional months to retain"
    
    retention_days = fields.Integer(
        string="Retention Days",
        default=0,
        help="Additional days to retain"
    
    
    action = fields.Selection([)]
        ('retain', 'Retain'),
        ('destroy', 'Mark for Destruction'),:
            pass
        ('review', 'Flag for Review'),:
        ('archive', 'Archive')
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance):
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id", 
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id", 
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    

        # ============================================================================
    # VALIDATION METHODS
        # ============================================================================
    @api.constrains('retention_years', 'retention_months', 'retention_days')
    def _check_retention_periods(self):
        """Validate retention periods are not negative"""
        for rule in self:
            if (rule.retention_years < 0 or:)
                rule.retention_months < 0 or 
                rule.retention_days < 0
                raise ValidationError(_("Retention periods cannot be negative"))
            
            if (rule.retention_years == 0 and:)
                rule.retention_months == 0 and 
                rule.retention_days == 0
                raise ValidationError(_("At least one retention period must be specified"))

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends('policy_id', 'name')
    def _compute_display_name(self):
        """Generate display name for the rule""":
        for rule in self:
            if rule.policy_id and rule.name:
                rule.display_name = f"{rule.policy_id.name} - {rule.name}"
            else:
                rule.display_name = rule.name or "New Rule"
    
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True
    

        # Workflow state management
    state = fields.Selection([)]
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    
        help='Current status of the record'

