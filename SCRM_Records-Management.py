from . import stock_production_lot
from . import shredding_service
from . import pickup_request
from . import stock_picking
from odoo import fields, models
from odoo import fields, models, api
from odoo import fields, models
from odoo import api, models
from . import portal
from odoo import http
from odoo.http import request
from collections import defaultdict

# records_management/__manifest__.py
{
    'name': 'Records Management',
    'version': '1.0',
    'summary': 'Manage customer inventory and shredding services',
    'depends': ['stock', 'sale', 'website', 'maintenance'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/products.xml',
        'data/scheduled_actions.xml',
        'views/shredding_views.xml',
        'views/pickup_views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/js/map_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
} # type: ignore

# records_management/models/__init__.py

# records_management/models/stock_production_lot.py

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    customer_id = fields.Many2one('res.partner', string='Customer')

# records_management/models/shredding_service.py

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Document Shredding Service'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'),
        ('box', 'Box Shredding')
    ], string='Service Type', required=True)
    bin_ids = fields.Many2many('stock.production.lot', string='Serviced Bins', 
                               domain=[('product_id.name', '=', 'Shredding Bin')])
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many('stock.production.lot', string='Shredded Boxes', 
                                        domain=[('customer_id', '!=', False)])
    audit_barcodes = fields.Text(string='Audit Barcodes')
    total_charge = fields.Float(string='Total Charge', compute='_compute_total_charge')
    timestamp = fields.Datetime(string='Service Timestamp', default=fields.Datetime.now)
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    map_display = fields.Char(compute='_compute_map_display', string='Map')

    @api.depends('service_type', 'bin_ids', 'box_quantity', 'shredded_box_ids')
    def _compute_total_charge(self):
        for record in self:
            if record.service_type == 'bin':
                record.total_charge = len(record.bin_ids) * 10.0
            else:
                qty = record.box_quantity or len(record.shredded_box_ids)
                record.total_charge = qty * 5.0

    def _compute_map_display(self):
        for record in self:
            record.map_display = f"{record.latitude},{record.longitude}"

# records_management/models/pickup_request.py

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], default='draft', string='Status')
    item_ids = fields.Many2many('stock.production.lot', string='Items', 
                                domain="[('customer_id', '=', customer_id)]")

# records_management/models/stock_picking.py

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        if self.state == 'done' and self.picking_type_id.code == 'outgoing':
            customer_items = self.move_line_ids.filtered(lambda ml: ml.lot_id.customer_id)
            if customer_items:
                customer = customer_items[0].lot_id.customer_id
                self.env['sale.order'].create({
                    'partner_id': customer.id,
                    'order_line': [(0, 0, {
                        'product_id': self.env.ref('records_management.retrieval_fee_product').id,
                        'product_uom_qty': len(customer_items),
                    })],
                })
        return res

# records_management/controllers/__init__.py

# records_management/controllers/portal.py

class InventoryPortal(http.Controller):
    @http.route('/my/inventory', type='http', auth='user', website=True)
    def inventory(self, **kw):
        partner = request.env.user.partner_id
        serials = request.env['stock.production.lot'].search([('customer_id', '=', partner.id)])
        quants = request.env['stock.quant'].search([
            ('lot_id', 'in', serials.ids), 
            ('location_id.usage', '=', 'internal')
        ])
        return request.render('records_management.inventory_template', {'quants': quants})

    @http.route('/my/request_pickup', type='http', auth='user', website=True, methods=['POST'])
    def request_pickup(self, **post):
        partner = request.env.user.partner_id
        item_ids = [int(id) for id in request.httprequest.form.getlist('item_ids')]
        items = request.env['stock.production.lot'].search([
            ('id', 'in', item_ids),
            ('customer_id', '=', partner.id)
        ])
        if items:
            request.env['pickup.request'].create({
                'customer_id': partner.id,
                'item_ids': [(6, 0, items.ids)],
            })
        return request.redirect('/my/inventory')

# records_management/views/templates.xml
<odoo>
    <template id="inventory_template" name="My Inventory">
        <t t-call="website.layout">
            <div class="container">
                <h2>My Inventory</h2>
                <form action="/my/request_pickup" method="post">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Select</th>
                                <th>Product</th>
                                <th>Serial Number</th>
                                <th>Location</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="quants" t-as="quant">
                                <tr>
                                    <td>
                                        <input type="checkbox" name="item_ids" t-att-value="quant.lot_id.id"/>
                                    </td>
                                    <td><t t-esc="quant.product_id.display_name"/></td>
                                    <td><t t-esc="quant.lot_id.name"/></td>
                                    <td><t t-esc="quant.location_id.display_name"/></td>
                                </tr>
                            </t>
                        </tbody>
                    </table>
                    <button type="submit" class="btn btn-primary">Request Check-Out for Selected Items</button>
                </form>
            </div>
        </t>
    </template>
</odoo>

