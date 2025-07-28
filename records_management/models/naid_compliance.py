# -*- coding: utf-8 -*-
"""
NAID Compliance Management
"""

from odoo import models, fields, api, _


class NAIDCompliance(models.Model):
    """
    NAID Compliance Management
    """

    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Policy-specific fields
    sequence = fields.Integer(string="Sequence", default=10)
    policy_type = fields.Selection([
        ('access_control', 'Access Control'),
        ('document_handling', 'Document Handling'),
        ('destruction_process', 'Destruction Process'),
        ('employee_screening', 'Employee Screening'),
        ('facility_security', 'Facility Security'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('audit_requirements', 'Audit Requirements'),
    ], string="Policy Type")
    mandatory = fields.Boolean(string="Mandatory", default=False)
    automated_check = fields.Boolean(string="Automated Check", default=False)
    check_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string="Check Frequency")
    implementation_notes = fields.Text(string="Implementation Notes")
    violation_consequences = fields.Text(string="Violation Consequences")
    review_frequency_months = fields.Integer(string="Review Frequency (Months)", default=12)

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
