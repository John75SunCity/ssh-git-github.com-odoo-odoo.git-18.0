# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PaymentSplit(models.Model):
    _name = "payment.split"
    _description = "Payment Split"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "split_date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Split Reference", required=True, tracking=True, index=True
    ),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    ),
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # SPLIT DETAILS
    # ============================================================================
    split_date = fields.Datetime(
        string="Split Date", default=fields.Datetime.now, required=True, index=True
    ),
    original_amount = fields.Monetary(
        string="Original Amount", required=True, tracking=True)
    split_amount = fields.Monetary(string="Split Amount", required=True, tracking=True),
    remaining_amount = fields.Monetary(
        string="Remaining Amount", compute="_compute_remaining_amount", store=True
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id, required=True
    )

    # ============================================================================
    # SPLIT CONFIGURATION
    # ============================================================================
    split_type = fields.Selection(
        [
            ("percentage", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("equal", "Equal Split"),
            ("custom", "Custom"),
        ]),
        string="Split Type",
        default="fixed",
        required=True,
        tracking=True,
    )
    split_percentage = fields.Float(string="Split Percentage", digits=(5, 2)
    split_reason = fields.Text(string="Split Reason", tracking=True)

    # ============================================================================
    # PAYMENT DETAILS
    # ============================================================================
    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("card", "Card"),
            ("bank", "Bank Transfer"),
            ("check", "Check"),
            ("digital", "Digital Payment"),
            ("other", "Other"),
        ]),
        string="Payment Method",
        default="cash",
        tracking=True,
    )
    payment_ref = fields.Char(string="Payment Reference")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Note: Removed pos_wizard_id field - Model to TransientModel relationships are forbidden
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)

    # ============================================================================
    # STATUS FIELDS
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("processed", "Processed"),
            ("cancelled", "Cancelled"),
        ]),
        string="Status",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("original_amount", "split_amount")
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.original_amount - record.split_amount

    @api.depends("name", "split_amount", "currency_id")
    def _compute_display_name(self):
        for record in self:
            if record.name and record.split_amount:
                amount_str = f"{record.split_amount} {record.currency_id.symbol or ''}"
                record.display_name = f"{record.name} - {amount_str}"
            else:
                record.display_name = record.name or "Payment Split"

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("split_amount", "original_amount")
    def _check_split_amount(self):
        for record in self:
            if record.split_amount > record.original_amount:
                raise models.ValidationError(
                    "Split amount cannot be greater than original amount."
                )
            if record.split_amount <= 0:
                raise models.ValidationError("Split amount must be greater than zero.")

    @api.constrains("split_percentage")
    def _check_split_percentage(self):
        for record in self:
            if record.split_type == "percentage":
                if not (0 < record.split_percentage <= 100):
                    raise models.ValidationError(
                        "Split percentage must be between 0 and 100."
                    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the payment split"""
        self.write({"state": "confirmed"})

    def action_process(self):
        """Process the payment split"""
        self.write({"state": "processed"})

    def action_cancel(self):
        """Cancel the payment split"""
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.write({"state": "draft"})