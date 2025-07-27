# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaperBaleRecycling(models.Model):
    """
    Paper Bale Recycling - Simplified model for daily paper recycling operations
    Tracks bales from shredding through to load shipments and payment
    """
    _name = 'paper.bale.recycling'
    _description = 'Paper Bale for Recycling'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'bale_number desc, production_date desc'
    _rec_name = 'display_name'
    
    # Core business fields
    display_name = fields.Char('Bale ID', compute='_compute_display_name', store=True)
    bale_number = fields.Integer('Bale Number', required=True, 
                                help='Sequential bale number (auto-generated')
    
    # Paper specifications (simplified for daily operations
    paper_grade = fields.Selection([
        ('white', 'White Paper'),
        ('mixed', 'Mixed Paper'),
        ('cardboard', 'Cardboard')
       help='Type of paper in this bale'
    
    # Weight tracking (primary business metric), string="Selection Field")
    weight_lbs = fields.Float('Weight (lbs)', required=True, digits=(8, 2),
                             help='Weight in pounds as measured on floor scale',
    weight_kg = fields.Float('Weight (kg)', compute='_compute_weight_kg', store=True,
                            help='Automatic conversion to kilograms'
    
    # Production tracking
    production_date = fields.Date('Production Date', required=True,
                                 default=fields.Date.today,
                                 help='Date when bale was produced',
    weighed_by = fields.Many2one('hr.employee', string='Weighed By', required=True,
                                help='Employee who weighed the bale'
    
    # Load shipment tracking (key business process
    load_shipment_id = fields.Many2one('paper.load.shipment', string='Load Shipment',
                                      help='Which load shipment this bale is assigned to',
    load_number = fields.Char('Load Number', related='load_shipment_id.load_number', store=True)
    
    # Status workflow
    status = fields.Selection([
        ('produced', 'Produced',
        ('stored', 'In Storage'),
        ('assigned_load', 'Assigned to Load'),
        ('ready_ship', 'Ready to Ship'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('paid', 'Payment Received')
    
    # Mobile/Floor Scale Integration Fields), string="Selection Field"
    scale_reading = fields.Float('Scale Reading', help='Direct reading from floor scale')
    mobile_entry = fields.Boolean('Mobile Entry', default=False,
                                 help='Entered via mobile device',
    gps_coordinates = fields.Char('GPS Coordinates', help='Location where bale was weighed')
    
    # Quality tracking (simplified for daily operations
    moisture_level = fields.Selection([
        ('dry', 'Dry'),
        ('normal', 'Normal'),
        ('damp', 'Damp')
), string="Selection Field"
    contamination = fields.Boolean('Has Contamination', default=False,
                                  help='Check if bale has non-paper contamination',
    contamination_notes = fields.Text('Contamination Notes')
    
    # Storage and processing
    storage_location = fields.Many2one('stock.location', string='Storage Location')
    processed_from_service = fields.Many2one('shredding.service', string='From Shredding Service',
                                           help='Which shredding service produced this paper'
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company
    active = fields.Boolean('Active', default=True)
    
    # === COMPUTED METHODS ===
    
    @api.depends('bale_number', 'paper_grade', 'weight_lbs'
    def _compute_display_name(self):
        """Generate display name for bale"""
        for record in self:
            if record.bale_number and record.paper_grade:
                grade_short = {
                    'white': 'W',
                    'mixed': 'M', 
                    'cardboard': 'C'
                }.get(record.paper_grade, 'X')
                record.display_name = f"BALE-{record.bale_number:04d}-{grade_short}-{record.weight_lbs:.0f}lbs"
            else:
                record.display_name = f"New Bale"
    
    @api.depends('weight_lbs')
    def _compute_weight_kg(self):
        """Convert pounds to kilograms"""
        for record in self:
            record.weight_kg = record.weight_lbs * 0.453592 if record.weight_lbs else 0.0
    
    # === MODEL METHODS ===
    
    @api.model
    def create(self, vals:
        """Generate bale number sequence and handle mobile entry"""
        if not vals.get('bale_number'):
            # Auto-generate next bale number
            last_bale = self.search([], order='bale_number desc', limit=1
            vals['bale_number'] = (last_bale.bale_number + 1) if last_bale else 1
        
        # Handle mobile scale integration
        if vals.get('scale_reading' and not vals.get('weight_lbs'):
            vals['weight_lbs'] = vals['scale_reading']
            vals['mobile_entry'] = True
            
        return super().create(vals)
    
    @api.constrains('weight_lbs')
    def _check_weight(self):
        """Validate weight is positive"""
        for record in self:
            if record.weight_lbs <= 0:
                raise ValidationError(_('Weight must be greater than zero'))
    
    # === ACTION METHODS ===
    
    def action_store_bale(self:
        """Move bale to storage"""
        self.ensure_one()
        self.write({
            'status': 'stored',
            'storage_date': fields.Datetime.now()
        }
        return True
    
    def action_assign_to_load(self):
        """Assign bale to a load shipment"""
        self.ensure_one()
        if not self.load_shipment_id:
            raise ValidationError(_('Please select a load shipment first'))
        self.write({'status': 'assigned_load'})
        return True
    
    def action_ready_to_ship(self):
        """Mark bale as ready for shipping"""
        self.ensure_one()
        if not self.load_shipment_id:
            raise ValidationError(_('Bale must be assigned to a load first'))
        self.write({'status': 'ready_ship'})
        return True
    
    def action_ship_bale(self):
        """Ship the bale"""
        self.ensure_one()
        self.write({
            'status': 'shipped',
            'shipping_date': fields.Datetime.now()
        }
        return True
    
    def action_mark_delivered(self):
        """Mark bale as delivered"""
        self.ensure_one()
        self.write({'status': 'delivered'})
        return True
    
    def action_mark_paid(self):
        """Mark payment received for bale"""
        self.ensure_one()
        self.write({'status': 'paid'})
        return True
