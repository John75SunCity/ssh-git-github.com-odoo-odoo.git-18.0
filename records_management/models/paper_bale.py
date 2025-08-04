# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PaperBale(models.Model):
    _name = "paper.bale"
    _description = "Paper Bale"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Bale Number", required=True, tracking=True, index=True)
    bale_number = fields.Char(string="Bale Number Alt", tracking=True)  # Legacy field
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    reference_number = fields.Char(string="Reference Number")
    external_reference = fields.Char(string="External Reference")

    # ============================================================================
    # STATE MANAGEMENT FIELDS
    # ============================================================================
    state = fields.Selection([
        ('created', 'Created'),
        ('quality_checked', 'Quality Checked'),
        ('loaded', 'Loaded on Trailer'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('recycled', 'Recycled'),
        ('rejected', 'Rejected/Sent to Trash')
    ], default='created', tracking=True)
    
    bale_status = fields.Selection([
        ('created', 'Created'),
        ('quality_checked', 'Quality Checked'),
        ('loaded', 'Loaded on Trailer'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('recycled', 'Recycled'),
        ('rejected', 'Rejected/Sent to Trash')
    ], string="Bale Status", default='created', tracking=True)
    
    workflow_state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Workflow State", default='draft')

    # ============================================================================
    # PHYSICAL PROPERTIES
    # ============================================================================
    weight = fields.Float(string="Weight (kg)")
    weight_lbs = fields.Float(string="Weight (lbs)", digits=(10, 2))
    weight_recorded = fields.Float(string="Weight Recorded (lbs)", digits=(10, 2))
    weight_unit = fields.Selection([
        ('lbs', 'Pounds'), 
        ('kg', 'Kilograms'), 
        ('tons', 'Tons')
    ], string="Weight Unit", default='lbs')
    
    dimensions = fields.Char(string="Dimensions (L x W x H)")
    density = fields.Float(string="Density", digits=(8, 2), compute="_compute_density", store=True)
    moisture_content = fields.Float(string="Moisture Content (%)", digits=(5, 2))
    moisture_reading = fields.Float(string="Moisture Reading %", digits=(5, 2))

    # ============================================================================
    # MATERIAL CLASSIFICATION
    # ============================================================================
    paper_type = fields.Selection([
        ('mixed_office', 'Mixed Office Paper'),
        ('white_ledger', 'White Ledger'),
        ('newspaper', 'Newspaper'),
        ('cardboard', 'Cardboard/OCC'),
        ('magazines', 'Magazines'),
        ('mixed_paper', 'Mixed Paper'),
        ('office', 'Office Paper'),
        ('non_paper', 'Non-Paper Material (Trash)')
    ], string="Material Type", required=True)
    
    bale_type = fields.Selection([
        ('mixed', 'Mixed Paper'),
        ('cardboard', 'Cardboard'),
        ('newspaper', 'Newspaper'),
        ('office', 'Office Paper')
    ], string="Bale Type", default='mixed')
    
    paper_grade = fields.Selection([
        ('1', 'Grade 1 - High Quality'),
        ('2', 'Grade 2 - Standard'),
        ('3', 'Grade 3 - Mixed'),
        ('4', 'Grade 4 - Low Quality')
    ], string="Paper Grade")
    
    grade_assigned = fields.Selection([
        ('A', 'Grade A - Premium'),
        ('B', 'Grade B - Standard'),
        ('C', 'Grade C - Low Grade'),
        ('reject', 'Reject')
    ], string="Grade Assigned")

    # ============================================================================
    # CONTAMINATION & QUALITY
    # ============================================================================
    contamination_level = fields.Selection([
        ('none', 'No Contamination'),
        ('low', 'Low (<2%)'),
        ('medium', 'Medium (2-5%)'),
        ('high', 'High (>5%)')
    ], string="Contamination Level", default='none')
    
    contamination_found = fields.Boolean(string="Contamination Found", default=False)
    contamination_percentage = fields.Float(string="Contamination %", digits=(5, 2))
    contamination_assessment = fields.Text("Contamination Assessment")
    
    quality_score = fields.Float(string="Quality Score", digits=(5, 2))
    quality_checked = fields.Boolean(string="Quality Checked")
    quality_control_passed = fields.Boolean("Quality Control Passed", default=False)
    passed_inspection = fields.Boolean(string="Passed Inspection", default=False)
    quality_notes = fields.Text(string="Quality Notes")

    # ============================================================================
    # REJECTION MANAGEMENT
    # ============================================================================
    is_rejected = fields.Boolean(string="Is Rejected", default=False, tracking=True)
    rejection_reason = fields.Text(string="Rejection Reason")
    rejection_date = fields.Date(string="Rejection Date")

    # ============================================================================
    # DATE FIELDS
    # ============================================================================
    creation_date = fields.Date(string="Creation Date", default=fields.Date.today)
    production_date = fields.Date(string="Production Date")
    pickup_date = fields.Date(string="Pickup Date")
    load_date = fields.Date(string="Load Date")
    loading_date = fields.Datetime(string="Loading Date")
    shipping_date = fields.Date(string="Shipping Date")
    delivery_date = fields.Date(string="Delivery Date")
    destruction_date = fields.Date(string="Destruction Date")
    quality_check_date = fields.Date(string="Quality Check Date")
    inspection_date = fields.Date(string="Inspection Date")
    measurement_date = fields.Datetime(string="Measurement Date")
    weigh_date = fields.Date(string="Weigh Date")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    completion_date = fields.Datetime(string="Completion Date")
    next_action_date = fields.Date(string="Next Action Date")
    deadline_date = fields.Date(string="Deadline")
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")
    processing_completion_date = fields.Date("Processing Completion Date")
    sorting_completion_date = fields.Date("Sorting Completion Date")
    validation_date = fields.Datetime(string="Validation Date")

    # ============================================================================
    # LOGISTICS & TRANSPORTATION
    # ============================================================================
    loaded_on_trailer = fields.Boolean(string="Loaded on Trailer", default=False, tracking=True)
    trailer_id = fields.Many2one("fleet.vehicle", string="Trailer")
    trailer_info = fields.Char(string="Trailer Information")
    load_id = fields.Many2one("load", string="Load")
    load_shipment_id = fields.Many2one("paper.load.shipment", string="Load Shipment")
    loading_position = fields.Char(string="Loading Position")
    loading_order = fields.Integer(string="Loading Order")
    storage_location = fields.Char(string="Storage Location")
    service_location = fields.Char(string="Service Location")
    source_facility = fields.Char(string="Source Facility")
    production_facility = fields.Char(string="Production Facility")
    recycling_facility = fields.Char(string="Recycling Facility")
    gps_pickup_location = fields.Char("GPS Pickup Location")
    
    transportation_method = fields.Selection([
        ('truck', 'Truck'), 
        ('rail', 'Rail'), 
        ('container', 'Container')
    ], default='truck')

    # ============================================================================
    # PERSONNEL FIELDS
    # ============================================================================
    operator_id = fields.Many2one("res.users", string="Operator")
    quality_checked_by = fields.Many2one("res.users", string="Quality Checked By")
    inspector = fields.Many2one("hr.employee", string="Inspector")
    loaded_by = fields.Many2one("hr.employee", string="Loaded By")
    measured_by = fields.Many2one("hr.employee", string="Measured By")
    weighed_by = fields.Many2one("hr.employee", string="Weighed By")
    responsible_user_id = fields.Many2one("res.users", string="Responsible User")
    supervisor_id = fields.Many2one("res.users", string="Supervisor")
    validated_by_id = fields.Many2one("res.users", string="Validated By")

    # ============================================================================
    # CUSTOMER & BUSINESS
    # ============================================================================
    customer_id = fields.Many2one("res.partner", string="Customer")
    customer_name = fields.Char(string="Customer Name")
    assigned_team_id = fields.Many2one("hr.department", string="Assigned Team")
    processing_facility_id = fields.Many2one("processing.facility", "Processing Facility")

    # ============================================================================
    # FINANCIAL FIELDS
    # ============================================================================
    currency_id = fields.Many2one("res.currency", string="Currency", 
                                  default=lambda self: self.env.company.currency_id)
    market_value = fields.Monetary(string="Market Value", currency_field="currency_id")
    sale_price = fields.Monetary(string="Sale Price", currency_field="currency_id")
    estimated_value = fields.Monetary(string="Estimated Value", currency_field="currency_id")
    market_price_per_lb = fields.Monetary(string="Market Price per lb", currency_field="currency_id")
    price_per_ton = fields.Monetary(string="Price per Ton", currency_field="currency_id")
    revenue_potential = fields.Monetary(string="Revenue Potential", currency_field="currency_id")
    processing_cost = fields.Monetary(string="Processing Cost", currency_field="currency_id")

    # ============================================================================
    # ENVIRONMENTAL IMPACT
    # ============================================================================
    carbon_footprint_saved = fields.Float(string="Carbon Footprint Saved (kg CO2)", digits=(10, 2))
    trees_saved = fields.Float(string="Trees Saved", digits=(8, 2), compute="_compute_environmental_impact", store=True)
    trees_saved_equivalent = fields.Float(string="Trees Saved Equivalent", digits=(8, 2))
    water_saved = fields.Float(string="Water Saved (gallons)", digits=(10, 2), compute="_compute_environmental_impact", store=True)
    energy_saved = fields.Float(string="Energy Saved (kWh)", digits=(10, 2))
    environmental_certification = fields.Char(string="Environmental Certification")
    sustainable_source = fields.Boolean(string="Sustainable Source", default=False)
    chain_of_custody_maintained = fields.Boolean(string="Chain of Custody Maintained", default=True)
    chain_of_custody_verified = fields.Boolean(string="Chain of Custody Verified", default=False)
    carbon_neutral = fields.Boolean(string="Carbon Neutral", default=False)
    environmental_impact_assessment = fields.Text("Environmental Impact Assessment")

    # ============================================================================
    # DOCUMENTATION & COMPLIANCE
    # ============================================================================
    photos_taken = fields.Boolean(string="Photos Taken", default=False)
    weight_ticket_number = fields.Char(string="Weight Ticket Number")
    quality_certificate = fields.Boolean(string="Quality Certificate", default=False)
    documentation_complete = fields.Boolean(string="Documentation Complete")
    naid_compliance_verified = fields.Boolean(string="NAID Compliance Verified", default=False)
    
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string="Confidentiality Level", default='confidential')
    
    security_level_required = fields.Selection([
        ('standard', 'Standard'),
        ('secure', 'Secure'),
        ('confidential', 'Confidential')
    ], default='standard')

    # ============================================================================
    # PROCESSING & WORKFLOW
    # ============================================================================
    processing_time = fields.Float(string="Processing Time (hours)", digits=(8, 2))
    estimated_processing_time = fields.Float("Estimated Processing Time (Hours)")
    weight_efficiency = fields.Float(string="Weight Efficiency %", digits=(5, 2))
    efficiency_rating = fields.Selection([
        ('poor', 'Poor'),
        ('fair', 'Fair'),
        ('good', 'Good'),
        ('excellent', 'Excellent')
    ], string="Efficiency Rating")
    
    performance_score = fields.Float(string="Performance Score", digits=(5, 2))
    validation_required = fields.Boolean(string="Validation Required")
    pre_processing_required = fields.Boolean("Pre-processing Required", default=False)
    sorting_required = fields.Boolean("Sorting Required", default=True)
    customer_approval_required = fields.Boolean("Customer Approval Required", default=False)
    customer_notification_sent = fields.Boolean("Customer Notification Sent", default=False)
    destruction_method_verified = fields.Boolean("Destruction Method Verified", default=False)
    final_weight_verified = fields.Boolean("Final Weight Verified", default=False)
    recycling_certificate_required = fields.Boolean("Recycling Certificate Required", default=True)

    # ============================================================================
    # OPERATIONAL FIELDS
    # ============================================================================
    source_containers = fields.Text(string="Source Containers")
    special_handling = fields.Text(string="Special Handling Instructions")
    loading_notes = fields.Text(string="Loading Notes")
    handling_requirements = fields.Text("Handling Requirements")
    load_optimization_notes = fields.Text("Load Optimization Notes")
    packaging_requirements = fields.Text("Packaging Requirements")
    temperature_requirements = fields.Text("Temperature Requirements")
    notes = fields.Text(string="Notes")
    
    storage_duration_days = fields.Integer("Storage Duration (Days)", default=30)
    volume_optimization_ratio = fields.Float("Volume Optimization Ratio", default=1.0)
    
    recycling_category = fields.Selection([
        ('office_paper', 'Office Paper'),
        ('newsprint', 'Newsprint'),
        ('cardboard', 'Cardboard'),
        ('mixed', 'Mixed')
    ], default='mixed')
    
    waste_stream_classification = fields.Selection([
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('institutional', 'Institutional')
    ], default='commercial')
    
    weight_verification_method = fields.Selection([
        ('scale', 'Scale'), 
        ('estimate', 'Estimate')
    ], default='scale')
    
    inspection_type = fields.Selection([
        ('incoming', 'Incoming Inspection'),
        ('quality_control', 'Quality Control'),
        ('pre_loading', 'Pre-Loading Check'),
        ('final', 'Final Inspection')
    ], string="Inspection Type")
    
    measurement_type = fields.Selection([
        ('initial', 'Initial Weighing'),
        ('verification', 'Verification Weighing'),
        ('final', 'Final Weighing'),
        ('reweigh', 'Re-weighing')
    ], string="Measurement Type")
    
    action_type = fields.Selection([
        ('sort', 'Sort'), 
        ('compress', 'Compress'), 
        ('transport', 'Transport')
    ], "Action Type")
    
    action_date = fields.Date("Action Date")
    scale_used = fields.Char(string="Scale Used")
    variance_from_previous = fields.Float(string="Variance from Previous (lbs)", digits=(10, 2))

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    paper_bale_recycling_id = fields.Many2one("paper.bale.recycling", string="Recycling Record")
    destruction_certificate_ids = fields.Many2many("destruction.certificate", string="Related Destruction Certificates")
    
    # Source Document Management
    source_document_ids = fields.One2many("paper.bale.source.document", "bale_id", string="Source Documents")
    document_count = fields.Integer(string="Document Count", compute="_compute_document_count", store=True)
    document_name = fields.Char(string="Document Name")
    document_type = fields.Selection([
        ('financial', 'Financial Records'),
        ('legal', 'Legal Documents'),
        ('medical', 'Medical Records'),
        ('corporate', 'Corporate Files'),
        ('mixed', 'Mixed Documents')
    ], string="Document Type")
    weight_contributed = fields.Float(string="Weight Contributed (lbs)", digits=(10, 2))
    
    # Loading Management
    loading_history_ids = fields.One2many("paper.bale.loading.history", "bale_id", string="Loading History")
    trailer_load_count = fields.Integer(string="Trailer Load Count", compute="_compute_trailer_load_count", store=True)
    
    # Quality Inspection System
    quality_inspection_ids = fields.One2many("paper.bale.quality.inspection", "bale_id", string="Quality Inspections")
    
    # Weight Management
    weight_measurement_ids = fields.One2many("paper.bale.weight.measurement", "bale_id", string="Weight Measurements")
    weight_history_count = fields.Integer(string="Weight History Count", compute="_compute_weight_history_count", store=True)
    
    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('source_document_ids')
    def _compute_document_count(self):
        """Compute total number of source documents"""
        for record in self:
            record.document_count = len(record.source_document_ids)

    @api.depends('loading_history_ids')
    def _compute_trailer_load_count(self):
        """Compute trailer loading history count"""
        for record in self:
            record.trailer_load_count = len(record.loading_history_ids)

    @api.depends('weight_measurement_ids')
    def _compute_weight_history_count(self):
        """Compute weight measurement history count"""
        for record in self:
            record.weight_history_count = len(record.weight_measurement_ids)

    @api.depends('weight_lbs', 'dimensions')
    def _compute_density(self):
        """Compute density of the bale"""
        for record in self:
            if record.weight_lbs and record.dimensions:
                # Simple density calculation - would need actual volume calculation
                record.density = record.weight_lbs / 100  # Placeholder calculation
            else:
                record.density = 0

    @api.depends('weight_lbs', 'paper_type', 'is_rejected')
    def _compute_environmental_impact(self):
        """Compute environmental impact metrics (excluded if rejected)"""
        for record in self:
            if record.weight_lbs and not record.is_rejected and record.paper_type != 'non_paper':
                # Standard environmental impact calculations for recycled paper
                weight_tons = record.weight_lbs / 2000
                record.trees_saved = weight_tons * 17  # Approximately 17 trees per ton
                record.water_saved = weight_tons * 7000  # Approximately 7000 gallons per ton
            else:
                record.trees_saved = 0
                record.water_saved = 0

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('paper_type')
    def _onchange_paper_type(self):
        """Auto-mark non-paper materials for rejection"""
        if self.paper_type == 'non_paper':
            self.is_rejected = True
            self.state = 'rejected'
            self.bale_status = 'rejected'
            self.rejection_reason = 'Non-paper material - sent to trash'
            self.rejection_date = fields.Date.today()

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_reject_bale(self):
        """Reject bale and send to trash"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Bale',
            'res_model': 'paper.bale',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_is_rejected': True,
                'default_state': 'rejected',
                'default_bale_status': 'rejected',
                'default_rejection_date': fields.Date.today(),
            },
        }

    def action_unreject_bale(self):
        """Unreject a bale if it was mistakenly rejected"""
        self.ensure_one()
        if self.is_rejected:
            self.write({
                'is_rejected': False,
                'state': 'created',
                'bale_status': 'created',
                'rejection_reason': False,
                'rejection_date': False,
            })
            self.message_post(body="Bale has been unrejected and returned to active status.")
        return True

    def action_load_trailer(self):
        """Load bale onto trailer."""
        self.ensure_one()
        if self.is_rejected:
            raise UserError("Cannot load rejected bales onto trailers.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Trailer',
            'res_model': 'records.vehicle',
            'view_mode': 'tree',
            'domain': [('vehicle_type', '=', 'trailer'), ('state', '=', 'available')],
            'context': {
                'default_bale_id': self.id,
                'search_default_available': 1,
            },
        }

    def action_move_to_storage(self):
        """Move bale to storage location."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Move to Storage',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_type_id': self.env.ref('stock.picking_type_internal').id,
                'default_origin': self.name,
                'default_note': f'Moving bale {self.name} to storage',
            },
        }

    def action_print_label(self):
        """Print bale identification label."""
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.paper_bale_label_report',
            'report_type': 'qweb-pdf',
            'context': {'active_ids': [self.id]},
        }

    def action_quality_inspection(self):
        """Perform quality inspection of bale."""
        self.ensure_one()
        if self.is_rejected:
            raise UserError("Cannot perform quality inspection on rejected bales.")

        # Create quality check activity
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f'Quality Inspection: {self.name}',
            note='Perform comprehensive quality inspection including contamination check and moisture content assessment.',
            user_id=self.user_id.id,
        )
        self.message_post(body="Quality inspection scheduled.")
        return True

    def action_view_inspection_details(self):
        """View quality inspection details."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inspection Details',
            'res_model': 'quality.check',
            'view_mode': 'tree,form',
            'domain': [('product_id.name', 'ilike', self.name)],
            'context': {'search_default_product_id': self.name},
        }

    def action_view_source_documents(self):
        """View source documents that contributed to this bale."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Source Documents',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {
                'default_bale_id': self.id,
                'search_default_bale_id': self.id,
            },
        }

    def action_view_trailer_info(self):
        """View trailer information for this bale."""
        self.ensure_one()
        if not self.trailer_id:
            raise UserError("No trailer assigned to this bale.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Trailer Information',
            'res_model': 'records.vehicle',
            'res_id': self.trailer_id.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_weight_history(self):
        """View weight measurement history."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weight History',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('product_id.name', 'ilike', self.name)],
            'context': {
                'search_default_product_id': self.name,
                'group_by': 'in_date',
            },
        }

    def action_weigh_bale(self):
        """Record bale weight measurement."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weigh Bale',
            'res_model': 'paper.bale',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_weight': self.weight,
                'focus_field': 'weight',
            },
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_active_bales_total_weight(self):
        """Get total weight of non-rejected bales"""
        active_bales = self.search([('is_rejected', '=', False)])
        return sum(active_bales.mapped('weight_lbs'))

    @api.model
    def get_recyclable_value_total(self):
        """Get total market value of non-rejected bales"""
        active_bales = self.search([('is_rejected', '=', False)])
        return sum(active_bales.mapped('market_value'))

    @api.model
    def get_environmental_impact_totals(self):
        """Get environmental impact totals (excluding rejected bales)"""
        active_bales = self.search([('is_rejected', '=', False)])
        return {
            'total_trees_saved': sum(active_bales.mapped('trees_saved')),
            'total_water_saved': sum(active_bales.mapped('water_saved')),
            'total_carbon_saved': sum(active_bales.mapped('carbon_footprint_saved')),
        }


