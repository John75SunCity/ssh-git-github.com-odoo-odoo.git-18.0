# -*- coding: utf-8 -*-
"""
Advanced Billing Module

See RECORDS_MANAGEMENT_SYSTEM_MANUAL.md - Section 6: Advanced Billing Period Management Module
for comprehensive documentation, business processes, and integration details.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

# Standard Odoo imports with development environment handling
try:
    from odoo import api, fields, models, _
    from odoo.exceptions import ValidationError
except ImportError:
    # Development environment fallback
    api = fields = models = None
    ValidationError = Exception
    _ = lambda x, *args, **kwargs: x % args if args else x


class AdvancedBilling(models.Model):
    _name = "advanced.billing"
    _description = "Advanced Billing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # BILLING FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    billing_period_id = fields.Many2one(
        "records.advanced.billing.period",
        string="Billing Period",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    invoice_id = fields.Many2one(
        "account.move", string="Invoice", tracking=True
    )
    payment_terms = fields.Selection(
        [
            ("immediate", "Immediate Payment"),
            ("net_15", "Net 15 Days"),
            ("net_30", "Net 30 Days"),
            ("net_45", "Net 45 Days"),
            ("net_60", "Net 60 Days"),
            ("custom", "Custom Terms"),
        ],
        string="Payment Terms",
        default="net_30",
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("invoiced", "Invoiced"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    line_ids = fields.One2many(
        "records.billing.line", "billing_id", string="Billing Lines"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    total_amount = fields.Monetary(
        string="Total Amount",
        compute="_compute_total_amount",
        store=True,
        currency_field="currency_id",
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("line_ids.price_total")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped("price_total"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm billing"""

        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft billing can be confirmed"))

        self.write({"state": "confirmed"})
        self.message_post(body=_("Advanced billing confirmed"))

    def action_generate_invoice(self):
        """Generate invoice"""

        self.ensure_one()
        if self.state != "confirmed":
            raise ValidationError(_("Only confirmed billing can be invoiced"))

        # Create invoice from billing lines
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in self.line_ids],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            "state": "invoiced",
            "invoice_id": invoice.id,
        })

        self.message_post(body=_("Invoice generated: %s") % invoice.name)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        """Mark billing as done"""

        self.ensure_one()
        if self.state != "invoiced":
            raise ValidationError(_("Only invoiced billing can be marked as done"))

        self.write({"state": "done"})
        self.message_post(body=_("Advanced billing completed"))

    def action_cancel(self):
        """Cancel billing"""

        self.ensure_one()
        if self.state in ["invoiced", "done"]:
            raise ValidationError(_("Cannot cancel invoiced or completed billing"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Advanced billing cancelled"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("total_amount")
    def _check_total_amount(self):
        for record in self:
            if record.total_amount < 0:
                raise ValidationError(_("Total amount cannot be negative"))
