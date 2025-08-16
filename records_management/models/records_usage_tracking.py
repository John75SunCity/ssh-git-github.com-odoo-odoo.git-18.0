# -*- coding: utf-8 -*-
# Records Usage Tracking Model

from odoo import api, fields, models, _




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
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )
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

    # ============================================================================
    # BUSINESS FIELDS
    # ============================================================================
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
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')
