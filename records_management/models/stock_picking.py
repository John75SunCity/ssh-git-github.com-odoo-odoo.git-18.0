# -*- coding: utf-8 -*-

Temporary Model


from odoo import models, fields, api, _



class StockPicking(models.Model):

        Temporary Model


    _name = "stock.picking.records.extension"
    _description = "Temporary Model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

        # Core fields
    name = fields.Char(string="Name", required=True,,
    tracking=True),
    company_id = fields.Many2one('res.company',,
    default=lambda self: self.env.company),
    user_id = fields.Many2one('res.users',,
    default=lambda self: self.env.user),
    active = fields.Boolean(default=True)

        # Basic state management
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    

        # Common fields
    description = fields.Text(
    notes = fields.Text(
    ,
    date = fields.Date(default=fields.Date.today),
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

    def action_confirm(self):
        """Confirm the record"""

        self.ensure_one()
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""

        self.ensure_one()
        self.write({'state': 'done'})
