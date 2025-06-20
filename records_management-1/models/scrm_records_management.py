"""
Odoo manifest dictionary has been removed from this Python file.
Please place the manifest dictionary in a separate __manifest__.py file as required by Odoo module structure.
"""
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, AccessError
from odoo import http
from odoo.http import request

# Constant for the pickup request form field name
PICKUP_ITEM_IDS_FIELD = 'item_ids'

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    customer_id = fields.Many2one('res.partner', string='Customer')

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    
    service_date = fields.Date(string='Service Date', default=lambda self: fields.Date.today())
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True)
    bin_ids = fields.Many2many('stock.production.lot', string='Serviced Bins', 
                               domain=[('product_id.name', '=', 'Shredding Bin')])
    box_quantity = fields.Integer(string='Number of Boxes', default=0)
    shredded_box_ids = fields.Many2many('stock.production.lot', string='Shredded Boxes', 
                                        domain=[('customer_id', '!=', False)])
    audit_barcodes = fields.Text(string='Audit Barcodes')
    total_charge = fields.Float(string='Total Charge', compute='_compute_total_charge')
    timestamp = fields.Datetime(string='Service Timestamp', default=lambda self: fields.Datetime.now())
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    map_display = fields.Char(compute='_compute_map_display', string='Map')

    @api.constrains('box_quantity')
    def _check_box_quantity(self):
        for rec in self:
            if rec.service_type == 'box' and (rec.box_quantity is None or rec.box_quantity < 1):
                raise ValidationError(_("Box quantity must be a positive integer for box shredding."))

    @api.constrains('latitude', 'longitude')
    def _check_lat_long(self):
        for rec in self:
            if rec.latitude and not (-90 <= rec.latitude <= 90):
                raise ValidationError(_("Latitude must be between -90 and 90."))
            if rec.longitude and not (-180 <= rec.longitude <= 180):
                raise ValidationError(_("Longitude must be between -180 and 180."))

    @api.depends('service_type', 'bin_ids', 'box_quantity', 'shredded_box_ids')
    def _compute_total_charge(self):
        for record in self:
            if record.service_type == 'bin':
                record.total_charge = len(record.bin_ids) * 10.0
            else:
                qty = record.box_quantity or len(record.shredded_box_ids) or 0
                record.total_charge = qty * 5.0

    @api.depends('latitude', 'longitude')
    def _compute_map_display(self):
        for record in self:
            record.map_display = f"{record.latitude},{record.longitude}"

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    item_ids = fields.Many2many('stock.production.lot', string='Items', 
                                domain="[('customer_id', '=', customer_id)]")

    @api.model
    def create_pickup_request(self, partner, item_ids):
        if not item_ids:
            raise ValidationError(_("No items selected for pickup."))
        items = self.env['stock.production.lot'].search([
            ('id', 'in', item_ids),
            ('customer_id', '=', partner.id)
        ])
        if not items:
            raise ValidationError(_("Selected items are invalid or do not belong to you."))
        return self.create({
            'customer_id': partner.id,
            'item_ids': [(6, 0, items.ids)],
        })