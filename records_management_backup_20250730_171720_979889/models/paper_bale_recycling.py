# -*- coding: utf-8 -*-
"""
Paper Bale Recycling - Internal Waste Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaperBaleRecycling(models.Model):
    """
    Paper Bale Recycling - Internal Operations
    Tracks shredded paper waste baling and sale to recycling companies
    This is purely internal operations - not tied to customer documents
    """

    _name = "paper.bale.recycling"
    _description = "Paper Bale Recycling"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "bale_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Bale Number", required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Recycling Manager',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)

    # ==========================================
    # BALE BASICS
    # ==========================================
    bale_date = fields.Date(string='Bale Date', default=fields.Date.today, 
                           required=True, tracking=True)
    
    # Weight measurements
    gross_weight = fields.Float(string='Gross Weight (lbs)', required=True, tracking=True)
    tare_weight = fields.Float(string='Tare Weight (lbs)', tracking=True)
    net_weight = fields.Float(string='Net Weight (lbs)', compute='_compute_net_weight', 
                             store=True, tracking=True)

    # ==========================================
    # PROCESSING STATUS
    # ==========================================
    state = fields.Selection([
        ('baling', 'Baling'),
        ('ready', 'Ready for Pickup'),
        ('shipped', 'Shipped'),
        ('invoiced', 'Invoiced')
    ], string='Status', default='baling', tracking=True, required=True)

    # ==========================================
    # RECYCLING PARTNER AND SALE
    # ==========================================
    recycling_partner_id = fields.Many2one('res.partner', string='Recycling Company',
                                          domain=[('supplier_rank', '>', 0)], tracking=True)
    pickup_date = fields.Date(string='Pickup Date', tracking=True)
    
    # Pricing
    price_per_ton = fields.Float(string='Price per Ton ($)', tracking=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_total_revenue',
                                store=True, tracking=True)
    action_assign_to_load = fields.Char(string='Action Assign To Load')
    action_mark_delivered = fields.Char(string='Action Mark Delivered')
    action_mark_paid = fields.Char(string='Action Mark Paid')
    action_ready_to_ship = fields.Char(string='Action Ready To Ship')
    action_ship_bale = fields.Char(string='Action Ship Bale')
    action_store_bale = fields.Char(string='Action Store Bale')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    assigned_load = fields.Char(string='Assigned Load')
    bale_number = fields.Char(string='Bale Number')
    basic_info = fields.Char(string='Basic Info')
    card = fields.Char(string='Card')
    cardboard = fields.Char(string='Cardboard')
    contamination = fields.Char(string='Contamination')
    contamination_notes = fields.Char(string='Contamination Notes')
    delivered = fields.Char(string='Delivered')
    display_name = fields.Char(string='Display Name')
    gps_coordinates = fields.Char(string='Gps Coordinates')
    group_load_shipment = fields.Char(string='Group Load Shipment')
    group_paper_grade = fields.Char(string='Group Paper Grade')
    group_production_date = fields.Date(string='Group Production Date')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    group_weighed_by = fields.Char(string='Group Weighed By')
    help = fields.Char(string='Help')
    load_info = fields.Char(string='Load Info')
    load_number = fields.Char(string='Load Number')
    load_shipment_id = fields.Many2one('load.shipment', string='Load Shipment Id')
    location_info = fields.Char(string='Location Info')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    mixed_paper = fields.Char(string='Mixed Paper')
    mobile_entry = fields.Char(string='Mobile Entry')
    moisture_level = fields.Char(string='Moisture Level')
    paid = fields.Char(string='Paid')
    paper_grade = fields.Char(string='Paper Grade')
    processed_from_service = fields.Char(string='Processed From Service')
    produced = fields.Char(string='Produced')
    production_date = fields.Date(string='Production Date')
    quality_info = fields.Char(string='Quality Info')
    ready_ship = fields.Char(string='Ready Ship')
    res_model = fields.Char(string='Res Model')
    scale_reading = fields.Char(string='Scale Reading')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    shipped = fields.Char(string='Shipped')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    storage_location = fields.Char(string='Storage Location')
    stored = fields.Char(string='Stored')
    system_info = fields.Char(string='System Info')
    this_month = fields.Char(string='This Month')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    view_mode = fields.Char(string='View Mode')
    weighed_by = fields.Char(string='Weighed By')
    weight_info = fields.Char(string='Weight Info')
    weight_kg = fields.Char(string='Weight Kg')
    weight_lbs = fields.Char(string='Weight Lbs')
    white_paper = fields.Char(string='White Paper')

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('gross_weight', 'tare_weight')
    def _compute_net_weight(self):
        """Calculate net weight"""
        for record in self:
            record.net_weight = record.gross_weight - (record.tare_weight or 0.0)

    @api.depends('net_weight', 'price_per_ton')
    def _compute_total_revenue(self):
        """Calculate total revenue from bale"""
        for record in self:
            if record.net_weight and record.price_per_ton:
                tons = record.net_weight / 2000  # Convert lbs to tons
                record.total_revenue = tons * record.price_per_ton
            else:
                record.total_revenue = 0.0

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_mark_ready(self):
        """Mark bale as ready for pickup"""
        self.ensure_one()
        if self.state != 'baling':
            raise UserError(_('Only baling status can be marked ready'))
        
        if not self.gross_weight:
            raise UserError(_('Weight must be recorded'))
        
        self.write({'state': 'ready'})
        self.message_post(body=_('Bale ready for pickup'))

    def action_schedule_pickup(self):
        """Schedule pickup with recycling company"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Only ready bales can be scheduled for pickup'))
        
        if not self.recycling_partner_id:
            raise UserError(_('Recycling company must be selected'))
        
        self.message_post(body=_('Pickup scheduled with recycling company'))

    def action_confirm_shipped(self):
        """Confirm bale has been shipped"""
        self.ensure_one()
        if self.state != 'ready':
            raise UserError(_('Only ready bales can be shipped'))
        
        self.write({
            'state': 'shipped',
            'pickup_date': fields.Date.today()
        })
        
        self.message_post(body=_('Bale shipped to recycling company'))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.recycling') or _('New')
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('gross_weight', 'tare_weight')
    def _check_weights(self):
        """Validate weight measurements"""
        for record in self:
            if record.tare_weight and record.gross_weight:
                if record.tare_weight >= record.gross_weight:
                    raise ValidationError(_('Tare weight cannot be greater than or equal to gross weight'))