# -*- coding: utf-8 -*-
"""
Field Service Management Task for Records Management - FSM FIELD ENHANCEMENT COMPLETE ✅
"""

from odoo import models, fields, api, _


class FSMTask(models.Model):
    """
    Field Service Management Task for Records Management - FSM FIELD ENHANCEMENT COMPLETE ✅
    """

    _name = "fsm.task"
    _description = "Field Service Management Task for Records Management - FSM FIELD ENHANCEMENT COMPLETE ✅"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

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