# ============================================================================
# RELATED MODELS FOR PAPER BALE SYSTEM
# ============================================================================
class PaperBaleSourceDocument(models.Model):
    """Source documents that contributed to a paper bale"""
    _name = "paper.bale.source.document"
    _description = "Paper Bale Source Document"
    _order = "destruction_date desc"

    bale_id = fields.Many2one("paper.bale", string="Paper Bale", required=True, ondelete="cascade")
    document_name = fields.Char(string="Document Name", required=True)
    document_type = fields.Selection([
        ('financial', 'Financial Records'),
        ('legal', 'Legal Documents'),
        ('medical', 'Medical Records'),
        ('corporate', 'Corporate Files'),
        ('mixed', 'Mixed Documents')
    ], string="Document Type", required=True)
    customer_name = fields.Char(string="Customer Name")
    destruction_date = fields.Date(string="Destruction Date")
    weight_contributed = fields.Float(string="Weight Contributed (lbs)", digits=(10, 2))
    naid_compliance_verified = fields.Boolean(string="NAID Compliance Verified", default=False)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string="Confidentiality Level", default='confidential')


class PaperBaleLoadingHistory(models.Model):
    """Loading history for paper bales"""
    _name = "paper.bale.loading.history"
    _description = "Paper Bale Loading History"
    _order = "action_date desc"

    bale_id = fields.Many2one("paper.bale", string="Paper Bale", required=True, ondelete="cascade")
    action_date = fields.Datetime(string="Action Date", default=fields.Datetime.now)
    action_type = fields.Selection([
        ('loaded', 'Loaded onto Trailer'),
        ('unloaded', 'Unloaded from Trailer'),
        ('repositioned', 'Repositioned'),
        ('inspection', 'Loading Inspection')
    ], string="Action Type", required=True)
    performed_by = fields.Many2one("hr.employee", string="Performed By")
    trailer_info = fields.Char(string="Trailer Information")
    notes = fields.Text(string="Notes")


