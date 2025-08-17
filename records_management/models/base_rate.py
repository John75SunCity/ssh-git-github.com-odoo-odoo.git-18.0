from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class BaseRate(models.Model):
    _name = 'base.rate'
    _description = 'Base Rate Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'company_id, effective_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    effective_date = fields.Date()
    expiration_date = fields.Date()
    version = fields.Char()
    description = fields.Text()
    currency_id = fields.Many2one()
    standard_box_rate = fields.Monetary()
    legal_box_rate = fields.Monetary()
    map_box_rate = fields.Monetary()
    odd_size_rate = fields.Monetary()
    pathology_rate = fields.Monetary()
    pickup_rate = fields.Monetary()
    delivery_rate = fields.Monetary()
    destruction_rate = fields.Monetary()
    document_retrieval_rate = fields.Monetary()
    scanning_rate = fields.Monetary()
    indexing_rate = fields.Monetary()
    technician_hourly_rate = fields.Monetary()
    supervisor_hourly_rate = fields.Monetary()
    new_customer_setup_fee = fields.Monetary()
    container_setup_fee = fields.Monetary()
    barcode_generation_fee = fields.Monetary()
    enable_volume_tiers = fields.Boolean()
    small_volume_threshold = fields.Integer()
    small_volume_multiplier = fields.Float()
    large_volume_threshold = fields.Integer()
    large_volume_multiplier = fields.Float()
    enterprise_volume_threshold = fields.Integer()
    enterprise_volume_multiplier = fields.Float()
    enable_location_modifiers = fields.Boolean()
    premium_location_multiplier = fields.Float()
    standard_location_multiplier = fields.Float()
    economy_location_multiplier = fields.Float()
    billing_frequency_default = fields.Selection()
    proration_method = fields.Selection()
    minimum_monthly_charge = fields.Monetary()
    average_container_rate = fields.Monetary()
    rate_per_cubic_foot = fields.Monetary()
    total_service_rate = fields.Monetary()
    customers_using_rates = fields.Integer()
    containers_at_base_rates = fields.Integer()
    state = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_rate_analysis(self):
            """Compute rate analysis metrics"""
            for rate in self:
                # Calculate average container rate (weighted by typical usage)
                # TYPE 1 is most common (60%), TYPE 2 (25%), others (15%)
                total_rate = ()
                    rate.standard_box_rate * 0.60 +
                    rate.legal_box_rate * 0.25 +
                    rate.map_box_rate * 0.5 +
                    rate.odd_size_rate * 0.5 +
                    rate.pathology_rate * 0.5

                rate.average_container_rate = total_rate

                # Calculate rate per cubic foot (weighted average)
                total_volume = (1.2 * 0.60) + (2.4 * 0.25) + (0.875 * 0.5) + (5.0 * 0.5) + (0.42 * 0.5)
                if total_volume > 0:
                    rate.rate_per_cubic_foot = total_rate / total_volume
                else:
                    rate.rate_per_cubic_foot = 0.0

                # Sum all service rates
                rate.total_service_rate = ()
                    rate.pickup_rate + rate.delivery_rate + rate.destruction_rate +
                    (rate.document_retrieval_rate or 0.0) + (rate.scanning_rate or 0.0) +
                    (rate.indexing_rate or 0.0)



    def _compute_usage_stats(self):
            """Compute statistics on rate usage"""
            for rate in self:
                if not rate.active:
                    rate.customers_using_rates = 0
                    rate.containers_at_base_rates = 0
                    continue

                # Count customers without negotiated rates
                all_customers = self.env['res.partner').search([)]
                    ('is_company', '=', True),
                    ('company_id', '=', rate.company_id.id)


                customers_with_negotiated = self.env['customer.negotiated.rate'].search([)]
                    ('state', '=', 'active'),
                    ('company_id', '=', rate.company_id.id)


                customers_using_base = all_customers - customers_with_negotiated
                rate.customers_using_rates = len(customers_using_base)

                # Count containers for customers using base rates:
                containers = self.env['records.container'].search([)]
                    ('partner_id', 'in', customers_using_base.ids),
                    ('active', '=', True)

                rate.containers_at_base_rates = len(containers)

        # ============================================================================
            # CONSTRAINT VALIDATIONS
        # ============================================================================

    def _check_date_validity(self):
            """Validate date range"""
            for rate in self:
                if rate.expiration_date and rate.effective_date > rate.expiration_date:
                    raise ValidationError(_('Effective date cannot be after expiration date'))


    def _check_volume_thresholds(self):
            """Validate volume thresholds are in ascending order"""
            for rate in self:
                if rate.enable_volume_tiers:
                    if rate.small_volume_threshold >= rate.large_volume_threshold:
                        raise ValidationError(_('Large volume threshold must be greater than small volume threshold'))
                    if rate.large_volume_threshold >= rate.enterprise_volume_threshold:
                        raise ValidationError(_('Enterprise volume threshold must be greater than large volume threshold'))


    def _check_multipliers(self):
            """Validate rate multipliers are reasonable"""
            for rate in self:
                multipliers = [rate.small_volume_multiplier, rate.large_volume_multiplier, rate.enterprise_volume_multiplier]
                for multiplier in multipliers:
                    if multiplier <= 0 or multiplier > 10:
                        raise ValidationError(_('Rate multipliers must be between 0.1 and 10.0'))


    def _check_unique_active_rate(self):
            """Ensure only one active base rate per company"""
            for rate in self:
                if rate.active:
                    other_active = self.search([)]
                        ('company_id', '=', rate.company_id.id),
                        ('active', '=', True),
                        ('id', '!=', rate.id)

                    if other_active:
                        raise ValidationError(_('Only one active base rate configuration is allowed per company'))

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_container_rate(self, container_type, volume=None):
            """Get the rate for a specific container type""":
            self.ensure_one()

            base_rates = {}
                'type_01': self.standard_box_rate,
                'type_02': self.legal_box_rate,
                'type_03': self.map_box_rate,
                'type_04': self.odd_size_rate,
                'type_06': self.pathology_rate,


            return base_rates.get(container_type, self.standard_box_rate)


    def get_volume_multiplier(self, container_count):
            """Get volume-based rate multiplier"""
            self.ensure_one()

            if not self.enable_volume_tiers:
                return 1.0

            if container_count >= self.enterprise_volume_threshold:
                return self.enterprise_volume_multiplier
            elif container_count >= self.large_volume_threshold:
                return self.large_volume_multiplier
            elif container_count <= self.small_volume_threshold:
                return self.small_volume_multiplier
            else:
                return 1.0


    def get_location_multiplier(self, location_type):
            """Get location-based rate multiplier"""
            self.ensure_one()

            if not self.enable_location_modifiers:
                return 1.0

            multipliers = {}
                'premium': self.premium_location_multiplier,
                'standard': self.standard_location_multiplier,
                'economy': self.economy_location_multiplier,


            return multipliers.get(location_type, self.standard_location_multiplier)


    def calculate_customer_rate(self, partner_id, container_type, location_type='standard'):
            """Calculate final rate for a customer considering all modifiers""":
            self.ensure_one()

            # Get base container rate
            base_rate = self.get_container_rate(container_type)

            # Get customer's container count for volume multiplier:'
            container_count = self.env['records.container'].search_count([)]
                ('partner_id', '=', partner_id),
                ('active', '=', True)


            volume_multiplier = self.get_volume_multiplier(container_count)
            location_multiplier = self.get_location_multiplier(location_type)

            final_rate = base_rate * volume_multiplier * location_multiplier

            return {}
                'base_rate': base_rate,
                'volume_multiplier': volume_multiplier,
                'location_multiplier': location_multiplier,
                'final_rate': final_rate,
                'container_count': container_count


        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_duplicate_rates(self):
            """Create a new version of these rates"""
            self.ensure_one()

            new_rate = self.copy({)}
                'name': _('%s (v%s)', self.name, fields.Datetime.now().strftime('%Y%m%d')),
                'effective_date': fields.Date.today(),
                'active': False,  # New rates start inactive
                'version': str(float(self.version or '1.0') + 0.1)


            return {}
                'type': 'ir.actions.act_window',
                'name': _('Base Rate Configuration'),
                'res_model': 'base.rate',
                'res_id': new_rate.id,
                'view_mode': 'form',
                'target': 'current'



    def action_apply_increase(self):
            """Open wizard to apply percentage increase to all rates"""
            self.ensure_one()

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Apply Rate Increase'),
                'res_model': 'base.rate.increase.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_base_rate_id': self.id}



    def action_view_customers_using_rates(self):
            """View customers using these base rates"""
            self.ensure_one()

            # Get customers without negotiated rates
            customers_with_negotiated = self.env['customer.negotiated.rate'].search([)]
                ('state', '=', 'active'),
                ('company_id', '=', self.company_id.id)


            all_customers = self.env['res.partner'].search([)]
                ('is_company', '=', True),
                ('company_id', '=', self.company_id.id)


            customers_using_base = all_customers - customers_with_negotiated

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Customers Using Base Rates'),
                'res_model': 'res.partner',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', customers_using_base.ids)],
                'context': {'default_company_id': self.company_id.id}



    def action_activate_rates(self):
            """Activate these rates and deactivate others"""
            self.ensure_one()

            # Deactivate other active rates for this company:
            other_rates = self.search([)]
                ('company_id', '=', self.company_id.id),
                ('active', '=', True),
                ('id', '!=', self.id)

            other_rates.write({'active': False})

            # Activate this rate
            self.write({'active': True, 'state': 'active'})

            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Base rates activated successfully'),
                    'type': 'success'




    def action_deactivate_rates(self):
            """Deactivate these rates"""
            self.ensure_one()

            self.write({'active': False, 'state': 'inactive'})

            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Base rates deactivated successfully'),
                    'type': 'success'



        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_active_rate_for_company(self, company_id=None):
            """Get the active base rate for a company""":
            if not company_id:
                company_id = self.env.company.id

            return self.search([)]
                ('company_id', '=', company_id),
                ('active', '=', True)



    def create_default_rates(self, company_id):
            """Create default base rates for a new company""":
            return self.create({)}
                'name': _('Default Base Rates'),
                'company_id': company_id,
                'standard_box_rate': 4.50,
                'legal_box_rate': 6.75,
                'map_box_rate': 3.95,
                'odd_size_rate': 22.50,
                'pathology_rate': 0.19,
                'pickup_rate': 50.0,
                'delivery_rate': 50.0,
                'destruction_rate': 75.0,
                'document_retrieval_rate': 15.0,
                'scanning_rate': 0.25,
                'indexing_rate': 0.15,
                'technician_hourly_rate': 45.0,
                'supervisor_hourly_rate': 65.0,
                'new_customer_setup_fee': 100.0,
                'container_setup_fee': 2.50,
                'barcode_generation_fee': 1.0,
                'minimum_monthly_charge': 25.0,
                'active': True,
                'state': 'active'



    def get_service_rate(self, service_type):
            """Get rate for a specific service type""":
            self.ensure_one()

            service_rates = {}
                'pickup': self.pickup_rate,
                'delivery': self.delivery_rate,
                'destruction': self.destruction_rate,
                'document_retrieval': self.document_retrieval_rate,
                'scanning': self.scanning_rate,
                'indexing': self.indexing_rate,


            return service_rates.get(service_type, 0.0)


    def get_hourly_rate(self, role_type):
            """Get hourly rate for a specific role""":
            self.ensure_one()

            hourly_rates = {}
                'technician': self.technician_hourly_rate,
                'supervisor': self.supervisor_hourly_rate,


            return hourly_rates.get(role_type, self.technician_hourly_rate)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_container_rates(self):
            """Validate container rates are positive"""
            for record in self:
                container_rates = []
                    record.standard_box_rate, record.legal_box_rate, record.map_box_rate,
                    record.odd_size_rate, record.pathology_rate

                for rate in container_rates:
                    if rate < 0:
                        raise ValidationError(_('Container rates cannot be negative'))


    def _check_service_rates(self):
            """Validate service rates are positive"""
            for record in self:
                service_rates = [record.pickup_rate, record.delivery_rate, record.destruction_rate]
                for rate in service_rates:
                    if rate < 0:
                        raise ValidationError(_('Service rates cannot be negative'))


