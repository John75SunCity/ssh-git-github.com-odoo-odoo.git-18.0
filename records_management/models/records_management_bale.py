# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsManagementBale(models.Model):
    """Model for advanced records management bale tracking."""
    _name = 'records.management.bale'
    _description = 'Records Management Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'load_id, creation_date desc'

    # Core fields
    name = fields.Char('Bale Reference', required=True, default='/')
    description = fields.Text('Description')
    
    # Load relationship
    load_id = fields.Many2one('load', string='Load', 
                              help='The load this bale is part of')
    
    # Bale characteristics
    bale_type = fields.Selection([
        ('paper', 'Paper Bale'),
        ('cardboard', 'Cardboard Bale'),
        ('mixed_paper', 'Mixed Paper'),
        ('confidential', 'Confidential Paper'),
        ('shredded', 'Shredded Material'),
        ('pulp', 'Pulped Material'),
        ('other', 'Other Material')
    ], string='Bale Type', required=True, tracking=True)
    
    # Physical measurements
    weight_kg = fields.Float('Weight (kg)', digits=(10, 2), required=True)
    length_cm = fields.Float('Length (cm)', digits=(8, 1))
    width_cm = fields.Float('Width (cm)', digits=(8, 1))
    height_cm = fields.Float('Height (cm)', digits=(8, 1))
    volume_m3 = fields.Float('Volume (m³)', compute='_compute_volume', store=True)
    density_kg_m3 = fields.Float('Density (kg/m³)', compute='_compute_density', store=True)
    
    # Creation details
    creation_date = fields.Datetime('Creation Date', required=True, 
                                   default=fields.Datetime.now, tracking=True)
    creation_location = fields.Many2one('records.location', string='Creation Location')
    created_by_user = fields.Many2one('res.users', string='Created By', 
                                     default=lambda self: self.env.user)
    
    # Material source tracking
    source_boxes_count = fields.Integer('Source Boxes Count')
    source_documents_estimated = fields.Integer('Estimated Documents')
    shredding_service_id = fields.Many2one('shredding.service', string='Source Shredding Service')
    
    # Quality and composition
    moisture_content = fields.Float('Moisture Content (%)', digits=(5, 2))
    contamination_level = fields.Selection([
        ('none', 'No Contamination'),
        ('minimal', 'Minimal (<1%)'),
        ('low', 'Low (1-5%)'),
        ('moderate', 'Moderate (5-10%)'),
        ('high', 'High (>10%)')
    ], string='Contamination Level', default='none')
    
    fiber_quality = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Fiber Quality', default='good')
    
    # Processing and treatment
    processing_method = fields.Selection([
        ('baling_only', 'Baling Only'),
        ('compacted', 'Compacted'),
        ('shredded_baled', 'Shredded then Baled'),
        ('pulped_formed', 'Pulped and Formed'),
        ('treated', 'Chemically Treated')
    ], string='Processing Method', required=True)
    
    binding_material = fields.Selection([
        ('wire', 'Wire Binding'),
        ('plastic_strap', 'Plastic Strapping'),
        ('twine', 'Natural Twine'),
        ('none', 'No Binding'),
        ('other', 'Other')
    ], string='Binding Material', default='wire')
    
    # Storage and handling
    storage_location = fields.Many2one('records.location', string='Storage Location')
    storage_date = fields.Datetime('Storage Date')
    storage_conditions = fields.Selection([
        ('indoor_dry', 'Indoor - Dry'),
        ('indoor_humid', 'Indoor - Humid'),
        ('outdoor_covered', 'Outdoor - Covered'),
        ('outdoor_exposed', 'Outdoor - Exposed'),
        ('climate_controlled', 'Climate Controlled')
    ], string='Storage Conditions', default='indoor_dry')
    
    # Market and recycling
    market_grade = fields.Selection([
        ('grade_1', 'Grade 1 - Premium'),
        ('grade_2', 'Grade 2 - Standard'),
        ('grade_3', 'Grade 3 - Mixed'),
        ('grade_4', 'Grade 4 - Low Grade'),
        ('reject', 'Reject Material')
    ], string='Market Grade', default='grade_2')
    
    estimated_value = fields.Float('Estimated Value ($)', digits='Product Price')
    recycling_destination = fields.Char('Recycling Destination')
    
    # Shipping and logistics
    shipping_date = fields.Datetime('Shipping Date')
    shipping_method = fields.Selection([
        ('truck', 'Truck'),
        ('rail', 'Rail'),
        ('barge', 'Barge'),
        ('combined', 'Combined Transport')
    ], string='Shipping Method')
    
    vehicle_id = fields.Char('Vehicle/Container ID')
    bill_of_lading = fields.Char('Bill of Lading Number')
    
    # Environmental tracking
    carbon_footprint_kg = fields.Float('Carbon Footprint (kg CO2)', digits=(10, 2))
    water_savings_liters = fields.Float('Water Savings (liters)', digits=(12, 2))
    energy_savings_kwh = fields.Float('Energy Savings (kWh)', digits=(10, 2))
    
    # Status and workflow
    state = fields.Selection([
        ('created', 'Created'),
        ('quality_check', 'Quality Check'),
        ('stored', 'In Storage'),
        ('ready_ship', 'Ready to Ship'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('processed', 'Processed at Mill')
    ], string='Status', default='created', tracking=True)
    
    # Documentation
    photos_taken = fields.Boolean('Photos Taken', default=False)
    quality_certificate = fields.Boolean('Quality Certificate Issued', default=False)
    chain_of_custody_maintained = fields.Boolean('Chain of Custody Maintained', default=True)
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    
    @api.depends('length_cm', 'width_cm', 'height_cm')
    def _compute_volume(self):
        """Compute volume from dimensions"""
        for record in self:
            if record.length_cm and record.width_cm and record.height_cm:
                # Convert cm³ to m³
                volume_cm3 = record.length_cm * record.width_cm * record.height_cm
                record.volume_m3 = volume_cm3 / 1_000_000  # cm³ to m³
            else:
                record.volume_m3 = 0.0
    
    @api.depends('weight_kg', 'volume_m3')
    def _compute_density(self):
        """Compute density from weight and volume"""
        for record in self:
            if record.weight_kg and record.volume_m3:
                record.density_kg_m3 = record.weight_kg / record.volume_m3
            else:
                record.density_kg_m3 = 0.0
    
    @api.model
    def create(self, vals):
        """Generate sequence for bale reference"""
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('records.management.bale') or '/'
        return super().create(vals)
    
    @api.constrains('weight_kg', 'moisture_content')
    def _check_values(self):
        """Validate weight and moisture content"""
        for record in self:
            if record.weight_kg <= 0:
                raise ValidationError(_('Weight must be greater than zero'))
            if record.moisture_content and (record.moisture_content < 0 or record.moisture_content > 100):
                raise ValidationError(_('Moisture content must be between 0 and 100 percent'))
    
    def action_quality_check(self):
        """Perform quality check on bale"""
        self.ensure_one()
        self.write({'state': 'quality_check'})
    
    def action_store_bale(self):
        """Move bale to storage"""
        self.ensure_one()
        if not self.storage_location:
            raise ValidationError(_('Storage location must be specified'))
        self.write({
            'state': 'stored',
            'storage_date': fields.Datetime.now()
        })
    
    def action_ship_bale(self):
        """Ship the bale"""
        self.ensure_one()
        self.write({
            'state': 'shipped',
            'shipping_date': fields.Datetime.now()
        })
    
    def action_process_complete(self):
        """Mark processing as complete"""
        self.ensure_one()
        self.write({'state': 'processed'})
