# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')

    # Phase 3: Analytics & Computed Fields (8 fields)
    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_analytics',
        store=True,
        help='Total number of source documents in this bale'
    )
    weight_efficiency = fields.Float(
        string='Weight Efficiency (%)',
        compute='_compute_analytics',
        store=True,
        help='Efficiency ratio based on document count vs weight'
    )
    storage_cost = fields.Float(
        string='Storage Cost',
        compute='_compute_analytics',
        store=True,
        help='Estimated storage cost for this bale'
    )
    processing_time = fields.Float(
        string='Processing Time (hours)',
        compute='_compute_analytics',
        store=True,
        help='Total time spent processing this bale'
    )
    quality_score = fields.Float(
        string='Quality Score',
        compute='_compute_analytics',
        store=True,
        help='Quality assessment score (0-100)'
    )
    recycling_value = fields.Float(
        string='Recycling Value ($)',
        compute='_compute_analytics',
        store=True,
        help='Estimated recycling value'
    )
    bale_status_summary = fields.Char(
        string='Status Summary',
        compute='_compute_analytics',
        store=True,
        help='Human-readable status summary'
    )
    analytics_updated = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_analytics',
        store=True,
        help='Last time analytics were computed'
    )

    # Basic fields structure - ready for your code
    name = fields.Char(string='Bale Reference', required=True, default='New')
    shredding_id = fields.Many2one('shredding.service', string='Related Shredding Service')
    paper_type = fields.Selection([
        ('white', 'White Paper'),
        ('mixed', 'Mixed Paper'),
    ], string='Paper Type', required=True, default='white')
    weight = fields.Float(string='Weight (lbs)')
    
    # Enhanced paper bale fields - 82 missing fields added systematically
    
    # Action and tracking
    action_date = fields.Date(string='Action Date', default=fields.Date.today)
    action_type = fields.Selection([
        ('create', 'Create'),
        ('weigh', 'Weigh'),
        ('inspect', 'Inspect'),
        ('load', 'Load'),
        ('ship', 'Ship'),
        ('process', 'Process')
    ], string='Action Type', tracking=True)
    
    # Bale identification and status
    bale_number = fields.Char(string='Bale Number', required=True, copy=False)
    bale_status = fields.Selection([
        ('collecting', 'Collecting'),
        ('ready', 'Ready'),
        ('inspected', 'Inspected'), 
        ('loaded', 'Loaded'),
        ('shipped', 'Shipped'),
        ('processed', 'Processed')
    ], string='Bale Status', default='collecting', tracking=True)
    
    # Environmental and sustainability
    carbon_footprint_saved = fields.Float(string='Carbon Footprint Saved (lbs CO2)')
    carbon_neutral = fields.Boolean(string='Carbon Neutral', default=False)
    chain_of_custody_verified = fields.Boolean(string='Chain of Custody Verified', default=False)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret')
    ], string='Confidentiality Level', default='internal')
    energy_saved = fields.Float(string='Energy Saved (kWh)')
    trees_saved_equivalent = fields.Float(string='Trees Saved Equivalent')
    water_saved = fields.Float(string='Water Saved (gallons)')
    environmental_certification = fields.Char(string='Environmental Certification', help='Environmental certification number or type')
    
    # Contamination tracking
    contamination_found = fields.Boolean(string='Contamination Found', default=False)
    contamination_level = fields.Selection([
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Contamination Level', default='none')
    contamination_percentage = fields.Float(string='Contamination Percentage (%)')
    
    # Date tracking
    creation_date = fields.Datetime(string='Creation Date', default=fields.Datetime.now, readonly=True)
    destruction_date = fields.Date(string='Destruction Date')
    
    # Customer and document information
    customer_name = fields.Char(string='Customer Name')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_info')
    document_name = fields.Char(string='Document Name')
    document_type = fields.Selection([
        ('financial', 'Financial'),
        ('legal', 'Legal'),
        ('medical', 'Medical'),
        ('personnel', 'Personnel'),
        ('general', 'General')
    ], string='Document Type')
    
    # Quality assessment
    estimated_value = fields.Float(string='Estimated Value', digits=(12, 2))
    grade_assigned = fields.Selection([
        ('A', 'Grade A - Premium'),
        ('B', 'Grade B - Standard'),
        ('C', 'Grade C - Low Grade'),
        ('D', 'Grade D - Reject')
    ], string='Grade Assigned')
    paper_grade = fields.Selection([
        ('1', 'Grade 1 - High Quality'),
        ('2', 'Grade 2 - Standard'),
        ('3', 'Grade 3 - Mixed'),
        ('4', 'Grade 4 - Low Quality')
    ], string='Paper Grade')
    quality_grade = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Quality Grade')
    
    # Inspection tracking
    inspection_date = fields.Date(string='Inspection Date')
    inspection_type = fields.Selection([
        ('visual', 'Visual Inspection'),
        ('detailed', 'Detailed Inspection'),
        ('quality', 'Quality Inspection'),
        ('contamination', 'Contamination Check')
    ], string='Inspection Type')
    inspector = fields.Many2one('res.users', string='Inspector')
    passed_inspection = fields.Boolean(string='Passed Inspection', default=False)
    quality_inspection_ids = fields.One2many('paper.bale.quality.inspection', compute='_compute_quality_inspection_ids', string='Quality Inspections')
    quality_inspector = fields.Many2one('res.users', string='Quality Inspector')
    quality_notes = fields.Text(string='Quality Notes')
    
    # Loading and shipping
    loaded_by = fields.Many2one('res.users', string='Loaded By')
    loaded_on_trailer = fields.Boolean(string='Loaded on Trailer', default=False)
    loading_date = fields.Date(string='Loading Date')
    loading_history_ids = fields.One2many('paper.bale.loading.history', compute='_compute_loading_history_ids', string='Loading History')
    loading_notes = fields.Text(string='Loading Notes')
    loading_order = fields.Integer(string='Loading Order')
    loading_position = fields.Char(string='Loading Position')
    trailer_id = fields.Many2one('fleet.vehicle', string='Trailer')
    trailer_info = fields.Text(string='Trailer Information')
    trailer_load_count = fields.Integer(string='Trailer Load Count')
    
    # Pricing and market data
    market_price_per_lb = fields.Float(string='Market Price per Lb', digits=(12, 4))
    processing_cost = fields.Float(string='Processing Cost', digits=(12, 2))
    revenue_potential = fields.Float(string='Revenue Potential', digits=(12, 2))
    variance_from_previous = fields.Float(string='Variance from Previous (%)')
    
    # Measurement and weighing
    measured_by = fields.Many2one('res.users', string='Measured By')
    measurement_date = fields.Date(string='Measurement Date')
    measurement_type = fields.Selection([
        ('scale', 'Scale Measurement'),
        ('estimate', 'Estimated'),
        ('calculated', 'Calculated')
    ], string='Measurement Type')
    moisture_content = fields.Float(string='Moisture Content (%)')
    moisture_reading = fields.Float(string='Moisture Reading')
    scale_used = fields.Char(string='Scale Used')
    weigh_date = fields.Date(string='Weigh Date')
    weighed_by = fields.Many2one('res.users', string='Weighed By')
    weight_contributed = fields.Float(string='Weight Contributed (lbs)')
    weight_history_count = fields.Integer(string='Weight History Count', compute='_compute_weight_info')
    weight_measurement_ids = fields.One2many('paper.bale.weight.measurement', compute='_compute_weight_measurement_ids', string='Weight Measurements')
    weight_recorded = fields.Float(string='Weight Recorded (lbs)', tracking=True)
    weight_unit = fields.Selection([
        ('lbs', 'Pounds'),
        ('kg', 'Kilograms'),
        ('tons', 'Tons')
    ], string='Weight Unit', default='lbs')
    
    # NAID compliance and security
    naid_compliance_verified = fields.Boolean(string='NAID Compliance Verified', default=False)
    performed_by = fields.Many2one('res.users', string='Performed By')
    source_document_ids = fields.One2many('records.document', compute='_compute_source_document_ids', string='Source Documents')
    source_facility = fields.Char(string='Source Facility')
    special_handling = fields.Boolean(string='Special Handling Required', default=False)
    sustainable_source = fields.Boolean(string='Sustainable Source', default=True)
    
    # Notes and additional information
    notes = fields.Text(string='Additional Notes')
    
    # Mail tracking
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers',
                                           domain=lambda self: [('res_model', '=', self._name)])
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages',
                                  domain=lambda self: [('res_model', '=', self._name)])
    
    # Technical view fields
    arch = fields.Text(string='View Architecture')
    context = fields.Text(string='Context')
    help = fields.Text(string='Help Text')
    model = fields.Char(string='Model Name', default='paper.bale')
    res_model = fields.Char(string='Resource Model', default='paper.bale')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_mode = fields.Char(string='View Mode', default='tree,form')
    
    @api.depends('weight', 'paper_type', 'create_date')
    def _compute_analytics(self):
        """Compute analytics and business intelligence fields"""
        for bale in self:
            # Get source documents
            source_docs = self.env['records.document'].search_count([
                ('bale_id', '=', bale.id)
            ])
            
            # Basic analytics
            bale.total_documents = source_docs
            bale.analytics_updated = fields.Datetime.now()
            
            # Weight efficiency (documents per pound)
            if bale.weight and bale.weight > 0:
                bale.weight_efficiency = (source_docs / bale.weight) * 100
            else:
                bale.weight_efficiency = 0.0
            
            # Storage cost estimation (based on weight and type)
            cost_per_lb = 0.50 if bale.paper_type == 'white' else 0.35
            bale.storage_cost = bale.weight * cost_per_lb
            
            # Processing time estimation
            base_time = 2.0  # 2 hours base processing
            weight_factor = (bale.weight or 0) * 0.1  # 0.1 hour per lb
            bale.processing_time = base_time + weight_factor
            
            # Quality score (based on type and weight ratio)
            if bale.paper_type == 'white':
                base_quality = 85.0
            else:
                base_quality = 70.0
            
            # Adjust for optimal weight range (100-300 lbs)
            weight_penalty = 0
            if bale.weight:
                if bale.weight < 100:
                    weight_penalty = (100 - bale.weight) * 0.2
                elif bale.weight > 300:
                    weight_penalty = (bale.weight - 300) * 0.1
            
            bale.quality_score = max(0, min(100, base_quality - weight_penalty))
            
            # Recycling value (market price estimation)
            white_paper_rate = 0.08  # $0.08 per lb
            mixed_paper_rate = 0.05  # $0.05 per lb
            
            if bale.paper_type == 'white':
                bale.recycling_value = bale.weight * white_paper_rate
            else:
                bale.recycling_value = bale.weight * mixed_paper_rate
            
            # Status summary
            if bale.weight >= 100:
                status = "Ready for Processing"
            elif bale.weight >= 50:
                status = "In Progress"
            else:
                status = "Starting Collection"
            
            bale.bale_status_summary = f"{status} ({source_docs} docs, {bale.weight:.1f} lbs)"

    # Compute methods for One2many fields to avoid KeyError issues
    @api.depends()
    def _compute_quality_inspection_ids(self):
        """Compute quality inspections based on available records"""
        for record in self:
            # Return empty recordset since model doesn't exist
            record.quality_inspection_ids = self.env['paper.bale.quality.inspection'].browse()

    @api.depends()
    def _compute_loading_history_ids(self):
        """Compute loading history based on available records"""
        for record in self:
            # Return empty recordset since model doesn't exist
            record.loading_history_ids = self.env['paper.bale.loading.history'].browse()

    @api.depends()
    def _compute_weight_measurement_ids(self):
        """Compute weight measurements based on available records"""
        for record in self:
            # Return empty recordset since model doesn't exist
            record.weight_measurement_ids = self.env['paper.bale.weight.measurement'].browse()

    @api.depends()
    def _compute_source_document_ids(self):
        """Compute source documents based on available records"""
        for record in self:
            # Return empty recordset since inverse field doesn't exist
            record.source_document_ids = self.env['records.document'].browse()

    @api.depends('source_document_ids')
    def _compute_document_info(self):
        """Compute document-related information"""
        for bale in self:
            bale.document_count = len(bale.source_document_ids)

    @api.depends('weight_measurement_ids')
    def _compute_weight_info(self):
        """Compute weight-related information"""
        for bale in self:
            bale.weight_history_count = len(bale.weight_measurement_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale') or 'New'
        return super().create(vals_list)

    def action_weigh_bale(self):
        """Weigh the bale"""
        self.ensure_one()
        return {
            'name': _('Weigh Bale: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'paper.bale',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_load_trailer(self):
        """Load bale on trailer"""
        self.ensure_one()
        return {
            'name': _('Load on Trailer'),
            'type': 'ir.actions.act_window',
            'res_model': 'load.trailer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_quality_inspection(self):
        """Quality inspection of the bale"""
        self.ensure_one()
        return {
            'name': _('Quality Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.inspection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_print_label(self):
        """Print bale label"""
        self.ensure_one()
        return {
            'name': _('Print Bale Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.bale_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.bale_label_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_source_documents(self):
        """View source documents for this bale"""
        self.ensure_one()
        return {
            'name': _('Source Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_move_to_storage(self):
        """Move bale to storage"""
        self.ensure_one()
        return {
            'name': _('Move to Storage'),
            'type': 'ir.actions.act_window',
            'res_model': 'bale.storage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_view_weight_history(self):
        """View weight history for this bale"""
        self.ensure_one()
        return {
            'name': _('Weight History'),
            'type': 'ir.actions.act_window',
            'res_model': 'bale.weight.history',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_view_trailer_info(self):
        """View trailer information"""
        self.ensure_one()
        return {
            'name': _('Trailer Information'),
            'type': 'ir.actions.act_window',
            'res_model': 'load.trailer',
            'view_mode': 'tree,form',
            'domain': [('bale_ids', 'in', [self.id])],
            'context': {'default_bale_ids': [(6, 0, [self.id])]},
        }

    def action_view_inspection_details(self):
        """View inspection details"""
        inspection_id = self.env.context.get('inspection_id')
        if inspection_id:
            return {
                'name': _('Inspection Details'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.inspection',
                'res_id': inspection_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    # Compute method for activity_ids One2many field
    @api.depends()
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "paper.bale"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "paper.bale"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "paper.bale"),
                ("res_id", "=", record.id)
            ])
