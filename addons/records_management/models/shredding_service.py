from odoo import fields, models, api

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True)
    bin_ids = fields.Many2many(
        'stock.production.lot',
        string='Serviced Bins',
        domain=[('product_id.name', '=', 'Shredding Bin')]
    )
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many(
        'stock.production.lot',
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
                record.map_display = f"{record.latitude},{record.longitude}"
            else:
                record.map_display = ''
