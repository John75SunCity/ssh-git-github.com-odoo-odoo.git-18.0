"""
Records Management Models
Contains the core business logic for the Records Management module.
"""
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'

    # Reference to the customer (res.partner) associated with this lot.
    customer_id = fields.Many2one('res.partner', string='Customer')


class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True)
    bin_ids = fields.Many2many('stock.lot', string='Serviced Bins', 
                               domain=[('product_id.name', '=', 'Shredding Bin')])
    box_quantity = fields.Integer(string='Number of Boxes', default=0)
    shredded_box_ids = fields.Many2many('stock.lot', string='Shredded Boxes', 
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
        """
        Compute the total charge based on service type and quantities.
        """
        for record in self:
            if record.service_type == 'bin':
                record.total_charge = len(record.bin_ids) * 10.0
            else:
                if record.box_quantity is not None:
                    qty = record.box_quantity
                else:
                    qty = len(record.shredded_box_ids) or 0
                record.total_charge = qty * 5.0

    @api.depends('latitude', 'longitude')
    def _compute_map_display(self):
        """
        Compute a string representation of the map location.
        """
        for record in self:
            record.map_display = f"{record.latitude},{record.longitude}"
