from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfigLine(models.Model):
    _name = 'records.billing.config.line'
    _description = 'Records Billing Config Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, sequence, service_type'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    config_id = fields.Many2one()
    product_id = fields.Many2one()
    service_type = fields.Selection()
    billing_method = fields.Selection()
    currency_id = fields.Many2one()
    unit_rate = fields.Monetary()
    minimum_charge = fields.Monetary()
    maximum_charge = fields.Monetary()
    minimum_quantity = fields.Float()
    quantity_increment = fields.Float()
    container_type = fields.Selection()
    effective_date = fields.Date()
    expiry_date = fields.Date()
    discount_percentage = fields.Float()
    markup_percentage = fields.Float()
    billing_frequency = fields.Selection()
    proration_allowed = fields.Boolean()
    effective_rate = fields.Monetary()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    applies_to_count = fields.Integer(string='Applies To Count')
    applies_to_volume = fields.Char(string='Applies To Volume')
    applies_to_weight = fields.Float(string='Applies To Weight')
    billing_config_id = fields.Many2one('billing.config')
    context = fields.Char(string='Context')
    filter_active = fields.Boolean(string='Filter Active')
    filter_default = fields.Char(string='Filter Default')
    filter_discounted = fields.Char(string='Filter Discounted')
    group_billing_method = fields.Char(string='Group Billing Method')
    group_container_type = fields.Selection(string='Group Container Type')
    group_service_type = fields.Selection(string='Group Service Type')
    help = fields.Char(string='Help')
    is_default = fields.Char(string='Is Default')
    notes = fields.Char(string='Notes')
    quantity_parameter = fields.Char(string='Quantity Parameter')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_applies_to_count(self):
            for record in self:
                record.applies_to_count = len(record.applies_to_ids)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_name(self):
            """Compute line description"""
            for record in self:
                parts = []
                if record.service_type:
                    service_dict = dict(record._fields['service_type'].selection)
                    parts.append(service_dict.get(record.service_type, record.service_type))

                if record.billing_method:
                    method_dict = dict(record._fields['billing_method'].selection)
                    parts.append(f"({method_dict.get(record.billing_method, record.billing_method)})")

                record.name = " ".join(parts) if parts else "New Billing Line":

    def _compute_display_name(self):
            """Compute display name"""
            for record in self:
                if record.effective_rate:
                    record.display_name = f"{record.name} - {record.effective_rate:,.2f}"
                else:
                    record.display_name = record.name or "New Billing Line"


    def _compute_effective_rate(self):
            """Calculate effective rate after discounts and markups"""
            for record in self:
                rate = record.unit_rate

                # Apply discount
                if record.discount_percentage:
                    rate = rate * (1 - record.discount_percentage / 100)

                # Apply markup
                if record.markup_percentage:
                    rate = rate * (1 + record.markup_percentage / 100)

                record.effective_rate = rate

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def calculate_charge(self, quantity, container_type=None):
            """Calculate charge for given quantity""":
            self.ensure_one()

            # Apply minimum quantity
            billable_quantity = max(quantity, self.minimum_quantity)

            # Round up to nearest increment
            if self.quantity_increment:
                import math
                billable_quantity = math.ceil(billable_quantity / self.quantity_increment) * self.quantity_increment

            # Calculate base charge
            charge = billable_quantity * self.effective_rate

            # Apply minimum charge
            if self.minimum_charge:
                charge = max(charge, self.minimum_charge)

            # Apply maximum charge cap
            if self.maximum_charge:
                charge = min(charge, self.maximum_charge)

            return charge

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_rates(self):
            """Validate rate values"""
            for record in self:
                if record.unit_rate < 0:
                    raise ValidationError(_('Unit rate cannot be negative'))

                if record.minimum_charge < 0:
                    raise ValidationError(_('Minimum charge cannot be negative'))

                if record.maximum_charge and record.maximum_charge < 0:
                    raise ValidationError(_('Maximum charge cannot be negative'))

                if record.maximum_charge and record.minimum_charge > record.maximum_charge:
                    raise ValidationError(_('Minimum charge cannot exceed maximum charge'))


    def _check_percentages(self):
            """Validate percentage values"""
            for record in self:
                if not (0 <= record.discount_percentage <= 100):
                    raise ValidationError(_('Discount percentage must be between 0 and 100'))

                if record.markup_percentage < 0:
                    raise ValidationError(_('Markup percentage cannot be negative'))


    def _check_quantities(self):
            """Validate quantity parameters"""
            for record in self:
                if record.minimum_quantity <= 0:
                    raise ValidationError(_('Minimum quantity must be greater than 0'))

                if record.quantity_increment <= 0:
                    raise ValidationError(_('Quantity increment must be greater than 0'))


    def _check_dates(self):
            """Validate date range"""
            for record in self:
                if record.expiry_date and record.effective_date > record.expiry_date:
                    raise ValidationError(_('Effective date cannot be after expiry date'))
