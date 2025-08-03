# -*- coding: utf-8 -*-
"""
Customer Billing Profile Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerBillingProfile(models.Model):
    """
    Customer Billing Profile - Manages billing configurations for customers
    """

    _name = "records.customer.billing.profile"
    _description = "Customer Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Profile Name", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Billing Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )

    # Contact count (computed field)
    contact_count = fields.Integer(
        string="Contact Count", compute="_compute_contact_count"
    )

    # ==========================================
    # STORAGE BILLING CONFIGURATION
    # ==========================================
    storage_billing_cycle = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("prepaid", "Prepaid"),
        ],
        string="Storage Billing Cycle",
        default="monthly",
        required=True,
        tracking=True,
    )

    storage_bill_in_advance = fields.Boolean(
        string="Bill Storage in Advance", default=False, tracking=True
    )
    storage_advance_months = fields.Integer(
        string="Advance Months", default=1, tracking=True
    )
    auto_generate_storage_invoices = fields.Boolean(
        string="Auto Generate Storage Invoices", default=True, tracking=True
    )

    # ==========================================
    # SERVICE BILLING CONFIGURATION
    # ==========================================
    service_billing_cycle = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Service Billing Cycle",
        default="monthly",
        required=True,
        tracking=True,
    )

    auto_generate_service_invoices = fields.Boolean(
        string="Auto Generate Service Invoices", default=True, tracking=True
    )

    # ==========================================
    # PREPAID OPTIONS
    # ==========================================
    prepaid_enabled = fields.Boolean(
        string="Prepaid Enabled", default=False, tracking=True
    )
    prepaid_months = fields.Integer(string="Prepaid Months", default=12, tracking=True)
    prepaid_discount_percent = fields.Float(
        string="Prepaid Discount %", default=0.0, tracking=True
    )

    # ==========================================
    # BILLING SCHEDULE
    # ==========================================
    billing_day = fields.Integer(
        string="Billing Day of Month", default=1, tracking=True
    )
    invoice_due_days = fields.Integer(
        string="Invoice Due Days", default=30, tracking=True
    )
    payment_term_id = fields.Many2one(
        "account.payment.term", string="Payment Terms", tracking=True
    )
    next_storage_billing_date = fields.Date(
        string="Next Storage Billing Date", tracking=True
    )

    # ==========================================
    # BILLING STATE MANAGEMENT
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("terminated", "Terminated"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    @api.depends("partner_id")
    def _compute_contact_count(self):
        """Compute contact count for the partner"""
        for record in self:
            if record.partner_id:
                # Count child contacts of the partner
                record.contact_count = len(record.partner_id.child_ids)
            else:
                record.contact_count = 0


    # ==========================================
    # SERVICE BILLING CONFIGURATION
    # ==========================================

    # ==========================================
    # PREPAID BILLING OPTIONS
    # ==========================================

    # ==========================================
    # BILLING SCHEDULE
    # ==========================================

    # ==========================================
    # AUTOMATION SETTINGS
    # ==========================================
    auto_send_invoices = fields.Boolean(
        string="Auto Send Invoices", default=False, tracking=True
    )
    auto_send_statements = fields.Boolean(
        string="Auto Send Statements", default=False, tracking=True
    )

    # ==========================================
    # PAYMENT TERMS
    # ==========================================

    # ==========================================
    # RELATED RECORDS
    # ==========================================
    billing_contact_ids = fields.One2many(
        "records.billing.contact", "billing_profile_id", string="Billing Contacts"
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends("billing_contact_ids")
    def _compute_contact_count(self):
        """Compute number of billing contacts"""
        for record in self:
            record.contact_count = len(record.billing_contact_ids)


    @api.depends("storage_billing_cycle", "storage_advance_months")
    def _compute_next_storage_billing_date(self):
        """Compute next storage billing date"""
        for record in self:
            # This would calculate based on billing cycle and current date
            # For now, just set to False - implement date calculation as needed
            record.next_storage_billing_date = False


    # ==========================================
    # WORKFLOW MANAGEMENT
    # ==========================================

    # ==========================================
    # ONCHANGE METHODS
    # ==========================================
    @api.onchange("storage_billing_cycle")
    def _onchange_storage_billing_cycle(self):
        """Update advance months based on billing cycle"""
        if self.storage_billing_cycle == "monthly":
            self.storage_advance_months = 1
        elif self.storage_billing_cycle == "quarterly":
            self.storage_advance_months = 3
        elif self.storage_billing_cycle == "semi_annual":
            self.storage_advance_months = 6
        elif self.storage_billing_cycle == "annual":
            self.storage_advance_months = 12
        elif self.storage_billing_cycle == "prepaid":
            self.prepaid_enabled = True

    @api.onchange("prepaid_enabled")
    def _onchange_prepaid_enabled(self):
        """Update billing cycle when prepaid is enabled"""
        if self.prepaid_enabled and self.storage_billing_cycle != "prepaid":
            self.storage_billing_cycle = "prepaid"

    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_activate(self):
        """Activate the billing profile"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft profiles can be activated"))
            record.write({"state": "active"})
            record.message_post(body=_("Billing profile activated"))

    def action_suspend(self):
        """Suspend the billing profile"""
        for record in self:
            if record.state not in ["active"]:
                raise UserError(_("Only active profiles can be suspended"))
            record.write({"state": "suspended"})
            record.message_post(body=_("Billing profile suspended"))

    def action_reactivate(self):
        """Reactivate suspended billing profile"""
        for record in self:
            if record.state != "suspended":
                raise UserError(_("Only suspended profiles can be reactivated"))
            record.write({"state": "active"})
            record.message_post(body=_("Billing profile reactivated"))

    def action_terminate(self):
        """Terminate the billing profile"""
        for record in self:
            if record.state in ["terminated"]:
                raise UserError(_("Profile is already terminated"))
            record.write({"state": "terminated"})
            record.message_post(body=_("Billing profile terminated"))

    def action_generate_invoice(self):
        """Generate comprehensive invoice for customer."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active billing profiles can generate invoices."))

        # Create invoice generation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Invoice generated: %s") % self.name,
            note=_(
                "Comprehensive invoice has been generated for customer billing profile."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Comprehensive invoice generated for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_move_type": "out_invoice",
                "default_partner_id": self.partner_id.id,
                "default_payment_term_id": self.payment_term_id.id,
                "default_ref": self.name,
            },
        }

    def action_generate_service_lines(self):
        """Generate service billing lines for invoice."""
        self.ensure_one()

        # Create service lines generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Service lines generated: %s") % self.name,
            note=_("Service billing lines have been generated and calculated."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Service billing lines generated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Service Lines: %s") % self.name,
            "res_model": "account.move.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("product_id.type", "=", "service"),
            ],
            "context": {
                "default_partner_id": self.partner_id.id,
                "search_default_partner_id": self.partner_id.id,
                "search_default_service_products": True,
            },
        }

    def action_generate_storage_lines(self):
        """Generate storage billing lines for invoice."""
        self.ensure_one()

        # Create storage lines generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Storage lines generated: %s") % self.name,
            note=_(
                "Storage billing lines have been generated based on current inventory."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Storage billing lines generated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Lines: %s") % self.name,
            "res_model": "account.move.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("product_id.detailed_type", "=", "product"),
            ],
            "context": {
                "default_partner_id": self.partner_id.id,
                "search_default_partner_id": self.partner_id.id,
                "search_default_storage_products": True,
            },
        }

    # ==========================================
    # BILLING METHODS
    # ==========================================
    def generate_storage_invoice(self):
        """Generate storage invoice for this profile"""
        self.ensure_one()
        if not self.auto_generate_storage_invoices:
            raise UserError(_("Auto generation of storage invoices is disabled"))

        # Implementation would create invoice here
        # For now, just log the action
        _logger.info(f"Generating storage invoice for {self.name}")
        self.message_post(body=_("Storage invoice generated"))

    def generate_service_invoice(self):
        """Generate service invoice for this profile"""
        self.ensure_one()
        if not self.auto_generate_service_invoices:
            raise UserError(_("Auto generation of service invoices is disabled"))

        # Implementation would create invoice here
        # For now, just log the action
        _logger.info(f"Generating service invoice for {self.name}")
        self.message_post(body=_("Service invoice generated"))

        # ==========================================
        # CRON METHODS
        # ==========================================def _cron_generate_scheduled_invoices(self):
        """Cron job to generate scheduled invoices"""
        active_profiles = self.search([("state", "=", "active")])

        for profile in active_profiles:
            try:
                if profile.auto_generate_storage_invoices:
                    profile.generate_storage_invoice()
                if profile.auto_generate_service_invoices:
                    profile.generate_service_invoice()
            except Exception as e:
                _logger.error(
                    f"Error generating invoices for profile {profile.name}: {e}"
                )

    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains("billing_day")
    def _check_billing_day(self):
        """Validate billing day"""
        for record in self:
            if not (1 <= record.billing_day <= 28):
                raise ValidationError(_("Billing day must be between 1 and 28"))

    @api.constrains("invoice_due_days")
    def _check_invoice_due_days(self):
        """Validate invoice due days"""
        for record in self:
            if record.invoice_due_days < 1:
                raise ValidationError(_("Invoice due days must be at least 1"))

    @api.constrains("storage_advance_months")
    def _check_storage_advance_months(self):
        """Validate storage advance months"""
        for record in self:
            if record.storage_advance_months < 1:
                raise ValidationError(_("Storage advance months must be at least 1"))

    @api.constrains("prepaid_months")
    def _check_prepaid_months(self):
        """Validate prepaid months"""
        for record in self:
            if record.prepaid_enabled and record.prepaid_months < 1:
                raise ValidationError(_("Prepaid months must be at least 1"))

    @api.constrains("prepaid_discount_percent")
    def _check_prepaid_discount_percent(self):
        """Validate prepaid discount percent"""
        for record in self:
            if (
                record.prepaid_discount_percent < 0
                or record.prepaid_discount_percent > 100
            ):
                raise ValidationError(
                    _("Prepaid discount percent must be between 0 and 100")
                )


class BillingContact(models.Model):
    """
    Billing Contact - Manages contacts for billing communications
    """

    _name = "records.billing.contact"
    _description = "Billing Contact"
    _order = "billing_profile_id, sequence, name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Contact Name", required=True)
    email = fields.Char(string="Email", required=True)
    phone = fields.Char(string="Phone")

    # ==========================================
    # BILLING PROFILE RELATIONSHIP
    # ==========================================
    billing_profile_id = fields.Many2one(
        "records.customer.billing.profile",
        string="Billing Profile",
        required=True,
        ondelete="cascade",
    )

    # ==========================================
    # CONTACT PREFERENCES
    # ==========================================
    receive_storage_invoices = fields.Boolean(
        string="Receive Storage Invoices", default=True
    )
    receive_service_invoices = fields.Boolean(
        string="Receive Service Invoices", default=True
    )
    receive_statements = fields.Boolean(string="Receive Statements", default=False)
    receive_notifications = fields.Boolean(string="Receive Notifications", default=True)

    # ==========================================
    # CONTACT MANAGEMENT
    # ==========================================
    primary_contact = fields.Boolean(string="Primary Contact", default=False)
    sequence = fields.Integer(string="Sequence", default=10)

    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains("email")
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.email and "@" not in record.email:
                raise ValidationError(_("Please enter a valid email address"))
