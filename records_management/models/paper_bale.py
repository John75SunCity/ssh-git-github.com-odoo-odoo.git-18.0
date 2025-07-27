# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Core fields
    name = fields.Char('Bale Reference', required=True, default='/')
    description = fields.Text('Description')
    
    # Relationship fields
    shredding_id = fields.Many2one('shredding.service', string='Shredding Service',
                                   help='The shredding service this bale is associated with'
    
    # Weight and measurement
    weight_kg = fields.Float('Weight (kg', digits=(10, 2))
    volume_m3 = fields.Float('Volume (m³)', digits=(10, 3))
    
    # Status and tracking
    state = fields.Selection([
        ('draft', 'Draft',
        ('ready', 'Ready for Processing'),
        ('processed', 'Processed'),
        ('shipped', 'Shipped'),
        ('complete', 'Complete')
    
    # Dates), string="Selection Field"
    creation_date = fields.Datetime('Creation Date', default=fields.Datetime.now)
    processing_date = fields.Datetime('Processing Date')
    shipping_date = fields.Datetime('Shipping Date')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company
    active = fields.Boolean('Active', default=True)
    
    # PHASE 4: Critical Business Fields (69 fields - Paper Recycling Enhanced
    
    # Action and lifecycle tracking
    action_date = fields.Date('Action Date', tracking=True)
    action_type = fields.Selection([
        ('created', 'Created'),
        ('weighed', 'Weighed'),
        ('graded', 'Graded'),
        ('loaded', 'Loaded'),
        ('shipped', 'Shipped'),
        ('processed', 'Processed')
    
    # Bale identification and status), string="Selection Field"
    bale_number = fields.Char('Bale Number', required=True, tracking=True)
    bale_status = fields.Selection([
        ('new', 'New'),
        ('in_production', 'In Production'),
        ('quality_check', 'Quality Check'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped')
    
    # Environmental and sustainability metrics), string="Selection Field"
    carbon_footprint_saved = fields.Float('Carbon Footprint Saved (kg CO2)', compute='_compute_environmental_metrics', store=True)
    carbon_neutral = fields.Boolean('Carbon Neutral', default=False)
    energy_saved = fields.Float('Energy Saved (kWh)', compute='_compute_environmental_metrics', store=True)
    trees_saved_equivalent = fields.Float('Trees Saved Equivalent', compute='_compute_environmental_metrics', store=True)
    water_saved = fields.Float('Water Saved (gallons)', compute='_compute_environmental_metrics', store=True)
    environmental_certification = fields.Selection([
        ('none', 'None'),
        ('recycled_content', 'Recycled Content'),
        ('sustainable_forestry', 'Sustainable Forestry'),
        ('carbon_neutral', 'Carbon Neutral'),
        ('zero_waste', 'Zero Waste'), string="Selection Field")
    sustainable_source = fields.Boolean('Sustainable Source', default=True)
    
    # Compliance and verification
    chain_of_custody_verified = fields.Boolean('Chain of Custody Verified', default=False, tracking=True)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'), string="Selection Field")
    naid_compliance_verified = fields.Boolean('NAID Compliance Verified', default=False, tracking=True)
    
    # Contamination and quality control
    contamination_found = fields.Boolean('Contamination Found', default=False, tracking=True)
    contamination_level = fields.Selection([
        ('none', 'None'),
        ('minimal', 'Minimal'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('rejected', 'Rejected'), string="Selection Field")
    contamination_percentage = fields.Float('Contamination Percentage (%)', default=0.0)
    
    # Customer and source tracking
    customer_name = fields.Char('Customer Name', related='shredding_id.customer_id.name', store=True)
    source_facility = fields.Char('Source Facility')
    source_document_ids = fields.Many2many('records.document', 
                                          relation='paper_bale_document_rel',
                                          string='Source Documents')  # Fixed to Many2many with shorter table name
    
    # Document tracking
    destruction_date = fields.Date('Destruction Date', tracking=True)
    document_count = fields.Integer('Document Count', compute='_compute_document_metrics', store=True)
    document_name = fields.Char('Document Name/Type')
    document_type = fields.Selection([
        ('office', 'Office Paper'),
        ('newspaper', 'Newspaper'),
        ('magazine', 'Magazine'),
        ('cardboard', 'Cardboard'),
        ('mixed', 'Mixed Paper')
    
    # Financial tracking), string="Selection Field"
    estimated_value = fields.Float('Estimated Value ($)', compute='_compute_financial_metrics', store=True)
    market_price_per_lb = fields.Float('Market Price per Lb ($)', default=0.05)
    processing_cost = fields.Float('Processing Cost ($)', default=0.0)
    revenue_potential = fields.Float('Revenue Potential ($)', compute='_compute_financial_metrics', store=True)
    
    # Quality and grading
    grade_assigned = fields.Selection([
        ('grade_1', 'Grade 1 - Premium',
        ('grade_2', 'Grade 2 - Standard'),
        ('grade_3', 'Grade 3 - Lower'),
        ('mixed', 'Mixed Grade'),
        ('reject', 'Reject'), string="Selection Field")
    paper_grade = fields.Selection([
        ('oinp', 'OINP - Office Paper'),
        ('onp', 'ONP - Old Newspaper'),
        ('occ', 'OCC - Old Corrugated'),
        ('mixed', 'Mixed Paper'),
        ('white_ledger', 'White Ledger'), string="Selection Field")
    paper_type = fields.Selection([
        ('white_office', 'White Office Paper'),
        ('colored_office', 'Colored Office Paper'),
        ('computer_paper', 'Computer Paper'),
        ('newspaper', 'Newspaper'),
        ('magazine', 'Magazine'),
        ('cardboard', 'Cardboard'), string="Selection Field")
    quality_grade = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'), string="Selection Field")
    quality_score = fields.Float('Quality Score (1-10)', default=7.0)
    
    # Inspection and quality control
    inspection_date = fields.Date('Inspection Date', tracking=True)
    inspection_type = fields.Selection([
        ('visual', 'Visual Inspection'),
        ('sample', 'Sample Testing'),
        ('full', 'Full Inspection'),
        ('random', 'Random Check'), string="Selection Field")
    inspector = fields.Many2one('res.users', string='Inspector')
    passed_inspection = fields.Boolean('Passed Inspection', default=False, tracking=True)
    quality_inspection_ids = fields.Many2many('paper.bale.quality.inspection', relation='quality_inspection_ids_rel', string='Quality Inspections')  # Fixed: was One2many with missing inverse field)
    quality_inspector = fields.Many2one('res.users', string='Quality Inspector')
    quality_notes = fields.Text('Quality Notes')
    
    # Loading and logistics
    loaded_by = fields.Many2one('res.users', string='Loaded By')
    loaded_on_trailer = fields.Boolean('Loaded on Trailer', default=False, tracking=True)
    loading_date = fields.Date('Loading Date', tracking=True)
    loading_history_ids = fields.Many2many('paper.bale.loading.history', relation='loading_history_ids_rel', string='Loading History')  # Fixed: was One2many with missing inverse field)
    loading_notes = fields.Text('Loading Notes')
    loading_order = fields.Integer('Loading Order', default=1)
    loading_position = fields.Char('Loading Position')
    trailer_id = fields.Many2one('fleet.vehicle', string='Trailer', domain="[('category_id.name', '=', 'Trailer')]")
    trailer_info = fields.Char('Trailer Information')
    trailer_load_count = fields.Integer('Trailer Load Count', default=0)
    
    # Measurement and weighing
    measured_by = fields.Many2one('res.users', string='Measured By')
    measurement_date = fields.Date('Measurement Date', tracking=True)
    measurement_type = fields.Selection([
        ('estimated', 'Estimated'),
        ('scale', 'Scale Measurement'),
        ('certified', 'Certified Measurement'), string="Selection Field")
    moisture_content = fields.Float('Moisture Content (%)', default=0.0)
    moisture_reading = fields.Float('Moisture Reading', default=0.0)
    scale_used = fields.Char('Scale Used for Weighing')
    weigh_date = fields.Date('Weigh Date', tracking=True)
    weighed_by = fields.Many2one('res.users', string='Weighed By')
    
    # Weight tracking and metrics
    weight = fields.Float('Weight (lbs', default=0.0, tracking=True)
    weight_contributed = fields.Float('Weight Contributed (lbs)', default=0.0)
    weight_efficiency = fields.Float('Weight Efficiency (%)', compute='_compute_weight_metrics', store=True)
    weight_history_count = fields.Integer('Weight History Count', compute='_compute_weight_metrics', store=True)
    weight_measurement_ids = fields.Many2many('paper.bale.weight.measurement', relation='weight_measurement_ids_rel', string='Weight Measurements')  # Fixed: was One2many with missing inverse field)
    weight_recorded = fields.Float('Weight Recorded (lbs', default=0.0, tracking=True)
    weight_unit = fields.Selection([
        ('lbs', 'Pounds'),
        ('kg', 'Kilograms'),
        ('tons', 'Tons'), string="Selection Field")
    variance_from_previous = fields.Float('Variance from Previous (%)', compute='_compute_weight_metrics', store=True)
    
    # Personnel and processing
    performed_by = fields.Many2one('res.users', string='Performed By')
    processing_time = fields.Float('Processing Time (hours)', default=0.0)
    special_handling = fields.Boolean('Special Handling Required', default=False)
    
    # Contextual field (from analysis
    notes = fields.Text('Notes')
    
    # Compute methods for the new fields
    @api.depends('weight', 'document_count', 'paper_type'
    def _compute_environmental_metrics(self):
        """Compute environmental impact metrics"""
        for record in self:
            # Environmental calculations based on paper recycling standards
            weight_kg = record.weight * 0.453592  # Convert lbs to kg
            
            # Carbon footprint savings (industry standard: 1.1 kg CO2 per kg paper
            record.carbon_footprint_saved = weight_kg * 1.1
            
            # Energy savings (industry standard: 4100 kWh per ton
            record.energy_saved = (weight_kg / 1000) * 4100
            
            # Trees saved (industry standard: 17 trees per ton
            record.trees_saved_equivalent = (weight_kg / 1000) * 17
            
            # Water saved (industry standard: 7000 gallons per ton
            record.water_saved = (weight_kg / 1000) * 7000
    
    @api.depends('weight', 'market_price_per_lb', 'processing_cost')
    def _compute_financial_metrics(self):
        """Compute financial metrics"""
        for record in self:
            # Revenue potential based on weight and market price
            record.revenue_potential = record.weight * record.market_price_per_lb
            
            # Estimated value after processing costs
            record.estimated_value = record.revenue_potential - record.processing_cost
    
    @api.depends('source_document_ids'
    def _compute_document_metrics(self):
        """Compute document-related metrics"""
        for record in self:
            record.document_count = len(record.source_document_ids)
    
    @api.depends('weight', 'weight_measurement_ids')
    def _compute_weight_metrics(self):
        """Compute weight-related metrics"""
        for record in self:
            measurements = record.weight_measurement_ids
            record.weight_history_count = len(measurements)
            
            if len(measurements) > 1:
                previous_weight = measurements[-2].weight if len(measurements) > 1 else record.weight
                if previous_weight > 0:
                    record.variance_from_previous = ((record.weight - previous_weight) / previous_weight) * 100
                else:
                    record.variance_from_previous = 0.0
            else:
                record.variance_from_previous = 0.0
            
            # Weight efficiency based on processing
            if record.weight > 0:
                record.weight_efficiency = (record.weight_contributed / record.weight * 100
            else:
                record.weight_efficiency = 0.0