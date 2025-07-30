# -*- coding: utf-8 -*-
"""
Document Retention Policy
"""

from odoo import models, fields, api, _


class RecordsRetentionPolicy(models.Model):
    """
    Document Retention Policy
    """

    _name = "records.retention.policy"
    _description = "Document Retention Policy"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    description = fields.Text(string="Description", help="Detailed description of the retention policy")
    code = fields.Char(string="Policy Code", help="Short code for the retention policy")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Policy Manager', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    
    # Retention configuration
    retention_period = fields.Integer(string="Retention Period (Years)", 
                                     help="Number of years to retain documents")
    retention_period_months = fields.Integer(string="Additional Months",
                                           help="Additional months for precise retention")
    
    # Policy details
    legal_requirement = fields.Boolean(string="Legal Requirement", 
                                      help="Whether this is a legally mandated retention period")
    destruction_required = fields.Boolean(string="Destruction Required",
                                        help="Whether documents must be destroyed after retention period")

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    action_activate_policy = fields.Char(string='Action Activate Policy')
    action_deactivate_policy = fields.Char(string='Action Deactivate Policy')
    action_review_policy = fields.Char(string='Action Review Policy')
    action_view_exceptions = fields.Char(string='Action View Exceptions')
    action_view_policy_documents = fields.Char(string='Action View Policy Documents')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    approval_status = fields.Selection([], string='Approval Status')  # TODO: Define selection options
    button_box = fields.Char(string='Button Box')
    changed_by = fields.Char(string='Changed By')
    compliance_rate = fields.Float(string='Compliance Rate', digits=(12, 2))
    destruction_efficiency_rate = fields.Float(string='Destruction Efficiency Rate', digits=(12, 2))
    destruction_method = fields.Char(string='Destruction Method')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count', store=True)
    effective_date = fields.Date(string='Effective Date')
    exception_count = fields.Integer(string='Exception Count', compute='_compute_exception_count', store=True)
    group_policy_type = fields.Selection([], string='Group Policy Type')  # TODO: Define selection options
    group_risk = fields.Char(string='Group Risk')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    help = fields.Char(string='Help')
    high_risk = fields.Char(string='High Risk')
    is_current_version = fields.Char(string='Is Current Version')
    legal_basis = fields.Char(string='Legal Basis')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    next_mandatory_review = fields.Char(string='Next Mandatory Review')
    policy_effectiveness_score = fields.Char(string='Policy Effectiveness Score')
    policy_risk_score = fields.Char(string='Policy Risk Score')
    policy_status = fields.Selection([], string='Policy Status')  # TODO: Define selection options
    policy_type = fields.Selection([], string='Policy Type')  # TODO: Define selection options
    policy_version = fields.Char(string='Policy Version')
    res_model = fields.Char(string='Res Model')
    retention_years = fields.Char(string='Retention Years')
    review_cycle_months = fields.Char(string='Review Cycle Months')
    review_date = fields.Date(string='Review Date')
    risk_level = fields.Char(string='Risk Level')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    under_review = fields.Char(string='Under Review')
    version_date = fields.Date(string='Version Date')
    version_history_ids = fields.One2many('version.history', 'records_retention_policy_id', string='Version History Ids')
    version_number = fields.Char(string='Version Number')
    view_mode = fields.Char(string='View Mode')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('exception_ids')
    def _compute_exception_count(self):
        for record in self:
            record.exception_count = len(record.exception_ids)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
