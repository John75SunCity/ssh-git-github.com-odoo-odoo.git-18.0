# -*- coding: utf-8 -*-
"""
Records Container Transfer Log
"""

from odoo import models, fields, api, _



class RecordsContainerTransfer(models.Model):
    """
    Records Container Transfer Log
    """

    _name = "records.container.transfer"
    _description = "Records Container Transfer Log"
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

        self.ensure_one()
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""

        self.ensure_one()
        self.write({'state': 'done'})
