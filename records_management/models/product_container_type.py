from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductContainerType(models.Model):
    _name = 'product.container.type'
    _description = 'Product Container Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'sequence, name'

    # ============================================================================
    # CORE & SPECIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Type Name", required=True, tracking=True)
    code = fields.Char(string="Type Code", required=True, tracking=True, help="Unique code for this container type (e.g., 'BOX01').")
    product_id = fields.Many2one('product.product', string="Related Service Product", ondelete='restrict', help="Service product used for billing this container type.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)

    # --- Physical Specs ---
    volume_cubic_feet = fields.Float(string="Volume (cu ft)", digits=(12, 4), tracking=True)
    average_weight_lbs = fields.Float(string="Average Weight (lbs)", tracking=True)
    max_weight_lbs = fields.Float(string="Max Weight (lbs)", tracking=True)
    length_inches = fields.Float(string="Length (in)")
    width_inches = fields.Float(string="Width (in)")
    height_inches = fields.Float(string="Height (in)")
    dimensions_display = fields.Char(string="Dimensions", compute='_compute_dimensions_display', store=True)
    
    # --- Categorization ---
    usage_category = fields.Selection([
        ('general', 'General Documents'),
        ('legal', 'Legal/Financial'),
        ('medical', 'Medical Records'),
        ('blueprints', 'Blueprints/Maps'),
        ('temporary', 'Temporary/Odd Size'),
    ], string="Usage Category", default='general', tracking=True)
    document_capacity = fields.Integer(string="Est. Document Capacity", help="Estimated number of standard documents this container can hold.")

    # ============================================================================
    # BILLING & FINANCIAL FIELDS
    # ============================================================================
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    base_monthly_rate = fields.Monetary(string="Base Monthly Rate", currency_field='currency_id', tracking=True)
    setup_fee = fields.Monetary(string="Setup Fee", currency_field='currency_id')
    handling_fee = fields.Monetary(string="Handling Fee", currency_field='currency_id')

    # ============================================================================
    # OPERATIONAL FIELDS
    # ============================================================================
    barcode_prefix = fields.Char(string="Barcode Prefix", help="Prefix for generating new container barcodes of this type.")
    requires_special_handling = fields.Boolean(string="Requires Special Handling", tracking=True)
    climate_controlled_only = fields.Boolean(string="Climate Controlled Only", tracking=True)
    security_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('vault', 'Vault'),
    ], string="Security Level", default='medium', tracking=True)

    # ============================================================================
    # COMPUTED STATS FIELDS
    # ============================================================================
    container_count = fields.Integer(string="Total Containers", compute='_compute_usage_stats', store=True)
    active_containers = fields.Integer(string="Active Containers", compute='_compute_usage_stats', store=True)
    monthly_revenue = fields.Monetary(string="Est. Monthly Revenue", compute='_compute_usage_stats', store=True)
    customer_count = fields.Integer(string="Active Customers", compute='_compute_usage_stats', store=True)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('code', 'company_id')
    def _check_unique_code(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('company_id', '=', record.company_id.id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Container code must be unique per company.'))

    @api.constrains('volume_cubic_feet', 'average_weight_lbs', 'max_weight_lbs')
    def _check_positive_values(self):
        for record in self:
            if record.volume_cubic_feet <= 0:
                raise ValidationError(_('Volume must be a positive number.'))
            if record.average_weight_lbs < 0 or record.max_weight_lbs < 0:
                raise ValidationError(_('Weights cannot be negative.'))
            if record.max_weight_lbs and record.max_weight_lbs < record.average_weight_lbs:
                raise ValidationError(_('Maximum weight must be greater than or equal to average weight.'))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('length_inches', 'width_inches', 'height_inches')
    def _compute_dimensions_display(self):
        for record in self:
            if record.length_inches and record.width_inches and record.height_inches:
                record.dimensions_display = _('%.1f" L x %.1f" W x %.1f" H') % (record.length_inches, record.width_inches, record.height_inches)
            else:
                record.dimensions_display = _('N/A')

    @api.depends('code', 'base_monthly_rate')
    def _compute_usage_stats(self):
        # This method is resource-intensive. It's better to run it via a scheduled action
        # or trigger it manually. For simplicity, it's a compute method here.
        container_obj = self.env['records.container']
        for record_type in self:
            domain = [('container_type_id', '=', record_type.id)]
            all_containers = container_obj.search(domain)
            active_containers = all_containers.filtered('active')
            
            record_type.container_count = len(all_containers)
            record_type.active_containers = len(active_containers)
            record_type.monthly_revenue = record_type.active_containers * record_type.base_monthly_rate
            record_type.customer_count = len(active_containers.mapped('partner_id'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers - %s') % self.name,
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('container_type_id', '=', self.id)],
            'context': {
                'default_container_type_id': self.id,
                'default_company_id': self.company_id.id
            }
        }

    def action_update_stats(self):
        """Manually trigger the recalculation of statistics."""
        self.ensure_one()
        self._compute_usage_stats()
        return True
