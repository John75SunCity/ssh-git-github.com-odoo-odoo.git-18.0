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

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
