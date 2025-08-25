from odoo import models, fields, api, _

class AdvancedBillingServiceLine(models.Model):
    _name = 'advanced.billing.service.line'
    _description = 'Advanced Billing Service Line'
    _order = 'sequence, id'

    billing_id = fields.Many2one('advanced.billing', string='Billing', required=True, ondelete='cascade')
    name = fields.Char(string='Service Description', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    subtotal = fields.Monetary(string='Subtotal', related='amount', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
