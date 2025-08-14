# -*- coding: utf-8 -*-
# Records Usage Tracking Model

from odoo import fields, models




class RecordsUsageTracking(models.Model):
    """Usage tracking for billing configuration"""

    _name = "records.usage.tracking"
    _description = "Records Usage Tracking"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _('New'),
        help='Unique identifier for this record'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide this record'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company this record belongs to'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.usage.tracking') or _('New')
        return super().create(vals_list)
    _order = "config_id, date desc"

    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    )
    date = fields.Date(string="Usage Date", required=True, default=fields.Date.today)
    service_type = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("scanning", "Scanning"),
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
        ],
        string="Service Type",
        required=True,
    )
    quantity = fields.Float(string="Quantity", digits=(10, 2), required=True)
    unit = fields.Char(string="Unit of Measure", default="boxes")
    cost = fields.Monetary(string="Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    notes = fields.Text(string="Notes")
