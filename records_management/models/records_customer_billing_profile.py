# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsCustomerBillingProfile(models.Model):
    """Customer Billing Profile for Records Management

    Manages customer-specific billing configurations, payment terms,
    and automated billing preferences for records management services.
    """

    _name = "records.customer.billing.profile"
    _description = "Records Customer Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Profile Name",
        required=True,
        tracking=True,
        help="Name for this billing profile",
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Customer name with billing profile",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER RELATIONSHIP FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer this billing profile applies to",
    )
    billing_contact_ids = fields.One2many(
        "records.billing.contact",
        "customer_billing_profile_id",
        string="Billing Contacts",
    )
    department_id = fields.Many2one(
        "records.department",
        string="Records Department",
        help="Primary records department for this customer",
    )

    # ============================================================================
    # BILLING CONFIGURATION FIELDS
    # ============================================================================
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("on_demand", "On Demand"),
        ],
        string="Billing Frequency",
        default="monthly",
        required=True,
        tracking=True,
    )

    payment_terms = fields.Selection(
        [
            ("net_15", "Net 15"),
            ("net_30", "Net 30"),
            ("net_45", "Net 45"),
            ("net_60", "Net 60"),
            ("prepaid", "Prepaid"),
        ],
        string="Payment Terms",
        default="net_30",
        required=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # ============================================================================
    # SERVICE RATE FIELDS
    # ============================================================================
    use_negotiated_rates = fields.Boolean(
        string="Use Negotiated Rates",
        default=False,
        help="Use customer-specific negotiated rates instead of standard rates",
    )
    storage_rate = fields.Monetary(
        string="Storage Rate per Container",
        currency_field="currency_id",
        help="Monthly storage rate per container",
    )
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate per Request",
        currency_field="currency_id",
        help="Rate per document retrieval request",
    )
    destruction_rate = fields.Monetary(
        string="Destruction Rate per Container",
        currency_field="currency_id",
        help="Rate per container destruction",
    )

    # ============================================================================
    # BILLING AUTOMATION FIELDS
    # ============================================================================
    auto_billing_enabled = fields.Boolean(
        string="Auto Billing Enabled",
        default=True,
        help="Automatically generate invoices based on schedule",
    )
    invoice_delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("mail", "Physical Mail"),
            ("both", "Email and Portal"),
        ],
        string="Invoice Delivery",
        default="email",
        required=True,
    )

    email_template_id = fields.Many2one(
        "mail.template",
        string="Invoice Email Template",
        help="Email template used for invoice delivery",
    )

    # ============================================================================
    # DISCOUNT AND PRICING FIELDS
    # ============================================================================
    volume_discount_enabled = fields.Boolean(
        string="Volume Discount Enabled",
        default=False,
        help="Apply volume discounts based on container count",
    )
    volume_discount_threshold = fields.Integer(
        string="Volume Discount Threshold",
        help="Minimum containers for volume discount",
    )
    volume_discount_percentage = fields.Float(
        string="Volume Discount %",
        help="Percentage discount for volume customers",
    )

    # ============================================================================
    # TRACKING AND AUDIT FIELDS
    # ============================================================================
    created_date = fields.Datetime(
        string="Created Date", default=fields.Datetime.now, readonly=True
    )
    last_invoice_date = fields.Datetime(
        string="Last Invoice Date",
        readonly=True,
        help="Date of last generated invoice",
    )
    total_invoiced = fields.Monetary(
        string="Total Invoiced",
        currency_field="currency_id",
        compute="_compute_invoice_totals",
        store=True,
        help="Total amount invoiced for this customer",
    )
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_invoice_totals", store=True
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("partner_id", "name")
    def _compute_display_name(self):
        """Generate display name from partner and profile name"""
        for record in self:
            if record.partner_id and record.name:
                record.display_name = (
                    f"{record.partner_id.name} - {record.name}"
                )
            else:
                record.display_name = record.name or "New Profile"

    @api.depends("partner_id")
    def _compute_invoice_totals(self):
        """Compute invoice totals for this customer"""
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ]
                )
                record.total_invoiced = sum(invoices.mapped("amount_total"))
                record.invoice_count = len(invoices)
            else:
                record.total_invoiced = 0.0
                record.invoice_count = 0

    # ============================================================================
    # CONSTRAINT VALIDATIONS
    # ============================================================================
    @api.constrains("volume_discount_threshold", "volume_discount_percentage")
    def _check_volume_discount(self):
        """Validate volume discount configuration"""
        for record in self:
            if record.volume_discount_enabled:
                if record.volume_discount_threshold <= 0:
                    raise ValidationError(
                        _("Volume discount threshold must be greater than 0")
                    )
                if not (0 < record.volume_discount_percentage <= 100):
                    raise ValidationError(
                        _(
                            "Volume discount percentage must be between 0 and 100"
                        )
                    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_invoices(self):
        """View invoices for this customer"""
        self.ensure_one()
        return {
            "name": _("Customer Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),
            ],
            "context": {"default_partner_id": self.partner_id.id},
        }

    def action_generate_invoice(self):
        """Generate invoice for this customer"""
        self.ensure_one()
        # Implementation for invoice generation would go here
        # This would integrate with the billing system
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _(
                    "Invoice generation initiated for %s", self.partner_id.name
                ),
                "type": "success",
            },
        }

    def action_duplicate_profile(self):
        """Duplicate this billing profile"""
        self.ensure_one()
        return {
            "name": _("Duplicate Billing Profile"),
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"{self.name} (Copy)",
                "default_partner_id": self.partner_id.id,
                "default_billing_frequency": self.billing_frequency,
                "default_payment_terms": self.payment_terms,
            },
        }
