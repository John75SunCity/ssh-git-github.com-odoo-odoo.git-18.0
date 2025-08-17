from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class Load(models.Model):
    _name = 'load'
    _description = 'Paper Bale Load Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Load Number', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    description = fields.Text(string='Load Description')
    sequence = fields.Integer(string='Sequence')
    state = fields.Selection()
    load_type = fields.Selection()
    trailer_id = fields.Many2one()
    driver_id = fields.Many2one()
    current_weight = fields.Float()
    weight_utilization = fields.Float()
    date_created = fields.Datetime()
    loading_start_date = fields.Datetime(string='Loading Start Date')
    loading_end_date = fields.Datetime(string='Loading End Date')
    scheduled_ship_date = fields.Date(string='Scheduled Ship Date')
    actual_ship_date = fields.Date(string='Actual Ship Date')
    estimated_delivery_date = fields.Date()
    actual_delivery_date = fields.Date(string='Actual Delivery Date')
    destination_partner_id = fields.Many2one()
    pickup_location = fields.Char(string='Pickup Location')
    delivery_address = fields.Text(string='Delivery Address')
    special_delivery_instructions = fields.Text(string='Special Delivery Instructions')
    route_optimization = fields.Boolean(string='Route Optimization')
    estimated_distance = fields.Float(string='Estimated Distance (miles)')
    estimated_fuel_cost = fields.Float(string='Estimated Fuel Cost')
    paper_bale_ids = fields.One2many()
    total_bales = fields.Integer(string='Total Bales')
    mixed_paper_weight = fields.Float(string='Mixed Paper Weight (lbs)')
    cardboard_weight = fields.Float(string='Cardboard Weight (lbs)')
    white_paper_weight = fields.Float(string='White Paper Weight (lbs)')
    confidential_weight = fields.Float(string='Confidential Weight (lbs)')
    currency_id = fields.Many2one()
    estimated_revenue = fields.Monetary()
    actual_revenue = fields.Monetary()
    transportation_cost = fields.Monetary()
    fuel_cost = fields.Monetary(string='Fuel Cost')
    total_costs = fields.Monetary()
    net_profit = fields.Monetary()
    quality_grade = fields.Selection()
    contamination_level = fields.Float(string='Contamination Level (%)')
    moisture_content = fields.Float(string='Moisture Content (%)')
    quality_inspection_passed = fields.Boolean()
    inspection_notes = fields.Text(string='Inspection Notes')
    bill_of_lading = fields.Binary()
    weight_ticket = fields.Binary(string='Weight Ticket')
    quality_certificate = fields.Binary(string='Quality Certificate')
    delivery_receipt = fields.Binary(string='Delivery Receipt')
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    action_cancel = fields.Char(string='Action Cancel')
    action_mark_sold = fields.Char(string='Action Mark Sold')
    action_prepare_load = fields.Char(string='Action Prepare Load')
    action_ship_load = fields.Char(string='Action Ship Load')
    action_start_loading = fields.Char(string='Action Start Loading')
    action_view_bales = fields.Char(string='Action View Bales')
    action_view_revenue_report = fields.Char(string='Action View Revenue Report')
    action_view_weight_tickets = fields.Char(string='Action View Weight Tickets')
    activity_exception_decoration = fields.Char(string='Activity Exception Decoration')
    activity_state = fields.Selection(string='Activity State')
    actual_delivery = fields.Char(string='Actual Delivery')
    actual_sale_price = fields.Float(string='Actual Sale Price')
    author_id = fields.Many2one('author')
    average_bale_weight = fields.Float(string='Average Bale Weight')
    bale_count = fields.Integer(string='Bale Count')
    bale_ids = fields.One2many('bale')
    bale_number = fields.Char(string='Bale Number')
    button_box = fields.Char(string='Button Box')
    buyer_company = fields.Char(string='Buyer Company')
    capacity_utilization = fields.Char(string='Capacity Utilization')
    card = fields.Char(string='Card')
    communication = fields.Char(string='Communication')
    contamination_notes = fields.Char(string='Contamination Notes')
    contamination_report = fields.Char(string='Contamination Report')
    context = fields.Char(string='Context')
    date = fields.Char(string='Date')
    delivered = fields.Char(string='Delivered')
    delivery_contact = fields.Char(string='Delivery Contact')
    delivery_date = fields.Date(string='Delivery Date')
    delivery_phone = fields.Char(string='Delivery Phone')
    destination_address = fields.Char(string='Destination Address')
    documentation = fields.Char(string='Documentation')
    draft = fields.Char(string='Draft')
    driver_name = fields.Char(string='Driver Name')
    estimated_delivery = fields.Char(string='Estimated Delivery')
    group_date = fields.Date(string='Group Date')
    group_driver = fields.Char(string='Group Driver')
    group_priority = fields.Selection(string='Group Priority')
    group_route = fields.Char(string='Group Route')
    group_state = fields.Selection(string='Group State')
    group_trailer = fields.Char(string='Group Trailer')
    hazmat = fields.Char(string='Hazmat')
    hazmat_required = fields.Boolean(string='Hazmat Required')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    image = fields.Char(string='Image')
    in_transit = fields.Char(string='In Transit')
    invoice_number = fields.Char(string='Invoice Number')
    late_delivery = fields.Char(string='Late Delivery')
    load_date = fields.Date(string='Load Date')
    load_details = fields.Char(string='Load Details')
    load_items = fields.Char(string='Load Items')
    load_quality_grade = fields.Char(string='Load Quality Grade')
    loading = fields.Char(string='Loading')
    loading_dock_requirements = fields.Char(string='Loading Dock Requirements')
    market_details = fields.Char(string='Market Details')
    market_price_per_ton = fields.Char(string='Market Price Per Ton')
    message_type = fields.Selection(string='Message Type')
    moisture_test_report = fields.Char(string='Moisture Test Report')
    my_loads = fields.Char(string='My Loads')
    overdue = fields.Char(string='Overdue')
    payment_terms = fields.Char(string='Payment Terms')
    photo_ids = fields.One2many('photo')
    photo_type = fields.Selection(string='Photo Type')
    planned = fields.Char(string='Planned')
    price_variance = fields.Char(string='Price Variance')
    production_date = fields.Date(string='Production Date')
    res_model = fields.Char(string='Res Model')
    route_code = fields.Char(string='Route Code')
    sale_contract_number = fields.Char(string='Sale Contract Number')
    sales_contract_number = fields.Char(string='Sales Contract Number')
    search_view_id = fields.Many2one('search.view')
    shipping = fields.Char(string='Shipping')
    shipping_date = fields.Date(string='Shipping Date')
    special_instructions = fields.Char(string='Special Instructions')
    subject = fields.Char(string='Subject')
    temp_controlled = fields.Char(string='Temp Controlled')
    temperature_controlled = fields.Char(string='Temperature Controlled')
    today = fields.Char(string='Today')
    total_weight = fields.Float(string='Total Weight')
    tracking = fields.Char(string='Tracking')
    trailer_number = fields.Char(string='Trailer Number')
    transport_company = fields.Char(string='Transport Company')
    truck_license_plate = fields.Char(string='Truck License Plate')
    value_per_ton = fields.Char(string='Value Per Ton')
    view_mode = fields.Char(string='View Mode')
    week = fields.Char(string='Week')
    weight = fields.Char(string='Weight')
    weight_certificate = fields.Char(string='Weight Certificate')
    weight_ticket_count = fields.Integer(string='Weight Ticket Count')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_bale_count(self):
            for record in self:""
                record.bale_count = len(record.bale_ids)""

    def _compute_total_weight(self):
            for record in self:""
                record.total_weight = sum(record.line_ids.mapped('amount'))""

    def _compute_weight_ticket_count(self):
            for record in self:""
                record.weight_ticket_count = len(record.weight_ticket_ids)""

    def _compute_current_weight(self):
            for record in self:""
                record.current_weight = sum(record.paper_bale_ids.mapped("weight"))

    def _compute_weight_utilization(self):
            for record in self:""
                if record.max_weight_capacity > 0:""
                    record.weight_utilization = ()""
                        record.current_weight / record.max_weight_capacity""
                    ""
                else:""
                    record.weight_utilization = 0.0""

    def _compute_total_bales(self):
            for record in self:""
                record.total_bales = len(record.paper_bale_ids)""

    def _compute_total_costs(self):
            for record in self:""
                record.total_costs = (record.transportation_cost or 0.0) + ()""
                    record.fuel_cost or 0.0""
                ""

    def _compute_net_profit(self):
            for record in self:""
                record.net_profit = (record.actual_revenue or 0.0) - ()""
                    record.total_costs or 0.0""
                ""

    def create(self, vals_list):
            for vals in vals_list:""
                if not vals.get("name"):
                    vals["name") = self.env["ir.sequence"].next_by_code("load") or "LOAD/"
            return super().create(vals_list)""
