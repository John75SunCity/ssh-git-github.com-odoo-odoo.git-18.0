from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class CustomerNegotiatedRate(models.Model):
    _name = 'customer.negotiated.rate'
    _description = 'Customer Negotiated Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'partner_id, rate_type, effective_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    partner_id = fields.Many2one()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    rate_type = fields.Selection()
    container_type = fields.Selection()
    service_type = fields.Selection()
    effective_date = fields.Date()
    expiration_date = fields.Date()
    is_current = fields.Boolean()
    currency_id = fields.Many2one()
    monthly_rate = fields.Monetary()
    annual_rate = fields.Monetary()
    setup_fee = fields.Monetary()
    per_service_rate = fields.Monetary()
    per_hour_rate = fields.Monetary()
    per_document_rate = fields.Monetary()
    minimum_volume = fields.Integer()
    maximum_volume = fields.Integer()
    discount_percentage = fields.Float()
    contract_reference = fields.Char()
    approval_required = fields.Boolean()
    approved_by_id = fields.Many2one()
    approval_date = fields.Datetime()
    state = fields.Selection()
    billing_profile_id = fields.Many2one()
    auto_apply = fields.Boolean()
    priority = fields.Integer()
    base_rate_comparison = fields.Monetary()
    savings_amount = fields.Monetary()
    savings_percentage = fields.Float()
    containers_using_rate = fields.Integer()
    monthly_revenue_impact = fields.Monetary()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_is_current(self):
            """Determine if rate is currently active""":

    def _compute_rate_comparison(self):
            """Compare negotiated rate to base rate"""
            for rate in self:
                if rate.rate_type != 'storage' or not rate.monthly_rate:
                    rate.base_rate_comparison = 0.0
                    rate.savings_amount = 0.0
                    rate.savings_percentage = 0.0
                    continue

                # Get base rate for comparison:
                base_rates = self.env['base.rate'].search([)]
                    ('company_id', '=', rate.company_id.id),
                    ('active', '=', True)


                if not base_rates:
                    rate.base_rate_comparison = 0.0
                    rate.savings_amount = 0.0
                    rate.savings_percentage = 0.0
                    continue

                # Get base rate based on container type
                if rate.container_type == 'type_01':
                    base_rate = base_rates.standard_box_rate
                elif rate.container_type == 'type_02':
                    base_rate = base_rates.legal_box_rate
                elif rate.container_type == 'type_03':
                    base_rate = base_rates.map_box_rate
                elif rate.container_type == 'type_04':
                    base_rate = base_rates.odd_size_rate
                elif rate.container_type == 'type_06':
                    base_rate = base_rates.pathology_rate
                else:
                    base_rate = base_rates.standard_box_rate

                rate.base_rate_comparison = base_rate
                rate.savings_amount = base_rate - rate.monthly_rate

                if base_rate > 0:
                    rate.savings_percentage = ((base_rate - rate.monthly_rate) / base_rate) * 100
                else:
                    rate.savings_percentage = 0.0


    def _compute_usage_stats(self):
            """Compute usage statistics for this rate""":
            for rate in self:
                if not rate.partner_id or not rate.is_current:
                    rate.containers_using_rate = 0
                    rate.monthly_revenue_impact = 0.0
                    continue

                # Count containers that would use this rate
                domain = [('partner_id', '=', rate.partner_id.id), ('active', '=', True)]
                if rate.container_type != 'all':
                    domain.append(('container_type', '=', rate.container_type))

                containers = self.env['records.container'].search(domain)
                rate.containers_using_rate = len(containers)
                rate.monthly_revenue_impact = len(containers) * (rate.monthly_rate or 0.0)

        # ============================================================================
            # CONSTRAINT VALIDATIONS
        # ============================================================================

    def _check_date_validity(self):
            """Validate date range"""
            for rate in self:
                if rate.expiration_date and rate.effective_date > rate.expiration_date:
                    raise ValidationError(_('Effective date cannot be after expiration date'))


    def _check_volume_range(self):
            """Validate volume range"""
            for rate in self:
                if rate.maximum_volume and rate.minimum_volume > rate.maximum_volume:
                    raise ValidationError(_('Minimum volume cannot be greater than maximum volume'))


    def _check_discount_percentage(self):
            """Validate discount percentage"""
            for rate in self:
                if rate.discount_percentage < 0 or rate.discount_percentage > 100:
                    raise ValidationError(_('Discount percentage must be between 0 and 100'))


    def _check_priority(self):
            """Validate priority value"""
            for rate in self:
                if rate.priority < 0:
                    raise ValidationError(_('Priority must be a positive number'))

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_partner_id(self):
            """Update fields when customer changes"""
            if self.partner_id:
                # Set default name
                if not self.name or self.name == 'New':
                    self.name = _('%s - Negotiated Rate', self.partner_id.name)

                # Look for existing billing profile:
                billing_profile = self.env['customer.billing.profile'].search([)]
                    ('partner_id', '=', self.partner_id.id),
                    ('active', '=', True)

                if billing_profile:
                    self.billing_profile_id = billing_profile.id


    def _onchange_rate_type(self):
            """Clear irrelevant fields when rate type changes"""
            if self.rate_type == 'storage':
                self.service_type = False
                self.per_service_rate = 0.0
                self.per_hour_rate = 0.0
                self.per_document_rate = 0.0
            elif self.rate_type == 'service':
                self.container_type = False
                self.monthly_rate = 0.0
                self.annual_rate = 0.0
            elif self.rate_type == 'volume_discount':
                self.per_service_rate = 0.0
                self.per_hour_rate = 0.0
                self.per_document_rate = 0.0


    def _onchange_monthly_rate(self):
            """Calculate annual rate when monthly rate changes"""
            if self.monthly_rate:
                self.annual_rate = self.monthly_rate * 12


    def _onchange_annual_rate(self):
            """Calculate monthly rate when annual rate changes"""
            if self.annual_rate:
                self.monthly_rate = self.annual_rate / 12

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_submit_for_approval(self):
            """Submit rate for management approval""":
            self.ensure_one()
            if self.state != 'draft':
                raise ValidationError(_('Only draft rates can be submitted for approval')):
            self.write({'state': 'submitted'})

            # Create activity for approver:
            self.activity_schedule()
                'mail.mail_activity_data_todo',
                summary=_('Rate Approval Required'),
                note=_('Negotiated rate for %s requires approval', self.partner_id.name),:
                user_id=self.env.user.id  # Could be dynamic based on approval workflow


            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Rate submitted for approval'),:
                    'type': 'success'




    def action_approve_rate(self):
            """Approve the negotiated rate"""
            self.ensure_one()
            if self.state != 'submitted':
                raise ValidationError(_('Only submitted rates can be approved'))

            self.write({)}
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approval_date': fields.Datetime.now()


            # Activate if effective date has passed:

    def action_activate_rate(self):
            """Activate the rate (if approved and effective date reached)""":
            self.ensure_one()
            if self.state != 'approved':
                raise ValidationError(_('Rate must be approved before activation'))

            if self.effective_date > fields.Date.today():
                raise ValidationError(_('Cannot activate rate before effective date'))

            self.write({'state': 'active'})

            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Rate activated successfully'),
                    'type': 'success'




    def action_expire_rate(self):
            """Expire the rate"""
            self.ensure_one()
            self.write({'state': 'expired'})

            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Rate expired'),
                    'type': 'info'




    def action_view_containers(self):
            """View containers that use this rate"""
            self.ensure_one()

            domain = [('partner_id', '=', self.partner_id.id)]
            if self.container_type != 'all':
                domain.append(('container_type', '=', self.container_type))

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Containers Using This Rate'),
                'res_model': 'records.container',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'default_partner_id': self.partner_id.id}



    def action_duplicate_rate(self):
            """Duplicate this rate for modification""":
            self.ensure_one()

            new_rate = self.copy({)}
                'name': _('%s (Copy)', self.name),
                'state': 'draft',
                'approved_by_id': False,
                'approval_date': False,
                'effective_date': fields.Date.today()


            return {}
                'type': 'ir.actions.act_window',
                'name': _('Negotiated Rate'),
                'res_model': 'customer.negotiated.rate',
                'res_id': new_rate.id,
                'view_mode': 'form',
                'target': 'current'


        # ============================================================================
            # CRON AND SCHEDULED METHODS
        # ============================================================================

    def cron_activate_rates(self):
            """Cron job to activate approved rates when effective date is reached"""
            rates_to_activate = self.search([)]
                ('state', '=', 'approved'),
                ('effective_date', '<=', fields.Date.today())


            for rate in rates_to_activate:
                rate.state = 'active'

            return True


    def cron_expire_rates(self):
            """Cron job to expire rates when expiration date is reached"""
            rates_to_expire = self.search([)]
                ('state', 'in', ['active', 'approved']),
                ('expiration_date', '<', fields.Date.today())


            for rate in rates_to_expire:
                rate.state = 'expired'

            return True

