# -*- coding: utf-8 -*-

Records Billing Config Line Model

Individual line items for billing configuration rates and services.:
    pass


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfigLine(models.Model):
    """Records Billing Config Line"""

    _name = "records.billing.config.line"
    _description = "Records Billing Config Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "config_id, sequence, service_type"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Line Description",
        compute='_compute_name',
        store=True,
        help="Computed name based on service and rate"
    

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the billing line":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this billing line"
    

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for line ordering":
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent billing configuration"
    

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        help="Product associated with this billing line"
    

        # ============================================================================
    # SERVICE CONFIGURATION
        # ============================================================================
    service_type = fields.Selection([)]
        ('storage', 'Document Storage'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Document Destruction'),
        ('pickup', 'Pickup Service'),
        ('delivery', 'Delivery Service'),
        ('scanning', 'Document Scanning'),
        ('indexing', 'Document Indexing'),
        ('consulting', 'Consulting Service'),
        ('setup', 'Setup Fee'),
        ('monthly', 'Monthly Fee'),
        ('other', 'Other Service')
    

    billing_method = fields.Selection([)]
        ('per_container', 'Per Container'),
        ('per_cubic_foot', 'Per Cubic Foot'),
        ('per_document', 'Per Document'),
        ('per_hour', 'Per Hour'),
        ('flat_rate', 'Flat Rate'),
        ('per_pickup', 'Per Pickup'),
        ('percentage', 'Percentage Based'),
        ('tiered', 'Tiered Pricing')
    

        # ============================================================================
    # PRICING FIELDS
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    

    unit_rate = fields.Monetary(
        string="Unit Rate",
        currency_field="currency_id",
        required=True,
        tracking=True,
        help="Base rate per unit"
    

    minimum_charge = fields.Monetary(
        string="Minimum Charge",
        currency_field="currency_id",
        default=0.0,
        help="Minimum charge for this service":
    

    maximum_charge = fields.Monetary(
        string="Maximum Charge",
        currency_field="currency_id",
        help="Maximum charge cap for this service":
    

        # ============================================================================
    # QUANTITY PARAMETERS
        # ============================================================================
    minimum_quantity = fields.Float(
        string="Minimum Quantity",
        default=1.0,
        help="Minimum billable quantity"
    

    quantity_increment = fields.Float(
        string="Quantity Increment",
        default=1.0,
        help="Billing quantity increment (e.g., 0.5 for half-hour increments)":
    

        # ============================================================================
    # CONTAINER TYPE SPECIFICATIONS
        # ============================================================================
    container_type = fields.Selection([)]
        ('type_01', 'TYPE 01 - Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02 - Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03 - Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04 - Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06 - Pathology Box (0.042 CF)'),
        ('all_types', 'All Container Types')
    

        # ============================================================================
    # TIME-BASED PRICING
        # ============================================================================
    effective_date = fields.Date(
        string="Effective Date",
        default=fields.Date.today,
        required=True,
        help="Date when this rate becomes effective"
    

    expiry_date = fields.Date(
        string="Expiry Date",
        help="Date when this rate expires"
    

        # ============================================================================
    # DISCOUNT AND MARKUP
        # ============================================================================
    discount_percentage = fields.Float(
        string="Discount %",
        default=0.0,
        help="Discount percentage to apply"
    

    markup_percentage = fields.Float(
        string="Markup %",
        default=0.0,
        help="Markup percentage to apply"
    

        # ============================================================================
    # BILLING TERMS
        # ============================================================================
    billing_frequency = fields.Selection([)]
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('on_demand', 'On Demand')
    

    proration_allowed = fields.Boolean(
        string="Proration Allowed",
        default=True,
        help="Whether partial periods can be prorated"
    

        # ============================================================================
    # CALCULATION RESULTS
        # ============================================================================
    effective_rate = fields.Monetary(
        string="Effective Rate",
        currency_field="currency_id",
        compute='_compute_effective_rate',
        store=True,
        help="Final rate after discounts/markups"
    

        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id", string="Messages"),
    applies_to_count = fields.Integer(string='Applies To Count', compute='_compute_applies_to_count', store=True),
    applies_to_volume = fields.Char(string='Applies To Volume'),
    applies_to_weight = fields.Float(string='Applies To Weight', digits=(12, 2))
    billing_config_id = fields.Many2one('billing.config', string='Billing Config Id'),
    context = fields.Char(string='Context'),
    filter_active = fields.Boolean(string='Filter Active', default=False),
    filter_default = fields.Char(string='Filter Default'),
    filter_discounted = fields.Char(string='Filter Discounted'),
    group_billing_method = fields.Char(string='Group Billing Method'),
    group_container_type = fields.Selection([], string='Group Container Type')  # TODO: Define selection options
    group_service_type = fields.Selection([], string='Group Service Type')  # TODO: Define selection options
    help = fields.Char(string='Help'),
    is_default = fields.Char(string='Is Default'),
    notes = fields.Char(string='Notes'),
    quantity_parameter = fields.Char(string='Quantity Parameter'),
    res_model = fields.Char(string='Res Model'),
    view_mode = fields.Char(string='View Mode')

    @api.depends('applies_to_ids')
    def _compute_applies_to_count(self):
        for record in self:
            record.applies_to_count = len(record.applies_to_ids)

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends('service_type', 'billing_method', 'unit_rate')
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
    @api.depends('name', 'effective_rate')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.effective_rate:
                record.display_name = f"{record.name} - {record.effective_rate:,.2f}"
            else:
                record.display_name = record.name or "New Billing Line"

    @api.depends('unit_rate', 'discount_percentage', 'markup_percentage')
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
    @api.constrains('unit_rate', 'minimum_charge', 'maximum_charge')
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

    @api.constrains('discount_percentage', 'markup_percentage')
    def _check_percentages(self):
        """Validate percentage values"""
        for record in self:
            if not (0 <= record.discount_percentage <= 100):
                raise ValidationError(_('Discount percentage must be between 0 and 100'))
            
            if record.markup_percentage < 0:
                raise ValidationError(_('Markup percentage cannot be negative'))

    @api.constrains('minimum_quantity', 'quantity_increment')
    def _check_quantities(self):
        """Validate quantity parameters"""
        for record in self:
            if record.minimum_quantity <= 0:
                raise ValidationError(_('Minimum quantity must be greater than 0'))
            
            if record.quantity_increment <= 0:
                raise ValidationError(_('Quantity increment must be greater than 0'))

    @api.constrains('effective_date', 'expiry_date')
    def _check_dates(self):
        """Validate date range"""
        for record in self:
            if record.expiry_date and record.effective_date > record.expiry_date:
                raise ValidationError(_('Effective date cannot be after expiry date'))
