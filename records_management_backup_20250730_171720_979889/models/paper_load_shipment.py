# -*- coding: utf-8 -*-
"""
Paper Load Shipment
"""

from odoo import models, fields, api, _


class PaperLoadShipment(models.Model):
    """
    Paper Load Shipment
    """

    _name = "paper.load.shipment"
    _description = "Paper Load Shipment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    action_add_bales_to_load = fields.Char(string='Action Add Bales To Load')
    action_create_invoice = fields.Char(string='Action Create Invoice')
    action_generate_manifest = fields.Char(string='Action Generate Manifest')
    action_mark_delivered = fields.Char(string='Action Mark Delivered')
    action_mark_in_transit = fields.Char(string='Action Mark In Transit')
    action_mark_paid = fields.Char(string='Action Mark Paid')
    action_ready_for_pickup = fields.Char(string='Action Ready For Pickup')
    action_schedule_pickup = fields.Char(string='Action Schedule Pickup')
    action_view_manifest = fields.Char(string='Action View Manifest')
    action_view_weight_breakdown = fields.Char(string='Action View Weight Breakdown')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    bale_count = fields.Integer(string='Bale Count', compute='_compute_bale_count', store=True)
    bale_ids = fields.One2many('bale', 'paper_load_shipment_id', string='Bale Ids')
    bale_number = fields.Char(string='Bale Number')
    bales = fields.Char(string='Bales')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    cardboard_count = fields.Integer(string='Cardboard Count', compute='_compute_cardboard_count', store=True)
    cardboard_weight = fields.Float(string='Cardboard Weight', digits=(12, 2))
    company_signature_date = fields.Date(string='Company Signature Date')
    customer_id = fields.Many2one('res.partner', string='Customer Id', domain=[('is_company', '=', True)])
    delivered = fields.Char(string='Delivered')
    delivery_notes = fields.Char(string='Delivery Notes')
    destination_address = fields.Char(string='Destination Address')
    display_name = fields.Char(string='Display Name')
    draft = fields.Char(string='Draft')
    driver_license = fields.Char(string='Driver License')
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    driver_signature_date = fields.Date(string='Driver Signature Date')
    gps_delivery_location = fields.Char(string='Gps Delivery Location')
    gps_pickup_location = fields.Char(string='Gps Pickup Location')
    grade_breakdown = fields.Char(string='Grade Breakdown')
    group_customer = fields.Char(string='Group Customer')
    group_driver = fields.Char(string='Group Driver')
    group_pickup_date = fields.Date(string='Group Pickup Date')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    help = fields.Char(string='Help')
    in_transit = fields.Char(string='In Transit')
    invoice_amount = fields.Float(string='Invoice Amount', digits=(12, 2))
    invoice_date = fields.Date(string='Invoice Date')
    invoiced = fields.Char(string='Invoiced')
    load_number = fields.Char(string='Load Number')
    load_summary = fields.Char(string='Load Summary')
    manifest_date = fields.Date(string='Manifest Date')
    manifest_generated = fields.Char(string='Manifest Generated')
    manifest_number = fields.Char(string='Manifest Number')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    mixed_paper_count = fields.Integer(string='Mixed Paper Count', compute='_compute_mixed_paper_count', store=True)
    mixed_paper_weight = fields.Float(string='Mixed Paper Weight', digits=(12, 2))
    mobile_entry = fields.Char(string='Mobile Entry')
    mobile_integration = fields.Char(string='Mobile Integration')
    mobile_manifest = fields.Char(string='Mobile Manifest')
    paid = fields.Char(string='Paid')
    paper_grade = fields.Char(string='Paper Grade')
    payment_amount = fields.Float(string='Payment Amount', digits=(12, 2))
    payment_due_date = fields.Date(string='Payment Due Date')
    payment_notes = fields.Char(string='Payment Notes')
    payment_received_date = fields.Date(string='Payment Received Date')
    payment_tracking = fields.Char(string='Payment Tracking')
    pickup_date = fields.Date(string='Pickup Date')
    pickup_info = fields.Char(string='Pickup Info')
    pickup_time = fields.Float(string='Pickup Time', digits=(12, 2))
    production_date = fields.Date(string='Production Date')
    ready_pickup = fields.Char(string='Ready Pickup')
    res_model = fields.Char(string='Res Model')
    scheduled = fields.Char(string='Scheduled')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    signatures = fields.Char(string='Signatures')
    signed_by = fields.Char(string='Signed By')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    system_info = fields.Char(string='System Info')
    this_month = fields.Char(string='This Month')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    total_weight_kg = fields.Char(string='Total Weight Kg')
    total_weight_lbs = fields.Char(string='Total Weight Lbs')
    transportation = fields.Char(string='Transportation')
    transportation_company = fields.Char(string='Transportation Company')
    truck_info = fields.Char(string='Truck Info')
    truck_visualization = fields.Char(string='Truck Visualization')
    view_mode = fields.Char(string='View Mode')
    weighed_by = fields.Char(string='Weighed By')
    weight_lbs = fields.Char(string='Weight Lbs')
    white_paper_count = fields.Integer(string='White Paper Count', compute='_compute_white_paper_count', store=True)
    white_paper_weight = fields.Float(string='White Paper Weight', digits=(12, 2))

    @api.depends('bale_ids')
    def _compute_bale_count(self):
        for record in self:
            record.bale_count = len(record.bale_ids)

    @api.depends('cardboard_ids')
    def _compute_cardboard_count(self):
        for record in self:
            record.cardboard_count = len(record.cardboard_ids)

    @api.depends('mixed_paper_ids')
    def _compute_mixed_paper_count(self):
        for record in self:
            record.mixed_paper_count = len(record.mixed_paper_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_weight_kg(self):
        for record in self:
            record.total_weight_kg = sum(record.line_ids.mapped('amount'))

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_weight_lbs(self):
        for record in self:
            record.total_weight_lbs = sum(record.line_ids.mapped('amount'))

    @api.depends('white_paper_ids')
    def _compute_white_paper_count(self):
        for record in self:
            record.white_paper_count = len(record.white_paper_ids)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
