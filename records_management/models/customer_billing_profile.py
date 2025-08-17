from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class CustomerBillingProfile(models.Model):
    _name = 'customer.billing.profile'
    _description = 'Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Profile Name', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    partner_id = fields.Many2one()
    department_id = fields.Many2one()
    billing_cycle = fields.Selection()
    billing_day = fields.Integer()
    auto_invoice = fields.Boolean()
    auto_generate_service_invoices = fields.Boolean()
    auto_generate_storage_invoices = fields.Boolean()
    auto_send_invoices = fields.Boolean()
    auto_send_statements = fields.Boolean()
    service_billing_cycle = fields.Selection()
    storage_billing_cycle = fields.Selection()
    storage_bill_in_advance = fields.Boolean()
    storage_advance_months = fields.Integer()
    invoice_due_days = fields.Integer()
    prepaid_months = fields.Integer()
    invoice_template_id = fields.Many2one()
    credit_limit = fields.Monetary()
    payment_terms_id = fields.Many2one('account.payment.term')
    payment_reliability_score = fields.Float()
    currency_id = fields.Many2one()
    prepaid_enabled = fields.Boolean()
    prepaid_balance = fields.Monetary()
    prepaid_discount_percent = fields.Float()
    minimum_prepaid_amount = fields.Monetary()
    send_invoices_by_email = fields.Boolean()
    invoice_email = fields.Char()
    late_payment_notification = fields.Boolean()
    notification_days = fields.Integer()
    billing_contact_ids = fields.One2many()
    contact_count = fields.Integer()
    invoice_ids = fields.One2many()
    prepaid_payment_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    action_activate = fields.Char(string='Action Activate')
    action_reactivate = fields.Char(string='Action Reactivate')
    action_suspend = fields.Char(string='Action Suspend')
    action_terminate = fields.Char(string='Action Terminate')
    automation = fields.Char(string='Automation')
    billing_contacts = fields.Char(string='Billing Contacts')
    billing_profile_id = fields.Many2one('billing.profile')
    billing_schedule = fields.Char(string='Billing Schedule')
    description = fields.Char(string='Description')
    draft = fields.Char(string='Draft')
    email = fields.Char(string='Email')
    group_customer = fields.Char(string='Group Customer')
    group_state = fields.Selection(string='Group State')
    group_storage_cycle = fields.Char(string='Group Storage Cycle')
    help = fields.Char(string='Help')
    monthly_storage = fields.Char(string='Monthly Storage')
    next_storage_billing_date = fields.Date(string='Next Storage Billing Date')
    payment_term_id = fields.Many2one('payment.term')
    phone = fields.Char(string='Phone')
    prepaid = fields.Char(string='Prepaid')
    primary_contact = fields.Char(string='Primary Contact')
    quarterly_storage = fields.Char(string='Quarterly Storage')
    receive_notifications = fields.Char(string='Receive Notifications')
    receive_service_invoices = fields.Char(string='Receive Service Invoices')
    receive_statements = fields.Char(string='Receive Statements')
    receive_storage_invoices = fields.Char(string='Receive Storage Invoices')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    service_billing = fields.Char(string='Service Billing')
    storage_billing = fields.Char(string='Storage Billing')
    suspended = fields.Char(string='Suspended')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_contact_count(self):
            """Calculate number of billing contacts"""
            for record in self:
                record.contact_count = len(record.billing_contact_ids)


    def _compute_prepaid_balance(self):
            """Calculate current prepaid balance"""
            for record in self:
                total_payments = sum(record.prepaid_payment_ids.mapped("amount"))
                # Subtract consumed amounts (this would need additional logic)
                record.prepaid_balance = total_payments


    def _compute_payment_reliability_score(self):
            """Calculate payment reliability score based on history"""
            for record in self:
                if not record.partner_id:
                    record.payment_reliability_score = 0.0
                    continue

                # This is a simplified calculation - in practice would analyze
                # payment history, late payments, defaults, etc.
                invoices = self.env["account.move").search(]
                    []
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),



                if not invoices:
                    record.payment_reliability_score = 50.0  # Neutral score
                    continue

                paid_on_time = invoices.filtered(lambda inv: inv.payment_state == "paid")
                score = (len(paid_on_time) / len(invoices)) * 100
                record.payment_reliability_score = min(100.0, max(0.0, score))

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate_profile(self):
            """Activate billing profile"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Can only activate draft profiles"))
            self.write({"state": "active"})


    def action_suspend_profile(self):
            """Suspend billing profile"""

            self.ensure_one()
            if self.state != "active":
                raise UserError(_("Can only suspend active profiles"))
            self.write({"state": "suspended"})


    def action_reactivate_profile(self):
            """Reactivate suspended profile"""

            self.ensure_one()
            if self.state != "suspended":
                raise UserError(_("Can only reactivate suspended profiles"))
            self.write({"state": "active"})


    def action_generate_invoice(self):
            """Generate invoice based on billing profile configuration"""

            self.ensure_one()
            if self.state != "active":
                raise UserError(_("Can only generate invoices for active profiles")):
            # Create invoice based on profile settings
            invoice_vals = self._prepare_invoice_values()
            invoice = self.env["account.move"].create(invoice_vals)

            return {}
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": invoice.id,
                "view_mode": "form",
                "target": "current",



    def action_view_invoices(self):
            """View all invoices for this billing profile""":
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Invoices"),
                "res_model": "account.move",
                "view_mode": "tree,form",
                "domain": [("billing_profile_id", "=", self.id)],
                "context": {"default_billing_profile_id": self.id},


        # ============================================================================
            # PRIVATE METHODS
        # ============================================================================

    def _prepare_invoice_values(self):
            """Prepare values for invoice creation""":
            self.ensure_one()
            return {}
                "partner_id": self.partner_id.id,
                "billing_profile_id": self.id,
                "payment_term_id": ()
                    self.payment_terms_id.id if self.payment_terms_id else False:

                "currency_id": self.currency_id.id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.today(),


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_billing_day(self):
            """Validate billing day is within valid range"""
            for record in self:
                if not (1 <= record.billing_day <= 28):
                    raise ValidationError(_("Billing day must be between 1 and 28"))


    def _check_credit_limit(self):
            """Validate credit limit is positive"""
            for record in self:
                if record.credit_limit < 0:
                    raise ValidationError(_("Credit limit must be positive"))


    def _check_prepaid_discount(self):
            """Validate prepaid discount percentage"""
            for record in self:
                if not (0 <= record.prepaid_discount_percent <= 100):
                    raise ValidationError(_("Prepaid discount must be between 0 and 100%"))

