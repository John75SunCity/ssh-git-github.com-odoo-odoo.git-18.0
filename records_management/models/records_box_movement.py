# -*- coding: utf-8 -*-
"""
Records Box Movement Management - Enterprise Grade
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsBoxMovement(models.Model):
    """
    Comprehensive Records Box Movement History
    Tracks all box location changes, transfers, and audit trails
    """

    _name = "records.box.movement"
    _description = "Records Box Movement History"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "movement_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Movement Reference", required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string="Movement Description", tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Responsible User',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # BOX AND LOCATION RELATIONSHIPS
    # ==========================================
    box_id = fields.Many2one('records.box', string='Records Box', 
                            required=True, tracking=True, ondelete='cascade')
    from_location_id = fields.Many2one('records.location', string='From Location', 
                                      tracking=True)
    to_location_id = fields.Many2one('records.location', string='To Location', 
                                    required=True, tracking=True)
    
    # ==========================================
    # MOVEMENT DETAILS
    # ==========================================
    movement_date = fields.Datetime(string='Movement Date', 
                                   default=fields.Datetime.now, required=True, tracking=True)
    movement_type = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('delivery', 'Delivery to Customer'),
        ('transfer', 'Internal Transfer'),
        ('storage', 'Storage Assignment'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Destruction Movement'),
        ('audit', 'Audit Check'),
        ('maintenance', 'Maintenance Movement'),
        ('temporary', 'Temporary Movement'),
        ('return', 'Return to Storage')
    ], string='Movement Type', required=True, tracking=True)
    
    movement_reason = fields.Text(string='Movement Reason', tracking=True)
    special_instructions = fields.Text(string='Special Instructions')

    # ==========================================
    # PERSONNEL TRACKING
    # ==========================================
    moved_by_id = fields.Many2one('res.users', string='Moved By', 
                                 default=lambda self: self.env.user, tracking=True)
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', tracking=True)
    customer_contact_id = fields.Many2one('res.partner', string='Customer Contact')
    driver_id = fields.Many2one('res.users', string='Driver/Courier')
    
    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)

    # ==========================================
    # TIMING FIELDS
    # ==========================================
    estimated_start_time = fields.Datetime(string='Estimated Start Time')
    estimated_completion_time = fields.Datetime(string='Estimated Completion Time')
    actual_start_time = fields.Datetime(string='Actual Start Time')
    actual_completion_time = fields.Datetime(string='Actual Completion Time')
    
    # ==========================================
    # DOCUMENTATION AND VERIFICATION
    # ==========================================
    signature_required = fields.Boolean(string='Signature Required', default=True)
    signature_obtained = fields.Boolean(string='Signature Obtained', tracking=True)
    photo_taken = fields.Boolean(string='Photo Documentation', tracking=True)
    verification_notes = fields.Text(string='Verification Notes')
    
    # Chain of custody fields
    custody_transferred = fields.Boolean(string='Custody Transferred', tracking=True)
    custody_transfer_date = fields.Datetime(string='Custody Transfer Date')
    chain_of_custody_ids = fields.One2many('records.chain.of.custody.log', 'movement_id',
                                          string='Chain of Custody Records')
    
    # ==========================================
    # BILLING AND COST TRACKING
    # ==========================================
    billable = fields.Boolean(string='Billable Movement', default=True)
    cost = fields.Float(string='Movement Cost', tracking=True)
    distance = fields.Float(string='Distance (Miles)')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle Used')
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    box_barcode = fields.Char(related='box_id.barcode', string='Box Barcode', readonly=True)
    customer_id = fields.Many2one(related='box_id.customer_id', string='Customer', readonly=True)
    box_current_location = fields.Many2one(related='box_id.location_id', 
                                          string='Current Box Location', readonly=True)
    
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    movement_status = fields.Char(string='Movement Status', compute='_compute_movement_status')
    
    @api.depends('actual_start_time', 'actual_completion_time')
    def _compute_duration(self):
        """Calculate movement duration"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                delta = record.actual_completion_time - record.actual_start_time
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0
    
    @api.depends('state', 'movement_date', 'actual_completion_time')
    def _compute_movement_status(self):
        """Compute human-readable movement status"""
        for record in self:
            if record.state == 'completed':
                record.movement_status = f"Completed on {record.actual_completion_time.strftime('%Y-%m-%d %H:%M') if record.actual_completion_time else 'Unknown'}"
            elif record.state == 'in_transit':
                record.movement_status = f"In Transit since {record.actual_start_time.strftime('%Y-%m-%d %H:%M') if record.actual_start_time else record.movement_date.strftime('%Y-%m-%d %H:%M')}"
            elif record.state == 'confirmed':
                record.movement_status = f"Scheduled for {record.movement_date.strftime('%Y-%m-%d %H:%M')}"
            else:
                record.movement_status = record.state.title()

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_confirm_movement(self):
        """Confirm the movement"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft movements can be confirmed'))
        
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('records.box.movement') or _('New')
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_('Movement confirmed by %s') % self.env.user.name)
    
    def action_start_movement(self):
        """Start the movement (in transit)"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Only confirmed movements can be started'))
        
        self.write({
            'state': 'in_transit',
            'actual_start_time': fields.Datetime.now()
        })
        self.message_post(body=_('Movement started by %s') % self.env.user.name)
    
    def action_complete_movement(self):
        """Complete the movement and update box location"""
        self.ensure_one()
        if self.state != 'in_transit':
            raise UserError(_('Only movements in transit can be completed'))
        
        # Update box location
        self.box_id.write({'location_id': self.to_location_id.id})
        
        # Complete movement
        self.write({
            'state': 'completed',
            'actual_completion_time': fields.Datetime.now()
        })
        
        # Create chain of custody record
        self._create_custody_record()
        
        self.message_post(
            body=_('Movement completed. Box %s moved to %s') % 
                 (self.box_id.name, self.to_location_id.name)
        )
    
    def action_cancel_movement(self):
        """Cancel the movement"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_('Cannot cancel completed movements'))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Movement cancelled by %s') % self.env.user.name)
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    def _create_custody_record(self):
        """Create chain of custody record for the movement"""
        custody_vals = {
            'name': f"Custody for {self.name}",
            'movement_id': self.id,
            'box_id': self.box_id.id,
            'from_location_id': self.from_location_id.id if self.from_location_id else False,
            'to_location_id': self.to_location_id.id,
            'transfer_date': self.actual_completion_time or fields.Datetime.now(),
            'transferred_by_id': self.moved_by_id.id,
            'received_by_id': self.env.user.id,
            'custody_status': 'transferred'
        }
        self.env['records.chain.of.custody.log'].create(custody_vals)
        self.write({'custody_transferred': True, 'custody_transfer_date': fields.Datetime.now()})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.box.movement') or _('New')
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('movement_date', 'actual_start_time', 'actual_completion_time')
    def _check_movement_times(self):
        """Validate movement times"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                if record.actual_completion_time <= record.actual_start_time:
                    raise ValidationError(_('Completion time must be after start time'))
            
            if record.actual_start_time and record.movement_date:
                if record.actual_start_time < record.movement_date:
                    raise ValidationError(_('Actual start time cannot be before scheduled movement date'))

    @api.constrains('from_location_id', 'to_location_id')
    def _check_locations(self):
        """Validate location changes"""
        for record in self:
            if record.from_location_id and record.to_location_id:
                if record.from_location_id == record.to_location_id:
                    raise ValidationError(_('From and To locations cannot be the same'))
