from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerNegotiatedRate(models.Model):
    _name = 'customer.negotiated.rate'
    _description = 'Customer Negotiated Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, effective_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Agreement Name', required=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    partner_id = fields.Many2one()
    contract_reference = fields.Char(string='Contract Reference')
    base_rate_id = fields.Many2one()
    effective_date = fields.Date(string='Effective Date', required=True)
    expiry_date = fields.Date(string='Expiry Date')
    negotiation_date = fields.Date()
    approval_date = fields.Date(string='Approval Date')
    external_per_bin_rate = fields.Float()
    external_service_call_rate = fields.Float()
    managed_permanent_removal_rate = fields.Float()
    managed_retrieval_rate = fields.Float()
    managed_service_call_rate = fields.Float()
    managed_shredding_rate = fields.Float()
    pickup_rate = fields.Float()
    storage_rate_monthly = fields.Float()
    global_discount_percent = fields.Float()
    volume_discount_threshold = fields.Integer()
    volume_discount_percent = fields.Float()
    override_external_rates = fields.Boolean()
    override_managed_rates = fields.Boolean()
    override_pickup_rates = fields.Boolean()
    override_storage_rates = fields.Boolean()
    description = fields.Text(string='Description')
    negotiation_notes = fields.Text(string='Negotiation Notes')
    approval_notes = fields.Text(string='Approval Notes')
    terms_conditions = fields.Text(string='Special Terms & Conditions')
    container_type = fields.Selection()
    container_type_code = fields.Char()
    container_monthly_rate = fields.Float()
    container_setup_fee = fields.Float()
    container_handling_fee = fields.Float()
    container_destruction_fee = fields.Float()
    rate_type = fields.Selection()
    display_name = fields.Char()
    is_expired = fields.Boolean()
    days_until_expiry = fields.Integer()
    total_discount_percent = fields.Float()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    today = fields.Date()
    today = fields.Date()
    expiry_date_obj = fields.Date()
    today_obj = fields.Date()
    service_date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display_name based on partner_id, name, and effective_date"""
            for record in self:
                if record.partner_id and record.name:
                    record.display_name = _("%s - %s", record.partner_id.name, record.name)
                elif record.partner_id:
                    record.display_name = _("%s - Negotiated Rates", record.partner_id.name)
                else:
                    record.display_name = record.name or "New Negotiated Rates"


    def _compute_is_expired(self):
            """Check if negotiated rates have expired""":

    def _compute_days_until_expiry(self):
            """Calculate days until expiry"""

    def _compute_total_discount(self):
            """Calculate total potential discount"""
            for record in self:
                record.total_discount_percent = ()
                    record.global_discount_percent + record.volume_discount_percent


        # ============================================================================
            # CONSTRAINTS AND VALIDATION
        # ============================================================================

    def _check_date_logic(self):
            """Ensure expiry date is after effective date"""
            for record in self:
                if (:)
                    record.expiry_date
                    and record.effective_date
                    and record.expiry_date <= record.effective_date

                    raise ValidationError(_("Expiry date must be after effective date"))


    def _check_unique_active_rates(self):
            """Ensure only one active rate set per customer at any time"""
            for record in self:
                if record.state == "active":
                    existing = self.search()
                        []
                            ("partner_id", "=", record.partner_id.id),
                            ("state", "=", "active"),
                            ("id", "!=", record.id),


                    if existing:
                        raise ValidationError()
                            _()
                                "Customer %s already has active negotiated rates. "
                                "Please expire existing rates before activating new ones.",
                                record.partner_id.name




    def _check_discount_limits(self):
            """Validate discount percentages are within reasonable limits"""
            for record in self:
                if record.global_discount_percent < 0 or record.global_discount_percent >= 100:
                    raise ValidationError()
                        _("Global discount percentage must be between 0 and 99.99")

                if record.volume_discount_percent < 0 or record.volume_discount_percent >= 100:
                    raise ValidationError()
                        _("Volume discount percentage must be between 0 and 99.99")


        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_submit_for_negotiation(self):
            """Submit rates for negotiation""":
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Can only submit draft rates for negotiation")):
            self.write({"state": "negotiating"})
            self.message_post(body=_("Rates submitted for negotiation")):

    def action_approve_rates(self):
            """Approve negotiated rates"""

            self.ensure_one()
            if self.state != "negotiating":
                raise UserError(_("Can only approve rates under negotiation"))
            self.write({"state": "approved", "approval_date": fields.Date.today()})
            self.message_post(body=_("Negotiated rates approved"))


    def action_activate_rates(self):
            """Activate approved rates"""

            self.ensure_one()
            if self.state != "approved":
                raise UserError(_("Can only activate approved rates"))

            # Deactivate any existing active rates for this customer:
            existing_active = self.search()
                [("partner_id", "=", self.partner_id.id), ("state", "=", "active")]

            existing_active.write({"state": "expired"})

            self.write({"state": "active"})
            self.message_post(body=_("Negotiated rates activated"))


    def action_expire_rates(self):
            """Mark rates as expired"""

            self.ensure_one()
            self.write({"state": "expired", "expiry_date": fields.Date.today()})
            self.message_post(body=_("Negotiated rates expired"))


    def action_cancel_rates(self):
            """Cancel negotiated rates"""

            self.ensure_one()
            self.write({"state": "cancelled"})
            self.message_post(body=_("Negotiated rates cancelled"))


    def action_reset_to_draft(self):
            """Reset to draft state"""

            self.ensure_one()
            self.write({"state": "draft", "approval_date": False})
            self.message_post(body=_("Rates reset to draft"))


    def action_duplicate_rates(self):
            """Create new version of negotiated rates"""

            self.ensure_one()
            new_rate = self.copy()
                {}
                    "name": _("%s (Copy)", self.name),
                    "state": "draft",
                    "effective_date": fields.Date.today(),
                    "approval_date": False,


            return {}
                "type": "ir.actions.act_window",
                "name": _("Duplicated Negotiated Rates"),
                "res_model": "customer.negotiated.rate",
                "res_id": new_rate.id,
                "view_mode": "form",
                "target": "current",


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_customer_rates(self, partner_id, service_date=None):
            """Get active negotiated rates for customer""":
            if not service_date:

    def get_effective_rate(self, rate_type, fallback_base_rate=None):
            """Get effective rate with fallback to base rates"""
            self.ensure_one()

            # Check if this rate type is overridden:
            override_field_map = {}
                "external_per_bin_rate": "override_external_rates",
                "external_service_call_rate": "override_external_rates",
                "managed_permanent_removal_rate": "override_managed_rates",
                "managed_retrieval_rate": "override_managed_rates",
                "managed_service_call_rate": "override_managed_rates",
                "managed_shredding_rate": "override_managed_rates",
                "pickup_rate": "override_pickup_rates",
                "storage_rate_monthly": "override_storage_rates",


            override_field = override_field_map.get(rate_type)
            if override_field and getattr(self, override_field, False):
                negotiated_rate = getattr(self, rate_type, 0.0)
                if negotiated_rate > 0:
                    # Apply global discount
                    if self.global_discount_percent > 0:
                        if self.global_discount_percent >= 100:
                            raise ValidationError()
                                _()
                                    "Global discount percent cannot be 100 or more, "
                                    "as it would result in zero or negative rates."


                        negotiated_rate *= 1 - self.global_discount_percent / 100
                    return negotiated_rate

            # Fallback to base rate
            base_rate = fallback_base_rate or self.base_rate_id
            if (:)
                base_rate
                and hasattr(base_rate, "get_rate")
                and callable(getattr(base_rate, "get_rate", None))

                return base_rate.get_rate(rate_type)

            return 0.0


    def get_container_specific_rate(self, container_type, rate_field):
            """Get negotiated rate for specific container type""":
            self.ensure_one()

            # If this negotiated rate applies to all container types or specific type
            if self.container_type in ['all_types', container_type]:
                return getattr(self, rate_field, 0.0)

            # Look for specific rate for this container type:
            specific_rate = self.search([)]
                ('partner_id', '=', self.partner_id.id),
                ('container_type', '=', container_type),
                ('state', '=', 'active'),


            if specific_rate:
                return getattr(specific_rate, rate_field, 0.0)

            return 0.0


    def get_dashboard_stats(self):
            """Get dashboard statistics for negotiated rates""":
            total_agreements = self.search_count([
            active_agreements = self.search_count([('state', '=', 'active')])
            expiring_soon = self.search_count([)]
                ('state', '=', 'active'),
                ('expiry_date', '<=', fields.Date.add(fields.Date.today(), days=30)),
                ('expiry_date', '>', fields.Date.today())


            return {}
                'total_agreements': total_agreements,
                'active_agreements': active_agreements,
                'expiring_soon': expiring_soon,
                'draft_agreements': self.search_count([('state', '=', 'draft')]),


        # ============================================================================
            # CRON AND AUTOMATION METHODS
        # ============================================================================

    def cron_expire_rates(self):
            """Cron job to automatically expire rates past their expiry date"""
            expired_rates = self.search([)]
                ('state', '=', 'active'),
                ('expiry_date', '<', fields.Date.today())


            for rate in expired_rates:
                rate.write({'state': 'expired'})
                rate.message_post(body=_("Rate automatically expired by system"))

            return len(expired_rates)


    def notify_expiring_rates(self):
            """Notify managers about rates expiring soon"""
            expiring_rates = self.search([)]
                ('state', '=', 'active'),
                ('expiry_date', '<=', fields.Date.add(fields.Date.today(), days=30)),
                ('expiry_date', '>', fields.Date.today())


            if expiring_rates:
                # Create activities for managers:
                managers = self.env.ref('records_management.group_records_manager').users
                for manager in managers:
                    for rate in expiring_rates:
                        self.env['mail.activity'].create({)}
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'summary': _('Negotiated Rate Expiring Soon'),
                            'note': _()
                                'Negotiated rate for %s expires on %s. ':
                                'Please review and renew if necessary.',:
                                rate.partner_id.name,
                                rate.expiry_date

                            'user_id': manager.id,
                            'res_model_id': self.env['ir.model']._get('customer.negotiated.rate').id,
                            'res_id': rate.id,


            return len(expiring_rates)

        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================

    def apply_rate_to_invoice_line(self, invoice_line):
            """Apply negotiated rate to invoice line"""
            self.ensure_one()

            # Determine the service type and apply appropriate rate
            service_type = invoice_line.product_id.default_code or 'storage'
            effective_rate = self.get_effective_rate(service_type)

            if effective_rate > 0:
                invoice_line.price_unit = effective_rate
                invoice_line.price_subtotal = effective_rate * invoice_line.quantity

                # Add note about negotiated rate
                note = _("Applied negotiated rate: %s", self.name)
                if invoice_line.name:
                    invoice_line.name += f"\n{note}"
                else:
                    invoice_line.name = note


    def create_rate_change_history(self, old_values):
            """Create audit trail for rate changes""":
            self.ensure_one()

            changes = []
            for field, old_value in old_values.items():
                new_value = getattr(self, field)
                if old_value != new_value:
                    changes.append(_("%(field)s: %(old)s # -> %(new)s",
                                    field=self._fields[field].string,
                                    old=old_value,
                                    new=new_value

            if changes:
                self.message_post()
                    body=_("Rate changes: %s", "; ".join(changes)),
                    subtype_xmlid="mail.mt_note"

