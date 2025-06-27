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

    # Reference to the customer (res.partner) associated with this lot.
    customer_id = fields.Many2one('res.partner', string='Customer')

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    service_date = fields.Date(string='Service Date', default=lambda self: fields.Date.today())

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today)
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
        """
        Compute the total charge based on service type and quantities.

        Returns:
            None
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

        Returns:
            None
        """
        for record in self:
            record.map_display = f"{record.latitude},{record.longitude}"

class PickupRequest(models.Model):
    """
    Represents a pickup request for items associated with a customer.

    Args:
        customer_id (Many2one): Reference to the customer (res.partner) making the pickup request.
        request_date (Date): The date the pickup request was created.
        state (Selection): The current status of the pickup request.
        item_ids (Many2many): List of items (stock.production.lot) included in the pickup request.
    """
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
        """
        Create a pickup request for the given partner and item_ids.

        Args:
            partner (res.partner): The customer.
            item_ids (list): List of stock.production.lot ids.

        Returns:
            pickup.request record or None
        Raises:
            ValidationError: If no items are provided.
        """
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

# --- HTTP Controller ---

class InventoryPortal(http.Controller):
    def _get_partner(self):
        """Helper to get the current user's partner."""
        partner = request.env.user.partner_id
        if not partner:
            raise AccessError(_("No partner associated with this user."))
        return partner

    def _get_serials(self, partner):
        """Helper to get serials for a partner."""
        return request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])

    def _get_quants(self, serials):
        """Helper to get quants for serials in internal locations."""
        # Batch if serials are many
        if len(serials) > 1000:
            ids_batches = [serials.ids[i:i+1000] for i in range(0, len(serials), 1000)]
            quants = request.env['stock.quant']
            for batch in ids_batches:
                quants |= request.env['stock.quant'].search([
                    ('lot_id', 'in', batch),
                    ('location_id.usage', '=', 'internal')
                ])
            return quants
        return request.env['stock.quant'].search([
            ('lot_id', 'in', serials.ids), 
            ('location_id.usage', '=', 'internal')
        ])

    @http.route('/my/inventory', type='http', auth='user', website=True)
    def inventory(self, **kw):
        """
        Render the inventory of stock quants associated with the current user's partner.

        Returns:
            werkzeug.wrappers.Response: The rendered inventory template.
        """
        partner = self._get_partner()
        serials = self._get_serials(partner)
        quants = self._get_quants(serials)
        return request.render('records_management.inventory_template', {'quants': quants})

    @http.route('/my/request_pickup', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def request_pickup(self, **post):
        """
        Handle pickup request form submission and rendering.

        Returns:
            werkzeug.wrappers.Response: Redirect or rendered form.
        """
        partner = self._get_partner()
        error = None
        if request.httprequest.method == 'POST':
            try:
                # Sanitize and validate item_ids
                raw_ids = request.httprequest.form.getlist(PICKUP_ITEM_IDS_FIELD)
                item_ids = [int(id) for id in raw_ids if id.isdigit()]
                if not item_ids:
                    error = _("Please select at least one item for pickup.")
                else:
                    request.env['pickup.request'].sudo().create_pickup_request(partner, item_ids)
                    return request.redirect('/my/inventory')
            except (ValidationError, Exception) as e:
                error = str(e)
        # Render the pickup request form for GET requests or on error
        serials = self._get_serials(partner)
        return request.render('records_management.pickup_request_form', {
            'serials': serials,
            'error': error,
            'pickup_item_ids_field': PICKUP_ITEM_IDS_FIELD,
            'partner': partner,
            'pickup_request': request.env['pickup.request'].new({
                'customer_id': partner.id,
                PICKUP_ITEM_IDS_FIELD: [(6, 0, [])]  # Initialize with empty list
            }),
            'pickup_item_ids_field_name': PICKUP_ITEM_IDS_FIELD,
            'pickup_item_ids_field_label': _('Items for Pickup'),
            'pickup_item_ids_field_help': _('Select items to request for pickup.'),
            'pickup_item_ids_field_required': True,
            'pickup_item_ids_field_domain': [('customer_id', '=', partner.id)],         

# --- Placeholders for test coverage (to be implemented in test modules) ---
# def test_compute_total_charge(self): ...
# def test_compute_map_display(self): ...
# def test_inventory_route(self): ...
# def test_request_pickup_route(self): ...
# def test_inventory_route(self): ...
# def test_request_pickup_route(self): ...
        })