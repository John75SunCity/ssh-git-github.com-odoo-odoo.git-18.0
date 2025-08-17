from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsCustomerBillingProfile(models.Model):
    _name = 'records.customer.billing.profile'
    _description = 'Records Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    billing_contact_ids = fields.One2many()
    department_id = fields.Many2one()
    billing_frequency = fields.Selection()
    payment_terms = fields.Selection()
    currency_id = fields.Many2one()
    use_negotiated_rates = fields.Boolean()
    storage_rate = fields.Monetary()
    retrieval_rate = fields.Monetary()
    destruction_rate = fields.Monetary()
    pickup_rate = fields.Monetary()
    delivery_rate = fields.Monetary()
    type01_storage_rate = fields.Monetary()
    type02_storage_rate = fields.Monetary()
    type03_storage_rate = fields.Monetary()
    type04_storage_rate = fields.Monetary()
    type06_storage_rate = fields.Monetary()
    auto_billing_enabled = fields.Boolean()
    invoice_delivery_method = fields.Selection()
    email_template_id = fields.Many2one()
    billing_contact_email = fields.Char()
    billing_cycle_day = fields.Integer()
    volume_discount_enabled = fields.Boolean()
    volume_discount_threshold = fields.Integer()
    volume_discount_percentage = fields.Float()
    early_payment_discount = fields.Float()
    early_payment_days = fields.Integer()
    minimum_monthly_charge = fields.Monetary()
    created_date = fields.Datetime()
    last_invoice_date = fields.Datetime()
    next_billing_date = fields.Date()
    total_invoiced = fields.Monetary()
    invoice_count = fields.Integer()
    average_monthly_revenue = fields.Monetary()
    last_payment_date = fields.Date()
    payment_status = fields.Selection()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    base_date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Generate display name from partner and profile name"""
            for record in self:
                if record.partner_id and record.name:
                    record.display_name = _("%s - %s", record.partner_id.name, record.name)
                else:
                    record.display_name = record.name or _("New Profile")


    def _compute_invoice_totals(self):
            """Compute invoice totals for this customer""":
            for record in self:
                if record.partner_id:
                    invoices = self.env["account.move").search([)]
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),

                    record.total_invoiced = sum(invoices.mapped("amount_total"))
                    record.invoice_count = len(invoices)
                else:
                    record.total_invoiced = 0.0
                    record.invoice_count = 0


    def _compute_next_billing_date(self):
            """Calculate next billing date based on frequency"""
            from datetime import timedelta
            from dateutil.relativedelta import relativedelta

            for record in self:
                if not record.last_invoice_date:
                    # First billing - use today

    def _compute_revenue_metrics(self):
            """Calculate revenue analytics"""
            from dateutil.relativedelta import relativedelta

            for record in self:
                if record.created_date and record.total_invoiced:
                    months_active = relativedelta(fields.Date.today(), record.created_date.date()).months + 1
                    if months_active > 0:
                        record.average_monthly_revenue = record.total_invoiced / months_active
                    else:
                        record.average_monthly_revenue = 0.0
                else:
                    record.average_monthly_revenue = 0.0


    def _compute_payment_metrics(self):
            """Calculate payment status and metrics"""
            for record in self:
                if record.partner_id:
                    # Get most recent payment
                    payments = self.env["account.payment"].search([)]
                        ("partner_id", "=", record.partner_id.id),
                        ("state", "=", "posted"),


                    record.last_payment_date = payments[0].date if payments else False:
                    # Calculate payment status based on overdue invoices
                    overdue_invoices = self.env["account.move"].search([)]
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("payment_state", "in", ["not_paid", "partial"]),
                        ("invoice_date_due", "<", fields.Date.today()),


                    if not overdue_invoices:
                        record.payment_status = "current"
                    else:
                        days_overdue = max([)]
                            (fields.Date.today() - inv.invoice_date_due).days
                            for inv in overdue_invoices:


                        if days_overdue >= 60:
                            record.payment_status = "overdue_60"
                        elif days_overdue >= 30:
                            record.payment_status = "overdue_30"
                        elif days_overdue >= 15:
                            record.payment_status = "overdue_15"
                        else:
                            record.payment_status = "current"
                else:
                    record.last_payment_date = False
                    record.payment_status = "current"

        # ============================================================================
            # CONSTRAINT VALIDATIONS
        # ============================================================================

    def _check_volume_discount(self):
            """Validate volume discount configuration"""
            for record in self:
                if record.volume_discount_enabled:
                    if record.volume_discount_threshold <= 0:
                        raise ValidationError(_("Volume discount threshold must be greater than 0"))
                    if not (0 < record.volume_discount_percentage <= 100):
                        raise ValidationError(_("Volume discount percentage must be between 0 and 100"))


    def _check_early_payment_discount(self):
            """Validate early payment discount configuration"""
            for record in self:
                if record.early_payment_discount > 0:
                    if record.early_payment_days <= 0:
                        raise ValidationError(_("Early payment days must be greater than 0"))
                    if record.early_payment_discount > 25:
                        raise ValidationError(_("Early payment discount cannot exceed 25%"))


    def _check_billing_cycle_day(self):
            """Validate billing cycle day"""
            for record in self:
                if not (1 <= record.billing_cycle_day <= 31):
                    raise ValidationError(_("Billing cycle day must be between 1 and 31"))


    def _check_unique_active_profile(self):
            """Ensure only one active profile per customer"""
            for record in self:
                if record.state == 'active':
                    existing = self.search([)]
                        ("partner_id", "=", record.partner_id.id),
                        ("state", "=", "active"),
                        ("id", "!=", record.id)

                    if existing:
                        raise ValidationError(_("Customer %s already has an active billing profile", record.partner_id.name))

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_view_invoices(self):
            """View invoices for this customer""":
            self.ensure_one()
            return {}
                "name": _("Customer Invoices"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "view_mode": "tree,form",
                "domain": []
                    ("partner_id", "=", self.partner_id.id),
                    ("move_type", "=", "out_invoice"),

                "context": {"default_partner_id": self.partner_id.id},



    def action_generate_invoice(self):
            """Generate invoice for this customer""":
            self.ensure_one()

            # Create billing record
            billing_vals = {}
                'partner_id': self.partner_id.id,
                'billing_profile_id': self.id,
                'billing_date': fields.Date.today(),
                'state': 'draft',


            billing_record = self.env['records.billing'].create(billing_vals)

            # Update last invoice date
            self.write({'last_invoice_date': fields.Datetime.now()})

            return {}
                "type": "ir.actions.act_window",
                "name": _("Generated Invoice"),
                "res_model": "records.billing",
                "res_id": billing_record.id,
                "view_mode": "form",
                "target": "current",



    def action_duplicate_profile(self):
            """Duplicate this billing profile"""
            self.ensure_one()

            copy_vals = {}
                'name': _("%s (Copy)", self.name),
                'partner_id': False,  # Clear partner to allow selection
                'state': 'draft',
                'active': False,  # Start inactive


            new_profile = self.copy(copy_vals)

            return {}
                "name": _("Duplicate Billing Profile"),
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": new_profile.id,
                "view_mode": "form",
                "target": "current",



    def action_activate_profile(self):
            """Activate billing profile"""
            for record in self:
                # Check for existing active profiles:
                existing_active = self.search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id)


                if existing_active:
                    # Suspend existing active profile
                    existing_active.write({"state": "suspended"})

                record.write({"state": "active"})
                record.message_post(body=_("Billing profile activated"))


    def action_suspend_profile(self):
            """Suspend billing profile"""
            for record in self:
                record.write({"state": "suspended"})
                record.message_post(body=_("Billing profile suspended"))


    def action_terminate_profile(self):
            """Terminate billing profile"""
            for record in self:
                if record.invoice_count > 0:
                    # Check for unpaid invoices:
                    unpaid_invoices = self.env["account.move"].search([)]
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("payment_state", "in", ["not_paid", "partial"]),


                    if unpaid_invoices:
                        raise UserError(_("Cannot terminate profile with unpaid invoices"))

                record.write({"state": "terminated"})
                record.message_post(body=_("Billing profile terminated"))


    def action_test_billing_configuration(self):
            """Test billing configuration"""
            self.ensure_one()

            # Validate configuration
            errors = []

            if self.use_negotiated_rates:
                if not self.storage_rate:
                    errors.append(_("Storage rate is required for negotiated rates")):
            if self.volume_discount_enabled:
                if not self.volume_discount_threshold:
                    errors.append(_("Volume discount threshold is required"))

            if self.auto_billing_enabled:
                if not self.billing_contact_email:
                    errors.append(_("Billing contact email is required for auto billing")):
            if errors:
                message = _("Configuration Issues:\n%s", "\n".join(errors))
                return {}
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {}
                        "message": message,
                        "type": "warning",


            else:
                return {}
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {}
                        "message": _("Billing configuration is valid"),
                        "type": "success",



        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def get_effective_rate(self, service_type, container_type=None):
            """Get effective rate for a service considering negotiated rates""":
            self.ensure_one()

            if not self.use_negotiated_rates:
                # Fall back to base rates
                base_rate = self.env['base.rate'].get_active_rate_for_company(self.company_id.id)
                if base_rate:
                    return base_rate.get_service_rate(service_type)
                return 0.0

            # Container-specific storage rates
            if service_type == 'storage' and container_type:
                rate_field = f"{container_type}_storage_rate"
                return getattr(self, rate_field, 0.0) or self.storage_rate or 0.0

            # Service-specific rates
            service_rates = {}
                'storage': self.storage_rate,
                'retrieval': self.retrieval_rate,
                'destruction': self.destruction_rate,
                'pickup': self.pickup_rate,
                'delivery': self.delivery_rate,


            return service_rates.get(service_type, 0.0)


    def calculate_volume_discount(self, container_count):
            """Calculate volume discount based on container count"""
            self.ensure_one()

            if not self.volume_discount_enabled:
                return 0.0

            if container_count >= self.volume_discount_threshold:
                return self.volume_discount_percentage / 100

            return 0.0


    def get_payment_terms_days(self):
            """Get payment terms in days"""
            self.ensure_one()

            terms_map = {}
                'net_15': 15,
                'net_30': 30,
                'net_45': 45,
                'net_60': 60,
                'prepaid': 0,


            return terms_map.get(self.payment_terms, 30)


    def is_due_for_billing(self):
            """Check if customer is due for billing""":
            self.ensure_one()

            if not self.auto_billing_enabled or self.state != 'active':
                return False

            if not self.next_billing_date:
                return True  # First billing

            return fields.Date.today() >= self.next_billing_date

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def get_billing_summary(self):
            """Get billing summary for reporting""":
            self.ensure_one()

            return {}
                'customer': self.partner_id.name,
                'profile': self.name,
                'frequency': dict(self._fields['billing_frequency'].selection)[self.billing_frequency],
                'payment_terms': dict(self._fields['payment_terms'].selection)[self.payment_terms],
                'total_invoiced': self.total_invoiced,
                'invoice_count': self.invoice_count,
                'average_monthly': self.average_monthly_revenue,
                'payment_status': dict(self._fields['payment_status'].selection).get(self.payment_status, 'Unknown'),
                'next_billing': self.next_billing_date,



    def get_dashboard_metrics(self):
            """Get dashboard metrics for billing profiles""":
            active_profiles = self.search([('state', '=', 'active')])

            return {}
                'active_profiles': len(active_profiles),
                'total_revenue': sum(active_profiles.mapped('total_invoiced')),
                'average_revenue_per_customer': sum(active_profiles.mapped('average_monthly_revenue')) / len(active_profiles) if active_profiles else 0,:
                'overdue_customers': len(active_profiles.filtered(lambda p: p.payment_status != 'current')),
                'due_for_billing': len(active_profiles.filtered('is_due_for_billing')),



