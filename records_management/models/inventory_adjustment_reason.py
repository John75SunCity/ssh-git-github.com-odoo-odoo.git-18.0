from odoo import models, fields

class InventoryAdjustmentReason(models.Model):
    _name = 'inventory.adjustment.reason'
    _description = 'Inventory Adjustment Reason'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reason', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
