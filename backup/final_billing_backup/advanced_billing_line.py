from odoo import models, fields, api, _

class AdvancedBillingLine(models.Model):
    _name = 'advanced.billing.line'
    _description = 'Advanced Billing Line'
    _order = 'sequence, id'

    billing_id = fields.Many2one('advanced.billing', string='Billing', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=False)
    name = fields.Char(string='Description', required=True)
    description = fields.Text(string='Line Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Monetary(string='Unit Price', required=True, default=0.0)
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    price_total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_price_total', store=True)
    amount = fields.Monetary(string='Amount', required=True, default=0.0)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_price_total(self):
        for line in self:
            taxes = line.tax_ids.compute_all(line.price_unit, line.currency_id, line.quantity, product=line.product_id)
            line.price_total = taxes['total_included'] if taxes else line.price_unit * line.quantity
