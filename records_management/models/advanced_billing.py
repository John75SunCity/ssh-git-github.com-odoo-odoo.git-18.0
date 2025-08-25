# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AdvancedBilling(models.Model):
    _name = 'advanced.billing'
    _description = 'Advanced Billing'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    line_ids = fields.One2many('advanced.billing.line', 'billing_id', string='Lines', copy=True)
    amount_total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_amount_total', store=True)

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('amount'))
