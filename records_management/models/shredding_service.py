from odoo import fields, models, api

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add mail threading for chatter
    _order = 'service_date desc, name'

    # Basic identification
    name = fields.Char(
        string='Service Reference', 
        required=True, 
        default='New', 
        tracking=True
    )
    
    # Status workflow
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    
    # Customer and scheduling
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today, tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    
    # Service details
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True, tracking=True)
    
    # Box management
    total_boxes = fields.Integer(
        string='Total Boxes', 
        compute='_compute_total_boxes', 
        store=True
    )
    box_quantity = fields.Integer(string='Box Quantity')
    
    # Costs
    unit_cost = fields.Float(string='Unit Cost', default=5.0)
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True
    )
    
    # Company support
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Notes
    notes = fields.Text(string='Notes')

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True)
    bin_ids = fields.Many2many(
        'stock.lot',
        'shredding_service_bin_rel',
        'service_id',
        'lot_id',
        string='Serviced Bins',
        domain=[('product_id.name', '=', 'Shredding Bin')]
    )
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many(
        'stock.lot',
        'shredding_service_box_rel',
        'service_id',
        'lot_id',
        string='Shredded Boxes',
        domain=[('customer_id', '!=', False)]
    )
    audit_barcodes = fields.Text(string='Audit Barcodes')
    total_charge = fields.Float(
        string='Total Charge',
        compute='_compute_total_charge',
        store=True
    )
    timestamp = fields.Datetime(string='Service Timestamp', default=fields.Datetime.now)
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    map_display = fields.Char(
        compute='_compute_map_display',
        string='Map'
    )

    @api.depends('service_type', 'bin_ids', 'box_quantity', 'shredded_box_ids')
    def _compute_total_charge(self):
        for record in self:
            if record.service_type == 'bin':
                record.total_charge = len(record.bin_ids) * 10.0  # $10 per bin
            else:
                qty = record.box_quantity or len(record.shredded_box_ids)
                record.total_charge = qty * 5.0  # $5 per box

    @api.depends('latitude', 'longitude')
    def _compute_map_display(self):
        for record in self:
            if record.latitude and record.longitude:
                record.map_display = "%s,%s" % (record.latitude, record.longitude)
            else:
                record.map_display = ''

    @api.depends('box_quantity', 'shredded_box_ids')
    def _compute_total_boxes(self):
        for record in self:
            if record.service_type == 'box':
                record.total_boxes = record.box_quantity or len(record.shredded_box_ids)
            else:
                record.total_boxes = 0

    @api.depends('total_boxes', 'unit_cost', 'bin_ids')
    def _compute_total_cost(self):
        for record in self:
            if record.service_type == 'bin':
                record.total_cost = len(record.bin_ids) * 10.0  # $10 per bin
            else:
                record.total_cost = record.total_boxes * record.unit_cost

    # Action methods for workflow
    def action_confirm(self):
        """Confirm the shredding service"""
        for record in self:
            record.status = 'confirmed'
        return True

    def action_start(self):
        """Start the shredding service"""
        for record in self:
            record.status = 'in_progress'
        return True

    def action_complete(self):
        """Complete the shredding service"""
        for record in self:
            record.status = 'completed'
        return True

    def action_cancel(self):
        """Cancel the shredding service"""
        for record in self:
            record.status = 'cancelled'
        return True

    # Create override for sequence
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('shredding.service')
                    or 'New'
                )
        return super().create(vals_list)
