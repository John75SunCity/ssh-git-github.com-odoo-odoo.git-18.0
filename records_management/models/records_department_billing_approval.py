# -*- coding: utf-8 -*-
from odoo import models, fields


class RecordsDepartmentBillingApproval(models.Model):
    _name = 'records.department.billing.approval'
    _description = 'Department Billing Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'approval_date desc'

    billing_contact_id = fields.Many2one(
        comodel_name='records.department.billing.contact',
        string='Billing Contact',
        required=True,
        ondelete='cascade'
    )
    approval_date = fields.Datetime(string='Approval Date', default=fields.Datetime.now)
    charge_amount = fields.Monetary(string='Charge Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    service_description = fields.Char(string='Service Description')
    vendor = fields.Char(string='Vendor')
    approval_notes = fields.Text(string='Notes')