class PaperBaleQualityInspection(models.Model):
    """Quality inspection records for paper bales"""
    _name = "paper.bale.quality.inspection"
    _description = "Paper Bale Quality Inspection"
    _order = "inspection_date desc"

    bale_id = fields.Many2one("paper.bale", string="Paper Bale", required=True, ondelete="cascade")
    inspection_date = fields.Date(string="Inspection Date", required=True)
    inspector = fields.Many2one("hr.employee", string="Inspector", required=True)
    inspection_type = fields.Selection([
        ('incoming', 'Incoming Inspection'),
        ('quality_control', 'Quality Control'),
        ('pre_loading', 'Pre-Loading Check'),
        ('final', 'Final Inspection')
    ], string="Inspection Type", required=True)
    contamination_found = fields.Boolean(string="Contamination Found", default=False)
    moisture_reading = fields.Float(string="Moisture Reading %", digits=(5, 2))
    grade_assigned = fields.Selection([
        ('A', 'Grade A - Premium'),
        ('B', 'Grade B - Standard'),
        ('C', 'Grade C - Low Grade'),
        ('reject', 'Reject')
    ], string="Grade Assigned")
    passed_inspection = fields.Boolean(string="Passed Inspection", default=False)
    notes = fields.Text(string="Inspection Notes")


class PaperBaleWeightMeasurement(models.Model):
    """Weight measurement history for paper bales"""
    _name = "paper.bale.weight.measurement"
    _description = "Paper Bale Weight Measurement"
    _order = "measurement_date desc"

    bale_id = fields.Many2one("paper.bale", string="Paper Bale", required=True, ondelete="cascade")
    measurement_date = fields.Datetime(string="Measurement Date", default=fields.Datetime.now)
    weight_recorded = fields.Float(string="Weight Recorded (lbs)", digits=(10, 2), required=True)
    scale_used = fields.Char(string="Scale Used")
    measured_by = fields.Many2one("hr.employee", string="Measured By")
    measurement_type = fields.Selection([
        ('initial', 'Initial Weighing'),
        ('verification', 'Verification Weighing'),
        ('final', 'Final Weighing'),
        ('reweigh', 'Re-weighing')
    ], string="Measurement Type", required=True)
    variance_from_previous = fields.Float(string="Variance from Previous (lbs)", digits=(10, 2))
    notes = fields.Text(string="Measurement Notes")
