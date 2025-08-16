# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductContainerType(models.Model):
    """Product Container Type"

        Defines container types as product variants for billing and inventory management.:
            pass
    Links physical container specifications with product catalog for automated billing.""":"
        Integrates with rate management and customer billing systems.

    _name = 'product.container.type'
    _description = 'Product Container Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'sequence, name'

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string='Container Type Name',
        required=True,
        tracking=True,
        help='Display name for this container type':
    
    
    code = fields.Char(
        string='Container Code',
        required=True,
        size=10,
        tracking=True,
        ,
    help='Unique code for this container type (e.g., TYPE01, TYPE02)':
    
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ,
    domain=[('type', '=', 'service')),
        help='Product record for billing this container type':
    
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Whether this container type is active'
    
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display sequence for ordering':
    

        # ============================================================================
    # PHYSICAL SPECIFICATIONS
        # ============================================================================
    volume_cubic_feet = fields.Float(
        ,
    string='Volume (Cubic Feet)',
        required=True,
        digits=(8, 3),
        help='Container volume in cubic feet'
    
    
    average_weight_lbs = fields.Float(
        ,
    string='Average Weight (lbs)',
        required=True,
        digits=(8, 2),
        help='Average weight when full in pounds'
    
    
    max_weight_lbs = fields.Float(
        ,
    string='Maximum Weight (lbs)',
        digits=(8, 2),
        help='Maximum recommended weight in pounds'
    
    
        # Dimensions
    length_inches = fields.Float(
        ,
    string='Length (inches)',
        digits=(6, 2),
        help='Container length in inches'
    
    
    width_inches = fields.Float(
        ,
    string='Width (inches)',
        digits=(6, 2),
        help='Container width in inches'
    
    
    height_inches = fields.Float(
        ,
    string='Height (inches)',
        digits=(6, 2),
        help='Container height in inches'
    
    
        # Calculated dimensions
    dimensions_display = fields.Char(
        string='Dimensions',
        compute='_compute_dimensions_display',
        help='Formatted dimensions display'
    

        # ============================================================================
    # BUSINESS SPECIFICATIONS
        # ============================================================================
    ,
    container_type_code = fields.Selection([))
        ('type_01', 'TYPE 1 - Standard Box'),
        ('type_02', 'TYPE 2 - Legal/Banker Box'),
        ('type_03', 'TYPE 3 - Map Box'),
        ('type_04', 'TYPE 4 - Odd Size/Temp Box'),
        ('type_06', 'TYPE 6 - Pathology Box'),
        ('custom', 'Custom Type')
    

    usage_category = fields.Selection([))
        ('general', 'General File Storage'),
        ('legal', 'Legal Documents'),
        ('medical', 'Medical Records'),
        ('blueprints', 'Blueprints/Maps'),
        ('temporary', 'Temporary Storage'),
        ('specialized', 'Specialized Storage')
    

    document_capacity = fields.Integer(
        string='Document Capacity',
        help='Approximate number of documents this container can hold'
    

        # ============================================================================
    # PRICING CONFIGURATION
        # ============================================================================
    base_monthly_rate = fields.Float(
        string='Base Monthly Rate',
        related='product_id.list_price',
        readonly=True,
        help='Base monthly storage rate from product'
    
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='product_id.currency_id',
        readonly=True
    

        # Service pricing
    setup_fee = fields.Monetary(
        string='Setup Fee',
        currency_field='currency_id',
        help='One-time setup fee for this container type':
    
    
    handling_fee = fields.Monetary(
        string='Handling Fee',
        currency_field='currency_id',
        help='Fee per container for pickup/delivery':
    

        # ============================================================================
    # OPERATIONAL FIELDS
        # ============================================================================
    barcode_prefix = fields.Char(
        string='Barcode Prefix',
        size=5,
        help='Prefix for generated barcodes for this container type':
    
    
    requires_special_handling = fields.Boolean(
        string='Requires Special Handling',
        default=False,
        help='Whether this container type requires special handling procedures'
    
    
    climate_controlled_only = fields.Boolean(
        string='Climate Controlled Only',
        default=False,
        help='Whether this container type requires climate-controlled storage'
    
    
    ,
    security_level = fields.Selection([))
        ('standard', 'Standard Security'),
        ('enhanced', 'Enhanced Security'),
        ('maximum', 'Maximum Security')
    

        # ============================================================================
    # USAGE STATISTICS (COMPUTED)
        # ============================================================================
    container_count = fields.Integer(
        string='Container Count',
        compute='_compute_usage_stats',
        help='Number of containers of this type'
    
    
    active_containers = fields.Integer(
        string='Active Containers',
        compute='_compute_usage_stats',
        help='Number of active containers of this type'
    
    
    monthly_revenue = fields.Monetary(
        string='Monthly Revenue',
        compute='_compute_usage_stats',
        currency_field='currency_id',
        help='Estimated monthly revenue from this container type'
    
    
        # Customer statistics
    customer_count = fields.Integer(
        string='Customer Count',
        compute='_compute_customer_stats',
        help='Number of customers using this container type'
    
    
    top_customers = fields.Text(
        string='Top Customers',
        compute='_compute_customer_stats',
        help='List of top customers by container count'
    

        # ============================================================================
    # WORKFLOW STATE MANAGEMENT
        # ============================================================================
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    
        help='Current status of the record'

    # ============================================================================
        # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities"
    
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers"
    
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        ,
    string="Messages"
    

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('length_inches', 'width_inches', 'height_inches')
    def _compute_dimensions_display(self):
        """Format dimensions for display""":
        for record in self:
            if record.length_inches and record.width_inches and record.height_inches:
                record.dimensions_display = _('%.1f"  %.1f"  %.1f"',"
                                            record.length_inches,
                                            record.width_inches,
                                            record.height_inches
            else:
                record.dimensions_display = _('Dimensions not specified')

    @api.depends('container_type_code')
    def _compute_usage_stats(self):
        """Compute usage statistics"""
        for container_type in self:
            containers = self.env['records.container').search([)]
                ('container_type', '=', container_type.container_type_code),
                ('company_id', '=', container_type.company_id.id)
            
            
            container_type.container_count = len(containers)
            container_type.active_containers = len(containers.filtered('active'))
            
            # Calculate monthly revenue
            active_count = container_type.active_containers
            container_type.monthly_revenue = active_count * container_type.base_monthly_rate

    @api.depends('container_type_code')
    def _compute_customer_stats(self):
        """Compute customer statistics"""
        for container_type in self:
            containers = self.env['records.container'].search([)]
                ('container_type', '=', container_type.container_type_code),
                ('active', '=', True),
                ('company_id', '=', container_type.company_id.id)
            
            
            customers = containers.mapped('partner_id')
            container_type.customer_count = len(customers)
            
            # Get top customers by container count
            if customers:
                customer_counts = {}
                for container in containers:
                    partner = container.partner_id
                    customer_counts[partner.name] = customer_counts.get(partner.name, 0) + 1
                
                # Sort by count and get top 5
                sorted_customers = sorted(customer_counts.items(), key=lambda x: x[1], reverse=True)
                top_5 = sorted_customers[:5]
                
                container_type.top_customers = '\n'.join([)]
                    _('%s (%d containers)', name, count) for name, count in top_5:
                
            else:
                container_type.top_customers = _('No customers yet')

    # ============================================================================
        # CONSTRAINT VALIDATIONS
    # ============================================================================
    @api.constrains('code')
    def _check_unique_code(self):
        """Ensure container code is unique per company"""
        for record in self:
            existing = self.search([)]
                ('code', '=', record.code),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            
            if existing:
                raise ValidationError(_('Container code must be unique per company'))

    @api.constrains('volume_cubic_feet', 'average_weight_lbs')
    def _check_positive_values(self):
        """Ensure physical specifications are positive"""
        for record in self:
            if record.volume_cubic_feet <= 0:
                raise ValidationError(_('Volume must be positive'))
            if record.average_weight_lbs <= 0:
                raise ValidationError(_('Average weight must be positive'))

    @api.constrains('length_inches', 'width_inches', 'height_inches')
    def _check_dimensions_consistency(self):
        """Check that dimensions are consistent with volume"""
        for record in self:
            if all([record.length_inches, record.width_inches, record.height_inches]):
                # Convert cubic inches to cubic feet (1728 cubic inches = 1 cubic foot)
                calculated_volume = ()
                    record.length_inches * record.width_inches * record.height_inches
                
                if abs(calculated_volume - record.volume_cubic_feet) > 0.1:
                    raise ValidationError(_('Dimensions do not match specified volume'))

    @api.constrains('max_weight_lbs', 'average_weight_lbs')
    def _check_weight_consistency(self):
        """Ensure max weight is greater than average weight"""
        for record in self:
            if record.max_weight_lbs and record.max_weight_lbs < record.average_weight_lbs:
                raise ValidationError(_())
                    'Maximum weight must be greater than or equal to average weight'
                

    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_type_code')
    def _onchange_container_type_code(self):
        """Set default specifications based on business type"""
        if self.container_type_code:
            # Set defaults based on actual business specifications
            specs = {}
                'type_01': {}
                    'name': 'Standard Box',
                    'volume_cubic_feet': 1.2,
                    'average_weight_lbs': 35,
                    'length_inches': 12,
                    'width_inches': 15,
                    'height_inches': 10,
                    'usage_category': 'general',
                    'document_capacity': 2500
                
                'type_02': {}
                    'name': 'Legal/Banker Box',
                    'volume_cubic_feet': 2.4,
                    'average_weight_lbs': 65,
                    'length_inches': 24,
                    'width_inches': 15,
                    'height_inches': 10,
                    'usage_category': 'legal',
                    'document_capacity': 5000
                
                'type_03': {}
                    'name': 'Map Box',
                    'volume_cubic_feet': 0.875,
                    'average_weight_lbs': 35,
                    'length_inches': 42,
                    'width_inches': 6,
                    'height_inches': 6,
                    'usage_category': 'blueprints',
                    'document_capacity': 200
                
                'type_04': {}
                    'name': 'Odd Size/Temp Box',
                    'volume_cubic_feet': 5.0,
                    'average_weight_lbs': 75,
                    'usage_category': 'temporary',
                    'document_capacity': 10000
                
                'type_06': {}
                    'name': 'Pathology Box',
                    'volume_cubic_feet': 0.42,
                    'average_weight_lbs': 40,
                    'length_inches': 12,
                    'width_inches': 6,
                    'height_inches': 10,
                    'usage_category': 'medical',
                    'document_capacity': 100
                
            
            
            if self.container_type_code in specs:
                spec = specs[self.container_type_code]
                for field, value in spec.items():
                    if not getattr(self, field) or field == 'name':
                        setattr(self, field, value)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update fields when product changes"""
        if self.product_id and not self.name:
            self.name = self.product_id.name

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        """View all containers of this type"""
        self.ensure_one()
        
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Containers - %s', self.name),
            'res_model': 'records.container',
            'view_mode': 'tree,form',
            'domain': [('container_type', '=', self.container_type_code)],
            'context': {}
                'default_container_type': self.container_type_code,
                'default_company_id': self.company_id.id
            
        

    def action_view_customers(self):
        """View customers using this container type"""
        self.ensure_one()
        
        containers = self.env['records.container'].search([)]
            ('container_type', '=', self.container_type_code),
            ('active', '=', True)
        
        customer_ids = containers.mapped('partner_id').ids
        
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Customers - %s', self.name),
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', customer_ids)],
            'context': {'default_company_id': self.company_id.id}
        

    def action_create_product(self):
        """Create or update the associated product"""
        self.ensure_one()
        
        if not self.product_id:
            # Create new product
            product_vals = {}
                'name': self.name,
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
                'list_price': 0.0,  # Will be set based on base rates
                'description': _('Storage service for %s containers', self.name),:
                'company_id': self.company_id.id
            
            
            product = self.env['product.product'].create(product_vals)
            self.product_id = product.id
            
            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Product created successfully'),
                    'type': 'success'
                
            
        else:
            # Update existing product
            self.product_id.write({)}
                'name': self.name,
                'description': _('Storage service for %s containers', self.name):
            
            
            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Product updated successfully'),
                    'type': 'success'
                
            

    def action_generate_barcodes(self):
        """Generate barcodes for containers of this type""":
        self.ensure_one()
        
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Generate Barcodes'),
            'res_model': 'container.barcode.generator.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_container_type_id': self.id}
        

    def action_activate(self):
        """Activate container type"""
        for record in self:
            record.write({'state': 'active'})
            record.message_post(body=_("Container type activated"))

    def action_deactivate(self):
        """Deactivate container type"""
        for record in self:
            record.write({'state': 'inactive'})
            record.message_post(body=_("Container type deactivated"))

    def action_archive(self):
        """Archive container type"""
        for record in self:
            if record.active_containers > 0:
                raise UserError(_("Cannot archive container type with active containers"))
            
            record.write({'state': 'archived', 'active': False})
            record.message_post(body=_("Container type archived"))

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    def get_utilization_report(self):
        """Get utilization statistics for this container type""":
        self.ensure_one()
        
        containers = self.env['records.container'].search([)]
            ('container_type', '=', self.container_type_code)
        
        
        total_volume = len(containers) * self.volume_cubic_feet
        locations = containers.mapped('location_id')
        
        return {}
            'container_type': self.name,
            'total_containers': len(containers),
            'active_containers': len(containers.filtered('active')),
            'total_volume': total_volume,
            'locations_used': len(locations),
            'customer_count': len(containers.mapped('partner_id')),
            'monthly_revenue': self.monthly_revenue
        

    def get_revenue_forecast(self, months=12):
        """Get revenue forecast for this container type""":
        self.ensure_one()
        
        # Simple growth calculation based on recent trends
        current_revenue = self.monthly_revenue
        
        # Calculate growth rate from last 6 months
        forecast_data = []
        for month in range(1, months + 1):
            # Simple linear growth model - can be enhanced with ML
            projected_revenue = current_revenue * (1 + 0.5 * month)  # 5% growth assumption
            forecast_data.append({)}
                'month': month,
                'projected_revenue': projected_revenue,
                'container_type': self.name
            
        
        return forecast_data

    @api.model
    def get_container_type_analytics(self):
        """Get analytics for all container types""":
        container_types = self.search([('active', '=', True)])
        
        analytics = {}
            'total_types': len(container_types),
            'total_containers': sum(container_types.mapped('container_count')),
            'total_revenue': sum(container_types.mapped('monthly_revenue')),
            'type_breakdown': []
        
        
        for container_type in container_types:
            analytics['type_breakdown'].append({)}
                'name': container_type.name,
                'code': container_type.container_type_code,
                'containers': container_type.container_count,
                'revenue': container_type.monthly_revenue,
                'customers': container_type.customer_count
            
        
        return analytics

    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_effective_rate(self, customer=None):
        """Get effective rate for this container type for a specific customer""":
        self.ensure_one()
        
        if customer:
            # Check for customer-specific rates:
            negotiated_rate = self.env['customer.negotiated.rates'].search([)]
                ('partner_id', '=', customer.id),
                ('container_type', '=', self.container_type_code),
                ('active', '=', True)
            
            
            if negotiated_rate:
                return negotiated_rate.monthly_rate
        
        # Fall back to base rate
        return self.base_monthly_rate

    def calculate_monthly_billing(self, customer, container_count):
        """Calculate monthly billing for a customer""":
        self.ensure_one()
        
        rate = self.get_effective_rate(customer)
        subtotal = rate * container_count
        
        # Apply volume discounts if applicable:
        billing_profile = customer.billing_profile_id
        if billing_profile and billing_profile.volume_discount_enabled:
            if container_count >= billing_profile.volume_discount_threshold:
                discount = subtotal * (billing_profile.volume_discount_percentage / 100)
                subtotal -= discount
        
        return {}
            'rate': rate,
            'container_count': container_count,
            'subtotal': subtotal,
            'total': subtotal + self.handling_fee
        

    def validate_container_specifications(self):
        """Validate container specifications against business rules"""
        self.ensure_one()
        
        # Business validation rules
        if self.container_type_code == 'type_01' and self.volume_cubic_feet != 1.2:
            return False, _('TYPE 1 containers must have exactly 1.2 cubic feet volume')
        
        if self.container_type_code == 'type_02' and self.volume_cubic_feet != 2.4:
            return False, _('TYPE 2 containers must have exactly 2.4 cubic feet volume')
        
        if self.container_type_code == 'type_06' and self.volume_cubic_feet != 0.42:
            return False, _('TYPE 6 containers must have exactly 0.42 cubic feet volume')
        
        return True, _('Specifications are valid')

    # ============================================================================
        # INTEGRATION METHODS
    # ============================================================================
    def sync_with_product_catalog(self):
        """Synchronize with product catalog"""
        self.ensure_one()
        
        if not self.product_id:
            self.action_create_product()
        else:
            # Update product information
            self.product_id.write({)}
                'name': self.name,
                'description': _('Storage service for %s containers', self.name),:
                'active': self.active
            
        
        return True

    @api.model
    def import_container_specifications(self, specifications_data):
        """Import container specifications from external data"""
        created_types = []
        
        for spec_data in specifications_data:
            # Create or update container type
            existing = self.search([)]
                ('code', '=', spec_data.get('code')),
                ('company_id', '=', self.env.company.id)
            
            
            if existing:
                existing.write(spec_data)
                created_types.append(existing)
            else:
                new_type = self.create(spec_data)
                created_types.append(new_type)
        
        return created_types
))))))))))))))))))))))))