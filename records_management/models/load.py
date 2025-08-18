from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Load(models.Model):
    _name = 'load'
    _description = 'Paper Bale Load Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_ship_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Load Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('loading', 'Loading'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('sold', 'Sold'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, copy=False)

    load_type = fields.Selection([
        ('outbound', 'Outbound'),
        ('inbound', 'Inbound')
    ], string='Load Type', default='outbound', required=True)

    # Logistical Information
    trailer_id = fields.Many2one(
        'maintenance.equipment',
        string='Trailer',
        domain="[('category_id.name', '=', 'Trailer')]"
    )
    driver_id = fields.Many2one('hr.employee', string='Driver')

    # Dates
    date_created = fields.Datetime(string='Creation Date', default=fields.Datetime.now, readonly=True)
    loading_start_date = fields.Datetime(string='Loading Start Date')
    loading_end_date = fields.Datetime(string='Loading End Date')
    scheduled_ship_date = fields.Date(string='Scheduled Ship Date')
    actual_ship_date = fields.Date(string='Actual Ship Date')
    estimated_delivery_date = fields.Date(string='Estimated Delivery Date')
    actual_delivery_date = fields.Date(string='Actual Delivery Date')

    # Destination & Pickup
    destination_partner_id = fields.Many2one('res.partner', string='Destination/Buyer')
    pickup_location_id = fields.Many2one('stock.location', string='Pickup Location')
    delivery_address = fields.Text(string='Delivery Address', compute='_compute_delivery_address', readonly=True, store=True)

    # Contents
    paper_bale_ids = fields.One2many('paper.bale', 'load_id', string='Paper Bales')
    total_bales = fields.Integer(string='Total Bales', compute='_compute_load_stats', store=True)
    current_weight = fields.Float(string='Total Weight (lbs)', compute='_compute_load_stats', store=True)
    weight_utilization = fields.Float(string='Weight Utilization (%)', compute='_compute_weight_utilization')

    # Financials
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    estimated_revenue = fields.Monetary(string='Estimated Revenue')
    actual_revenue = fields.Monetary(string='Actual Revenue')
    transportation_cost = fields.Monetary(string='Transportation Cost')
    fuel_cost = fields.Monetary(string='Fuel Cost')
    total_costs = fields.Monetary(string='Total Costs', compute='_compute_financials', store=True)
    net_profit = fields.Monetary(string='Net Profit', compute='_compute_financials', store=True)

    # Quality Control
    quality_grade = fields.Selection([
        ('wht', 'White (WHT)'),
        ('mix', 'Mixed (MIX)'),
        ('occ', 'Cardboard (OCC)'),
        ('trash', 'Trash (TRASH)')
    ], string='Paper Type')
    
    # Bale Management
    has_burst_bales = fields.Boolean(string='Has Burst Bales', default=False)
    burst_bale_count = fields.Integer(string='Burst Bales Count', default=0)
    reprocessing_required = fields.Boolean(string='Reprocessing Required', compute='_compute_reprocessing_required', store=True)
    
    exclude_trash_from_tracking = fields.Boolean(string='Exclude Trash from Market Tracking', default=True)
    
    contamination_level = fields.Float(string='Contamination Level (%)')
    moisture_content = fields.Float(string='Moisture Content (%)')
    quality_inspection_passed = fields.Boolean(string='QC Passed')
    inspection_notes = fields.Text(string='Inspection Notes')

    # Attachments
    bill_of_lading = fields.Binary(string='Bill of Lading')
    weight_ticket = fields.Binary(string='Weight Ticket')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('paper.bale.load')
                if not seq:
                    raise UserError(_("The sequence 'paper.bale.load' is missing. Please create it in Settings > Technical > Sequences."))
                vals['name'] = seq
        return super().create(vals_list)

    @api.depends('paper_bale_ids', 'paper_bale_ids.weight')
    def _compute_load_stats(self):
        for load in self:
            load.total_bales = len(load.paper_bale_ids)
            load.current_weight = sum(load.paper_bale_ids.mapped('weight'))

    @api.depends('current_weight', 'trailer_id.max_weight_capacity')
    def _compute_weight_utilization(self):
        for load in self:
            if load.trailer_id and load.trailer_id.max_weight_capacity > 0:
                load.weight_utilization = (load.current_weight / load.trailer_id.max_weight_capacity) * 100
            else:
                load.weight_utilization = 0.0

    @api.depends('transportation_cost', 'fuel_cost', 'actual_revenue')
    def _compute_financials(self):
        for load in self:
            load.total_costs = (load.transportation_cost or 0.0) + (load.fuel_cost or 0.0)
            load.net_profit = (load.actual_revenue or 0.0) - load.total_costs

    @api.depends('destination_partner_id')
    def _compute_delivery_address(self):
        for load in self:
            if load.destination_partner_id:
                address = load.destination_partner_id._display_address()
                load.delivery_address = address if address else False
            else:
                load.delivery_address = False

    @api.depends('has_burst_bales', 'burst_bale_count')
    def _compute_reprocessing_required(self):
        for load in self:
            load.reprocessing_required = load.has_burst_bales and load.burst_bale_count > 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_plan(self):
        self.ensure_one()
        self.write({'state': 'planned'})

    def action_start_loading(self):
        self.ensure_one()
        self.write({
            'state': 'loading',
            'loading_start_date': fields.Datetime.now()
        })

    def action_finish_loading(self):
        self.ensure_one()
        self.write({
            'state': 'in_transit',
            'loading_end_date': fields.Datetime.now(),
            'actual_ship_date': fields.Date.context_today(self)
        })

    def action_deliver(self):
        self.ensure_one()
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Date.context_today(self)
        })

    def action_mark_sold(self):
        self.ensure_one()
        self.write({'state': 'sold'})

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})

    def action_discard_burst_bales(self):
        self.ensure_one()
        if not self.has_burst_bales:
            raise UserError(_("No burst bales identified for this load."))
        
        burst_bales = self.paper_bale_ids.filtered(lambda b: b.is_burst)
        for bale in burst_bales:
            bale.write({
                'state': 'discarded',
                'discard_reason': 'Burst bale - requires reprocessing',
                'discard_date': fields.Datetime.now()
            })
        
        self.message_post(
            body=_("Discarded %d burst bale(s) for reprocessing. Bale numbers freed for reuse.", len(burst_bales))
        )
        
        return True

    def action_exclude_trash_bales(self):
        self.ensure_one()
        trash_bales = self.paper_bale_ids.filtered(lambda b: b.paper_type == 'trash')
        trash_bales.write({'exclude_from_market_tracking': True})
        
        self.message_post(
            body=_("Excluded %d TRASH bale(s) from market tracking.", len(trash_bales))
        )
        
        return True