# records_management/views/shredding_views.xml
<odoo>
    <record id="view_shredding_service_form" model="ir.ui.view">
        <field name="name">shredding.service.form</field>
        <field name="model">shredding.service</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="customer_id"/>
                        <field name="service_date"/>
                        <field name="service_type"/>
                        <field name="bin_ids"/>
                        <field name="box_quantity"/>
                        <field name="shredded_box_ids"/>
                        <field name="audit_barcodes"/>
                        <field name="total_charge" readonly="1"/>
                        <field name="timestamp"/>
                        <field name="latitude"/>
                        <field name="longitude"/>
                        <field name="attachment_ids" widget="many2many_binary"/>
                        <field name="map_display" widget="map_widget" options="{'latitude_field': 'latitude', 'longitude_field': 'longitude'}"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>

# records_management/views/pickup_views.xml
<odoo>
    <record id="view_pickup_request_form" model="ir.ui.view">
        <field name="name">pickup.request.form</field>
        <field name="model">pickup.request</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="customer_id"/>
                        <field name="request_date"/>
                        <field name="state"/>
                        <field name="item_ids"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>

# records_management/data/products.xml
<odoo>
    <record id="box_product" model="product.product">
        <field name="name">Box</field>
        <field name="type">product</field>
        <field name="tracking">serial</field>
    </record>
    <record id="file_product" model="product.product">
        <field name="name">File</field>
        <field name="type">product</field>
        <field name="tracking">serial</field>
    </record>
    <record id="shredding_bin_product" model="product.product">
        <field name="name">Shredding Bin</field>
        <field name="type">product</field>
        <field name="tracking">serial</field>
    </record>
    <record id="retrieval_fee_product" model="product.product">
        <field name="name">Retrieval Fee</field>
        <field name="type">service</field>
        <field name="list_price">10.0</field>
    </record>
    <record id="storage_fee_product" model="product.product">
        <field name="name">Storage Fee</field>
        <field name="type">service</field>
        <field name="list_price">5.0</field>
    </record>
</odoo>

# records_management/data/scheduled_actions.xml
<odoo>
    <record id="ir_cron_storage_fees" model="ir.cron">
        <field name="name">Compute Monthly Storage Fees</field>
        <field name="model_id" ref="base.model_ir_cron"/>
        <field name="state">code</field>
        <field name="code">
            quants = env['stock.quant'].search([('location_id.usage', '=', 'internal'), ('lot_id.customer_id', '!=', False)])
            customer_items = defaultdict(int)
            for quant in quants:
                customer = quant.lot_id.customer_id
                if customer:
                    customer_items[customer] += 1
            for customer, qty in customer_items.items():
                env['sale.order'].create({
                    'partner_id': customer.id,
                    'order_line': [(0, 0, {
                        'product_id': env.ref('records_management.storage_fee_product').id,
                        'product_uom_qty': qty,
                    })],
                })
        </field>
        <field name="interval_number">1</field>
        <field name="interval_type">months</field>
        <field name="numbercall">-1</field>
    </record>
</odoo>

# records_management/security/groups.xml
<odoo>
    <record id="group_warehouse_manager" model="res.groups">
        <field name="name">Warehouse Manager</field>
    </record>
    <record id="group_shredding_technician" model="res.groups">
        <field name="name">Shredding Technician</field>
    </record>
    <record id="group_customer_service" model="res.groups">
        <field name="name">Customer Service</field>
    </record>
</odoo>

# records_management/security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_stock_production_lot_manager,access.stock.production.lot.manager,model_stock_production_lot,group_warehouse_manager,1,1,1,1
access_stock_production_lot_cs,access.stock.production.lot.cs,model_stock_production_lot,group_customer_service,1,0,0,0
access_shredding_service_tech,access.shredding.service.tech,model_shredding_service,group_shredding_technician,1,1,1,1
access_shredding_service_cs,access.shredding.service.cs,model_shredding_service,group_customer_service,1,0,0,0
access_pickup_request_cs,access.pickup.request.cs,model_pickup_request,group_customer_service,1,1,1,1
access_pickup_request_manager,access.pickup.request.manager,model_pickup_request,group_warehouse_manager,1,0,0,0

# records_management/static/src/js/map_widget.js
odoo.define('records_management.map_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var MapWidget = AbstractField.extend({
        className: 'map_widget',
        _render: function () {
            this.$el.html('<div class="map_container" style="width:100%;height:300px"></div>');
            var latitude = this.recordData[this.options.latitude_field];
            var longitude = this.recordData[this.options.longitude_field];
            if (latitude && longitude && window.google && window.google.maps) {
                var map = new google.maps.Map(this.$('.map_container')[0], {
                    center: { lat: latitude, lng: longitude },
                    zoom: 15
                });
                new google.maps.Marker({
                    position: { lat: latitude, lng: longitude },
                    map: map
                });
            } else {
                this.$('.map_container').html('<span>No location set</span>');
            }
            return this._super();
        }
    });

    fieldRegistry.add('map_widget', MapWidget);

    return MapWidget;
});