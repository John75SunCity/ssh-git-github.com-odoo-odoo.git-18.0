# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaperLoadShipment(models.Model):
    """
    Paper Load Shipment - Tracks loads (e.g., LOAD 535) for paper recycling business
    Manages manifest generation, driver signatures, and payment tracking
    """
    _name = 'paper.load.shipment'
    _description = 'Paper Load Shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'load_number desc, pickup_date desc'
    _rec_name = 'load_number'
    
    # Core load identification
    load_number = fields.Char('Load Number', required=True,
                             help='Load identifier (e.g., LOAD 535)')
    
    # Shipment details
    pickup_date = fields.Date('Pickup Date', required=True,
                             help='Date when load will be/was picked up')
    pickup_time = fields.Datetime('Pickup Time',
                                 help='Scheduled or actual pickup time')
    
    # Driver and transportation
    driver_name = fields.Char('Driver Name', required=True)
    driver_phone = fields.Char('Driver Phone')
    driver_license = fields.Char('Driver License')
    truck_info = fields.Char('Truck Information',
                           help='Truck details, license plate, etc.')
    transportation_company = fields.Char('Transportation Company')
    
    # Load composition and weight (key business metrics)
    total_weight_lbs = fields.Float('Total Weight (lbs)', compute='_compute_totals', store=True,
                                   help='Total weight of all bales in this load')
    total_weight_kg = fields.Float('Total Weight (kg)', compute='_compute_totals', store=True)
    bale_count = fields.Integer('Number of Bales', compute='_compute_totals', store=True)
    
    # Paper grade breakdown (for manifest)
    white_paper_weight = fields.Float('White Paper Weight', compute='_compute_grade_breakdown', store=True)
    mixed_paper_weight = fields.Float('Mixed Paper Weight', compute='_compute_grade_breakdown', store=True)
    cardboard_weight = fields.Float('Cardboard Weight', compute='_compute_grade_breakdown', store=True)
    
    white_paper_count = fields.Integer('White Paper Bales', compute='_compute_grade_breakdown', store=True)
    mixed_paper_count = fields.Integer('Mixed Paper Bales', compute='_compute_grade_breakdown', store=True)
    cardboard_count = fields.Integer('Cardboard Bales', compute='_compute_grade_breakdown', store=True)
    
    # Status and workflow
    status = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('ready_pickup', 'Ready for Pickup'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid')
    ], string='Status', default='draft', tracking=True)
    
    # Bales relationship
    bale_ids = fields.One2many('paper.bale.recycling', 'load_shipment_id', 
                              string='Bales in Load')
    
    # Destination and customer
    customer_id = fields.Many2one('res.partner', string='Customer/Mill',
                                 help='Paper mill or customer receiving the load')
    destination_address = fields.Text('Destination Address')
    delivery_notes = fields.Text('Delivery Notes')
    
    # Signatures and documentation
    driver_signature = fields.Binary('Driver Signature')
    driver_signature_date = fields.Datetime('Driver Signature Date')
    company_signature = fields.Binary('Company Representative Signature')
    company_signature_date = fields.Datetime('Company Signature Date')
    signed_by = fields.Many2one('hr.employee', string='Signed by Employee')
    
    # Manifest and documentation
    manifest_generated = fields.Boolean('Manifest Generated', default=False)
    manifest_number = fields.Char('Manifest Number')
    manifest_date = fields.Datetime('Manifest Generation Date')
    bill_of_lading = fields.Char('Bill of Lading')
    
    # Payment tracking (3-4 week cycle as mentioned)
    invoice_amount = fields.Float('Invoice Amount', digits='Product Price')
    invoice_date = fields.Date('Invoice Date')
    payment_due_date = fields.Date('Payment Due Date')
    payment_received_date = fields.Date('Payment Received Date')
    payment_amount = fields.Float('Payment Amount', digits='Product Price')
    payment_notes = fields.Text('Payment Notes')
    
    # Mobile integration fields
    mobile_manifest = fields.Boolean('Mobile Manifest', default=False,
                                    help='Manifest generated on mobile device')
    gps_pickup_location = fields.Char('GPS Pickup Location')
    gps_delivery_location = fields.Char('GPS Delivery Location')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    
    # === COMPUTED METHODS ===
    
    @api.depends('bale_ids', 'bale_ids.weight_lbs', 'bale_ids.weight_kg')
    def _compute_totals(self):
        """Compute total weight and bale count"""
        for record in self:
            record.total_weight_lbs = sum(record.bale_ids.mapped('weight_lbs'))
            record.total_weight_kg = sum(record.bale_ids.mapped('weight_kg'))
            record.bale_count = len(record.bale_ids)
    
    @api.depends('bale_ids', 'bale_ids.paper_grade', 'bale_ids.weight_lbs')
    def _compute_grade_breakdown(self):
        """Compute weight and count by paper grade for manifest"""
        for record in self:
            white_bales = record.bale_ids.filtered(lambda b: b.paper_grade == 'white')
            mixed_bales = record.bale_ids.filtered(lambda b: b.paper_grade == 'mixed')
            cardboard_bales = record.bale_ids.filtered(lambda b: b.paper_grade == 'cardboard')
            
            record.white_paper_weight = sum(white_bales.mapped('weight_lbs'))
            record.mixed_paper_weight = sum(mixed_bales.mapped('weight_lbs'))
            record.cardboard_weight = sum(cardboard_bales.mapped('weight_lbs'))
            
            record.white_paper_count = len(white_bales)
            record.mixed_paper_count = len(mixed_bales)
            record.cardboard_count = len(cardboard_bales)
    
    # === MODEL METHODS ===
    
    @api.model
    def create(self, vals):
        """Generate load number sequence"""
        if not vals.get('load_number'):
            # Auto-generate next load number
            last_load = self.search([], order='load_number desc', limit=1)
            if last_load and last_load.load_number.startswith('LOAD '):
                try:
                    last_num = int(last_load.load_number.split(' ')[1])
                    vals['load_number'] = f'LOAD {last_num + 1}'
                except (ValueError, IndexError):
                    vals['load_number'] = 'LOAD 1'
            else:
                vals['load_number'] = 'LOAD 1'
        
        return super().create(vals)
    
    @api.constrains('pickup_date', 'payment_due_date')
    def _check_dates(self):
        """Validate date logic"""
        for record in self:
            if record.payment_due_date and record.pickup_date:
                if record.payment_due_date < record.pickup_date:
                    raise ValidationError(_('Payment due date cannot be before pickup date'))
    
    # === ACTION METHODS ===
    
    def action_schedule_pickup(self):
        """Schedule the pickup"""
        self.ensure_one()
        if not self.bale_ids:
            raise ValidationError(_('Cannot schedule pickup - no bales assigned to this load'))
        self.write({'status': 'scheduled'})
        return True
    
    def action_ready_for_pickup(self):
        """Mark load as ready for pickup"""
        self.ensure_one()
        if not self.driver_name:
            raise ValidationError(_('Driver name is required before marking ready for pickup'))
        self.write({'status': 'ready_pickup'})
        return True
    
    def action_generate_manifest(self):
        """Generate manifest for the load"""
        self.ensure_one()
        if not self.bale_ids:
            raise ValidationError(_('Cannot generate manifest - no bales in this load'))
        
        self.write({
            'manifest_generated': True,
            'manifest_date': fields.Datetime.now(),
            'manifest_number': f'MAN-{self.load_number}-{fields.Date.today().strftime("%Y%m%d")}'
        })
        
        # This would trigger manifest report generation
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.paper_load_manifest_report',
            'report_type': 'qweb-pdf',
            'context': {'active_id': self.id}
        }
    
    def action_mark_in_transit(self):
        """Mark load as in transit"""
        self.ensure_one()
        if not self.driver_signature:
            raise ValidationError(_('Driver signature required before marking in transit'))
        
        self.write({
            'status': 'in_transit',
            'pickup_time': fields.Datetime.now() if not self.pickup_time else self.pickup_time
        })
        return True
    
    def action_mark_delivered(self):
        """Mark load as delivered"""
        self.ensure_one()
        self.write({'status': 'delivered'})
        
        # Auto-update bale statuses
        self.bale_ids.write({'status': 'delivered'})
        return True
    
    def action_create_invoice(self):
        """Create invoice for the load"""
        self.ensure_one()
        if not self.customer_id:
            raise ValidationError(_('Customer is required to create invoice'))
        
        # Calculate payment due date (3-4 weeks as mentioned)
        import datetime
        due_date = fields.Date.today() + datetime.timedelta(weeks=3)
        
        self.write({
            'status': 'invoiced',
            'invoice_date': fields.Date.today(),
            'payment_due_date': due_date
        })
        return True
    
    def action_mark_paid(self):
        """Mark payment as received"""
        self.ensure_one()
        self.write({
            'status': 'paid',
            'payment_received_date': fields.Date.today()
        })
        
        # Auto-update bale statuses
        self.bale_ids.write({'status': 'paid'})
        return True
    
    def action_add_bales_to_load(self):
        """Action to add bales to this load"""
        self.ensure_one()
        return {
            'name': f'Add Bales to {self.load_number}',
            'type': 'ir.actions.act_window',
            'res_model': 'paper.bale.recycling',
            'view_mode': 'tree,form',
            'domain': [('status', 'in', ['produced', 'stored']), ('load_shipment_id', '=', False)],
            'context': {'default_load_shipment_id': self.id},
            'target': 'new'
        }
