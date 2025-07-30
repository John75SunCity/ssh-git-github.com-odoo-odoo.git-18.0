# -*- coding: utf-8 -*-
"""
Records Department
"""

from odoo import models, fields, api, _


class RecordsDepartment(models.Model):
    """
    Records Department Management
    Organizational departments for records management
    """

    _name = "records.department"
    _description = "Records Department"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Department Name", required=True, tracking=True)
    code = fields.Char(string="Department Code", required=True, tracking=True)
    description = fields.Text(string="Department Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Created By', 
                            default=lambda self: self.env.user, tracking=True)

    # ==========================================
    # PARENT ORGANIZATION
    # ==========================================
    partner_id = fields.Many2one('res.partner', string='Organization', 
                                tracking=True,
                                domain=[('is_company', '=', True)],
                                help="Parent organization that owns this department")

    # ==========================================
    # DEPARTMENT MANAGEMENT
    # ==========================================
    department_manager_id = fields.Many2one('res.users', string='Department Manager', tracking=True)
    records_coordinator_id = fields.Many2one('res.users', string='Records Coordinator', tracking=True)

    # ==========================================
    # CONTACT INFORMATION
    # ==========================================
    email = fields.Char(string='Department Email', tracking=True)
    phone = fields.Char(string='Department Phone', tracking=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='State', default='draft', tracking=True)

    # Common fields
    notes = fields.Text(string="Notes")
    date = fields.Date(default=fields.Date.today)

    # ==========================================
    # CONSTRAINTS
    # ==========================================
    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)', 'Department code must be unique per company!'),
    ]

    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_confirm(self):
        """Activate the department"""
        self.write({'state': 'active'})

    def action_deactivate(self):
        """Deactivate the department"""
        self.write({'state': 'inactive'})
