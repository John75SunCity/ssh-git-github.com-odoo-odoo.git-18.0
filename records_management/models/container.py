# -*- coding: utf-8 -*-
"""
Records Container Management - Enterprise Grade
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsContainer(models.Model):
    """
    Container Management for Records Storage
    Manages physical containers, bins, and storage units
    """

    _name = "records.container"
    _description = "Records Container Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Container Number", required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string="Container Description", tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Container Manager',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CONTAINER SPECIFICATIONS
    # ==========================================
    container_type = fields.Selection([
        ('bin', 'Storage Bin'),
        ('box', 'Document Box'),
        ('cabinet', 'Filing Cabinet'),
        ('rack', 'Storage Rack'),
        ('pallet', 'Pallet'),
        ('trailer', 'Mobile Trailer'),
        ('vault', 'Security Vault')
    ], string='Container Type', required=True, tracking=True)
    
    # Physical dimensions
    length = fields.Float(string='Length (inches)', tracking=True)
    width = fields.Float(string='Width (inches)', tracking=True)
    height = fields.Float(string='Height (inches)', tracking=True)
    volume = fields.Float(string='Volume (cubic ft)', compute='_compute_volume', store=True)
    
    # Capacity tracking
    max_weight = fields.Float(string='Max Weight (lbs)', tracking=True)
    current_weight = fields.Float(string='Current Weight (lbs)', 
                                 compute='_compute_current_weight', store=True)
    max_boxes = fields.Integer(string='Max Box Capacity', tracking=True)
    current_boxes = fields.Integer(string='Current Boxes',
                                  compute='_compute_current_boxes', store=True)

    # ==========================================
    # LOCATION AND STATUS
    # ==========================================
    location_id = fields.Many2one('records.location', string='Current Location',
                                 required=True, tracking=True)
    warehouse_zone = fields.Char(string='Warehouse Zone', tracking=True)
    aisle = fields.Char(string='Aisle', tracking=True)
    shelf = fields.Char(string='Shelf', tracking=True)
    position = fields.Char(string='Position', tracking=True)
    
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('full', 'Full'),
        ('maintenance', 'Maintenance'),
        ('damaged', 'Damaged'),
        ('retired', 'Retired')
    ], string='Status', default='available', tracking=True, required=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    container_ids = fields.One2many('records.container', 'parent_container_id', string='Stored Containers')
    customer_id = fields.Many2one('res.partner', string='Primary Customer',
                                 domain=[('is_company', '=', True)])
    
    # ==========================================
    # SECURITY AND ACCESS
    # ==========================================
    security_level = fields.Selection([
        ('standard', 'Standard'),
        ('enhanced', 'Enhanced'),
        ('maximum', 'Maximum Security')
    ], string='Security Level', default='standard', tracking=True)
    
    access_code = fields.Char(string='Access Code', tracking=True)
    lock_type = fields.Selection([
        ('none', 'No Lock'),
        ('key', 'Key Lock'),
        ('combination', 'Combination Lock'),
        ('electronic', 'Electronic Lock'),
        ('biometric', 'Biometric Lock')
    ], string='Lock Type', default='none', tracking=True)

    # ==========================================
    # AUDIT AND NAID TRACKING
    # ==========================================
    last_audit_date = fields.Date(string='Last Audit Date', tracking=True)
    next_audit_date = fields.Date(string='Next Audit Date', tracking=True)
    audit_frequency = fields.Integer(string='Audit Frequency (days)', default=90)
    
    # NAID compliance
    naid_certified = fields.Boolean(string='NAID Certified Container', tracking=True)
    certification_number = fields.Char(string='Certification Number', tracking=True)
    certification_expiry = fields.Date(string='Certification Expiry', tracking=True)

    # ==========================================
    box_ids = fields.One2many('records.box', 'parent_container_id', string='Boxes')
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('length', 'width', 'height')
    def _compute_volume(self):
        """Calculate container volume in cubic feet"""
        for record in self:
            if record.length and record.width and record.height:
                # Convert from cubic inches to cubic feet
                record.volume = (record.length * record.width * record.height) / 1728
            else:
                record.volume = 0.0

    @api.depends('box_ids', 'box_ids.weight')
    def _compute_current_weight(self):
        """Calculate current weight from stored boxes"""
        for record in self:
            record.current_weight = sum(record.box_ids.mapped('weight'))

    @api.depends('box_ids')
    def _compute_current_boxes(self):
        """Count current number of boxes"""
        for record in self:
            record.current_boxes = len(record.box_ids)

    # ==========================================
    # STATUS MANAGEMENT
    # ==========================================
    def action_mark_available(self):
        """Mark container as available"""
        self.ensure_one()
        self.write({'status': 'available'})
        self.message_post(body=_('Container marked as available'))

    def action_mark_full(self):
        """Mark container as full"""
        self.ensure_one()
        self.write({'status': 'full'})
        self.message_post(body=_('Container marked as full'))

    def action_schedule_maintenance(self):
        """Schedule container maintenance"""
        self.ensure_one()
        self.write({'status': 'maintenance'})
        
        # Create activity for maintenance
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary='Container Maintenance Required',
            note=f'Container {self.name} requires maintenance',
            user_id=self.user_id.id
        )
        
        self.message_post(body=_('Maintenance scheduled for container'))

    # ==========================================
    # AUDIT METHODS
    # ==========================================
    def action_perform_audit(self):
        """Perform container audit"""
        self.ensure_one()
        
        # Update audit dates
        next_audit = fields.Date.add(fields.Date.today(), days=self.audit_frequency)
        self.write({
            'last_audit_date': fields.Date.today(),
            'next_audit_date': next_audit
        })
        
        # Create audit log
        self.env['naid.audit.log'].create({
            'name': f'Container Audit - {self.name}',
            'user_id': self.env.user.id,
            'action': 'container_audit',
            'resource_type': 'container',
            'resource_id': self.id,
            'access_date': fields.Datetime.now(),
            'notes': f'Regular audit performed for container {self.name}'
        })
        
        self.message_post(body=_('Container audit completed'))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.container') or _('New')
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('current_weight', 'max_weight')
    def _check_weight_limits(self):
        """Validate weight limits"""
        for record in self:
            if record.max_weight and record.current_weight > record.max_weight:
                raise ValidationError(_('Current weight exceeds maximum capacity'))

    @api.constrains('current_boxes', 'max_boxes')
    def _check_box_limits(self):
        """Validate box count limits"""
        for record in self:
            if record.max_boxes and record.current_boxes > record.max_boxes:
                raise ValidationError(_('Current box count exceeds maximum capacity'))

    @api.constrains('certification_expiry')
    def _check_certification_expiry(self):
        """Check NAID certification expiry"""
        for record in self:
            if record.naid_certified and record.certification_expiry:
                if record.certification_expiry < fields.Date.today():
                    raise ValidationError(_('NAID certification has expired'))
    @api.depends('box_ids')
    def _compute_box_count(self):
        """Count boxes in container"""
        for record in self:
            record.box_count = len(record.box_ids)
