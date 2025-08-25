import math
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsBillingConfigLine(models.Model):
    _name = 'records.billing.config.line'
    _description = 'Records Billing Config Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, sequence, id'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related='config_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string="Currency", readonly=True)
    notes = fields.Text(string='Notes')

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    config_id = fields.Many2one('records.billing.config', string="Billing Configuration", required=True, ondelete='cascade')
    product_id = fields.Many2one(related='config_id.product_id', string="Service Product", store=True)

    # ============================================================================
    # BILLING RULE DEFINITION
    # ============================================================================
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('pickup', 'Pickup/Delivery'),
        ('other', 'Other'),
    ], string="Service Type", required=True, default='storage')
    
    billing_method = fields.Selection([
        ('per_unit', 'Per Unit'),
        ('flat_rate', 'Flat Rate'),
        ('per_container_type', 'Per Container Type'),
    ], string="Billing Method", required=True, default='per_unit')

    container_type_id = fields.Many2one('records.container.type', string="Container Type",
        help="Apply this rule only to a specific container type.")

    # ============================================================================
    # PRICING & CHARGES
    # ============================================================================
    unit_rate = fields.Monetary(string="Unit Rate", tracking=True, required=True, default=0.0)
    effective_rate = fields.Monetary(string="Effective Rate", compute='_compute_effective_rate', store=True,
        help="The final rate after discounts and markups are applied.")
    discount_percentage = fields.Float(string="Discount (%)", default=0.0)
    markup_percentage = fields.Float(string="Markup (%)", default=0.0)
    
    minimum_charge = fields.Monetary(string="Minimum Charge", default=0.0)
    maximum_charge = fields.Monetary(string="Maximum Charge (Cap)", default=0.0, help="A value of 0 means no maximum.")
    
    minimum_quantity = fields.Float(string="Minimum Quantity", default=1.0)
    quantity_increment = fields.Float(string="Quantity Increment", default=1.0, help="Billable quantity will be rounded up to the nearest increment.")

    # ============================================================================
    # VALIDITY & TIMING
    # ============================================================================
    effective_date = fields.Date(string="Effective Date")
    expiry_date = fields.Date(string="Expiry Date")
    proration_allowed = fields.Boolean(string="Allow Proration", default=False)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('service_type', 'billing_method', 'container_type_id.name')
    def _compute_display_name(self):
        """Compute display name for easy identification."""
        for record in self:
            parts = []
            if record.service_type:
                service_dict = dict(record._fields['service_type'].selection)
                parts.append(service_dict.get(record.service_type, record.service_type))
            if record.billing_method:
                method_dict = dict(record._fields['billing_method'].selection)
                parts.append(f"({method_dict.get(record.billing_method, record.billing_method)})")
            if record.container_type_id:
                parts.append(f"[{record.container_type_id.name}]")
            
            record.display_name = " ".join(parts) if parts else _("New Billing Line")

    @api.depends('unit_rate', 'discount_percentage', 'markup_percentage')
    def _compute_effective_rate(self):
        """Calculate effective rate after discounts and markups."""
        for record in self:
            rate = record.unit_rate
            if record.discount_percentage > 0:
                rate *= (1 - (record.discount_percentage / 100.0))
            if record.markup_percentage > 0:
                rate *= (1 + (record.markup_percentage / 100.0))
            record.effective_rate = rate

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def calculate_charge(self, quantity):
        """Calculate the charge for a given quantity based on this rule."""
        self.ensure_one()
        
        billable_quantity = max(quantity, self.minimum_quantity)

        if self.quantity_increment > 0:
            billable_quantity = math.ceil(billable_quantity / self.quantity_increment) * self.quantity_increment

        charge = billable_quantity * self.effective_rate

        if self.minimum_charge > 0:
            charge = max(charge, self.minimum_charge)

        if self.maximum_charge > 0:
            charge = min(charge, self.maximum_charge)

        return charge

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('unit_rate', 'minimum_charge', 'maximum_charge')
    def _check_rates(self):
        for record in self:
            if record.unit_rate < 0:
                raise ValidationError(_('Unit rate cannot be negative.'))
            if record.minimum_charge < 0:
                raise ValidationError(_('Minimum charge cannot be negative.'))
            if record.maximum_charge < 0:
                raise ValidationError(_('Maximum charge cannot be negative.'))
            if record.maximum_charge > 0 and record.minimum_charge > record.maximum_charge:
                raise ValidationError(_('Minimum charge cannot be greater than the maximum charge.'))

    @api.constrains('discount_percentage', 'markup_percentage')
    def _check_percentages(self):
        for record in self:
            if not 0.0 <= record.discount_percentage <= 100.0:
                raise ValidationError(_('Discount percentage must be between 0 and 100.'))
            if record.markup_percentage < 0:
                raise ValidationError(_('Markup percentage cannot be negative.'))

    @api.constrains('minimum_quantity', 'quantity_increment')
    def _check_quantities(self):
        for record in self:
            if record.minimum_quantity < 0:
                raise ValidationError(_('Minimum quantity cannot be negative.'))
            if record.quantity_increment < 0:
                raise ValidationError(_('Quantity increment cannot be negative.'))

    @api.constrains('effective_date', 'expiry_date')
    def _check_dates(self):
        for record in self:
            if record.effective_date and record.expiry_date and record.effective_date > record.expiry_date:
                raise ValidationError(_('The effective date cannot be after the expiry date.'))
