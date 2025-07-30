# -*- coding: utf-8 -*-
"""
Paper Bale
"""

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """
    Paper Bale
    """

    _name = "paper.bale"
    _description = "Paper Bale"
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
    action_date = fields.Date(string='Action Date')
    action_load_trailer = fields.Char(string='Action Load Trailer')
    action_move_to_storage = fields.Char(string='Action Move To Storage')
    action_print_label = fields.Char(string='Action Print Label')
    action_quality_inspection = fields.Char(string='Action Quality Inspection')
    action_type = fields.Selection([], string='Action Type')  # TODO: Define selection options
    action_view_inspection_details = fields.Char(string='Action View Inspection Details')
    action_view_source_documents = fields.Char(string='Action View Source Documents')
    action_view_trailer_info = fields.Char(string='Action View Trailer Info')
    action_view_weight_history = fields.Char(string='Action View Weight History')
    action_weigh_bale = fields.Char(string='Action Weigh Bale')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    analytics = fields.Char(string='Analytics')
    bale_number = fields.Char(string='Bale Number')
    bale_status = fields.Selection([], string='Bale Status')  # TODO: Define selection options
    button_box = fields.Char(string='Button Box')
    carbon_footprint_saved = fields.Char(string='Carbon Footprint Saved')
    carbon_neutral = fields.Char(string='Carbon Neutral')
    card = fields.Char(string='Card')
    chain_of_custody_verified = fields.Boolean(string='Chain Of Custody Verified', default=False)
    confidentiality_level = fields.Char(string='Confidentiality Level')
    contamination_found = fields.Char(string='Contamination Found')
    contamination_level = fields.Char(string='Contamination Level')
    contamination_percentage = fields.Char(string='Contamination Percentage')
    context = fields.Char(string='Context')
    created = fields.Char(string='Created')
    creation_date = fields.Date(string='Creation Date')
    customer_name = fields.Char(string='Customer Name')
    destruction_date = fields.Date(string='Destruction Date')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count', store=True)
    document_name = fields.Char(string='Document Name')
    document_type = fields.Selection([], string='Document Type')  # TODO: Define selection options
    energy_saved = fields.Char(string='Energy Saved')
    environmental = fields.Char(string='Environmental')
    environmental_certification = fields.Char(string='Environmental Certification')
    estimated_value = fields.Char(string='Estimated Value')
    grade_a = fields.Char(string='Grade A')
    grade_assigned = fields.Char(string='Grade Assigned')
    grade_b = fields.Char(string='Grade B')
    grade_c = fields.Char(string='Grade C')
    group_by_date = fields.Date(string='Group By Date')
    group_by_grade = fields.Char(string='Group By Grade')
    group_by_paper_type = fields.Selection([], string='Group By Paper Type')  # TODO: Define selection options
    group_by_source = fields.Char(string='Group By Source')
    group_by_status = fields.Selection([], string='Group By Status')  # TODO: Define selection options
    group_by_trailer = fields.Char(string='Group By Trailer')
    help = fields.Char(string='Help')
    in_storage = fields.Char(string='In Storage')
    inspection_date = fields.Date(string='Inspection Date')
    inspection_type = fields.Selection([], string='Inspection Type')  # TODO: Define selection options
    inspector = fields.Char(string='Inspector')
    loaded = fields.Char(string='Loaded')
    loaded_by = fields.Char(string='Loaded By')
    loaded_on_trailer = fields.Char(string='Loaded On Trailer')
    loading_date = fields.Date(string='Loading Date')
    loading_history_ids = fields.One2many('loading.history', 'paper_bale_id', string='Loading History Ids')
    loading_notes = fields.Char(string='Loading Notes')
    loading_order = fields.Char(string='Loading Order')
    loading_position = fields.Char(string='Loading Position')
    market_price_per_lb = fields.Char(string='Market Price Per Lb')
    measured_by = fields.Char(string='Measured By')
    measurement_date = fields.Date(string='Measurement Date')
    measurement_type = fields.Selection([], string='Measurement Type')  # TODO: Define selection options
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    moisture_content = fields.Char(string='Moisture Content')
    moisture_reading = fields.Char(string='Moisture Reading')
    naid_compliance_verified = fields.Boolean(string='Naid Compliance Verified', default=False)
    on_trailer = fields.Char(string='On Trailer')
    paper_grade = fields.Char(string='Paper Grade')
    paper_type = fields.Selection([], string='Paper Type')  # TODO: Define selection options
    passed_inspection = fields.Char(string='Passed Inspection')
    performed_by = fields.Char(string='Performed By')
    processing_cost = fields.Char(string='Processing Cost')
    processing_time = fields.Float(string='Processing Time', digits=(12, 2))
    quality = fields.Char(string='Quality')
    quality_grade = fields.Char(string='Quality Grade')
    quality_inspection_ids = fields.One2many('quality.inspection', 'paper_bale_id', string='Quality Inspection Ids')
    quality_inspector = fields.Char(string='Quality Inspector')
    quality_notes = fields.Char(string='Quality Notes')
    quality_score = fields.Char(string='Quality Score')
    ready_loading = fields.Char(string='Ready Loading')
    res_model = fields.Char(string='Res Model')
    revenue_potential = fields.Char(string='Revenue Potential')
    scale_used = fields.Char(string='Scale Used')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    shipped = fields.Char(string='Shipped')
    source_document_ids = fields.One2many('records.document', 'paper_bale_id', string='Source Document Ids')
    source_documents = fields.Char(string='Source Documents')
    source_facility = fields.Char(string='Source Facility')
    special_handling = fields.Char(string='Special Handling')
    sustainable = fields.Char(string='Sustainable')
    sustainable_source = fields.Char(string='Sustainable Source')
    this_month = fields.Char(string='This Month')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    trailer_id = fields.Many2one('trailer', string='Trailer Id')
    trailer_info = fields.Char(string='Trailer Info')
    trailer_load_count = fields.Integer(string='Trailer Load Count', compute='_compute_trailer_load_count', store=True)
    trailer_loading = fields.Char(string='Trailer Loading')
    trees_saved_equivalent = fields.Char(string='Trees Saved Equivalent')
    variance_from_previous = fields.Char(string='Variance From Previous')
    view_mode = fields.Char(string='View Mode')
    water_saved = fields.Char(string='Water Saved')
    weigh_date = fields.Date(string='Weigh Date')
    weighed = fields.Char(string='Weighed')
    weighed_by = fields.Char(string='Weighed By')
    weight = fields.Char(string='Weight')
    weight_contributed = fields.Char(string='Weight Contributed')
    weight_efficiency = fields.Char(string='Weight Efficiency')
    weight_history = fields.Char(string='Weight History')
    weight_history_count = fields.Integer(string='Weight History Count', compute='_compute_weight_history_count', store=True)
    weight_measurement_ids = fields.One2many('weight.measurement', 'paper_bale_id', string='Weight Measurement Ids')
    weight_recorded = fields.Char(string='Weight Recorded')
    weight_unit = fields.Char(string='Weight Unit')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('trailer_load_ids')
    def _compute_trailer_load_count(self):
        for record in self:
            record.trailer_load_count = len(record.trailer_load_ids)

    @api.depends('weight_history_ids')
    def _compute_weight_history_count(self):
        for record in self:
            record.weight_history_count = len(record.weight_history_ids)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
