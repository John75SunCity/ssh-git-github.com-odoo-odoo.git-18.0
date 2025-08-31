# -*- coding: utf-8 -*-
"""
Records Billing Model

Core billing model for Records Management system that handles
billing records, configurations, and financial tracking.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBilling(models.Model):
    """
    Records Billing Model

    Main billing model that manages billing records, configurations,
    and financial tracking for the Records Management system.
    """

    _name = "records.billing"
    _description = "Records Billing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    # Basic Information
    name = fields.Char(
        string="Billing Reference", required=True, copy=False, readonly=True, index=True, default=lambda self: _("New")
    )

    date = fields.Date(string="Billing Date", required=True, default=fields.Date.context_today, index=True)

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company, index=True
    )

    partner_id = fields.Many2one("res.partner", string="Customer", required=True, index=True)

    # Billing Configuration
    billing_config_id = fields.Many2one("records.billing.config", string="Billing Configuration", required=True)

    # Financial Information
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id
    )

    amount_total = fields.Monetary(
        string="Total Amount", currency_field="currency_id", compute="_compute_amount_total", store=True
    )

    amount_tax = fields.Monetary(
        string="Tax Amount", currency_field="currency_id", compute="_compute_amount_total", store=True
    )

    amount_untaxed = fields.Monetary(
        string="Untaxed Amount", currency_field="currency_id", compute="_compute_amount_total", store=True
    )

    # Status and State
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("billed", "Billed"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # Related Records
    billing_line_ids = fields.One2many("records.billing.line", "billing_id", string="Billing Lines")

    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)

    # Additional Information
    notes = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("records.billing") or _("New")
        return super().create(vals_list)

    @api.depends("billing_line_ids.price_subtotal", "billing_line_ids.price_tax")
    def _compute_amount_total(self):
        for record in self:
            lines = record.billing_line_ids
            record.amount_untaxed = sum(lines.mapped("price_subtotal"))
            record.amount_tax = sum(lines.mapped("price_tax"))
            record.amount_total = record.amount_untaxed + record.amount_tax

    def action_confirm(self):
        """Confirm the billing record"""
        self.ensure_one()
        self.write({"state": "confirmed"})

    def action_cancel(self):
        """Cancel the billing record"""
        self.ensure_one()
        self.write({"state": "cancelled"})

    def action_create_invoice(self):
        """Create invoice from billing record"""
        self.ensure_one()
        # Implementation for invoice creation
        pass
