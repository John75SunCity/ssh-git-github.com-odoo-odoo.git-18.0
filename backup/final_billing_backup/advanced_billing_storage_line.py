from odoo import models, fields, api, _

class AdvancedBillingStorageLine(models.Model):
    _name = 'advanced.billing.storage.line'
    _description = 'Advanced Billing Storage Line'
    _order = 'sequence, id'

    billing_id = fields.Many2one('advanced.billing', string='Billing', required=True, ondelete='cascade')
    name = fields.Char(string='Storage Description', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    subtotal = fields.Monetary(string='Subtotal', related='amount', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
