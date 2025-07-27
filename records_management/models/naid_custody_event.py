# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class NAIDCustodyEvent(models.Model):
    """Model for detailed NAID custody events in chain of custody."""
    _name = 'naid.custody.event'
    _description = 'NAID Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'custody_id, event_datetime desc'

    # Core fields
    name = fields.Char('Event Reference', required=True, default='/')
    description = fields.Text('Event Description')
    
    # Custody relationship
    custody_id = fields.Many2one('naid.custody', string='Custody Record', 
                                 required=True, ondelete='cascade'
    
    # Event details
    event_type = fields.Selection([
        ('pickup', 'Pickup/Collection',
        ('transport', 'In Transport'),
        ('arrival', 'Arrival at Facility'),
        ('storage', 'Placed in Storage'),
        ('retrieval', 'Retrieved from Storage'),
        ('destruction_prep', 'Destruction Preparation'),
        ('destruction', 'Destruction Event'),
        ('completion', 'Process Completion'),
        ('exception', 'Exception/Issue'),
        ('verification', 'Verification Check'),
), string="Selection Field"
    event_datetime = fields.Datetime('Event Date/Time', required=True,)
                                    default=fields.Datetime.now, tracking=True
    
    # Personnel involved
    responsible_user_id = fields.Many2one('res.users', string='Responsible Person', 
                                         required=True, tracking=True
    witness_user_id = fields.Many2one('res.users', string='Witness')
    customer_representative = fields.Char('Customer Representative')
    
    # Location tracking
    location_from = fields.Char('Location From')
    location_to = fields.Char('Location To')
    facility_location = fields.Many2one('records.location', string='Facility Location')
    
    # Security and verification
    security_seal_number = fields.Char('Security Seal Number')
    vehicle_identification = fields.Char('Vehicle ID/License')
    driver_name = fields.Char('Driver Name')
    driver_license = fields.Char('Driver License Number')
    
    # Documentation
    photo_taken = fields.Boolean('Photo Documented', default=False)
    video_recorded = fields.Boolean('Video Recorded', default=False)
    signature_required = fields.Boolean('Signature Required', default=False)
    signature_obtained = fields.Boolean('Signature Obtained', default=False)
    
    # Environmental conditions
    temperature = fields.Float('Temperature (°F')
    humidity = fields.Float('Humidity (%)')
    weather_conditions = fields.Char('Weather Conditions')
    
    # Exception handling
    exception_occurred = fields.Boolean('Exception Occurred', default=False)
    exception_type = fields.Selection([
        ('delay', 'Schedule Delay'),
        ('damage', 'Damage Observed'),
        ('security', 'Security Issue'),
        ('access', 'Access Problem'),
        ('equipment', 'Equipment Failure'),
        ('other', 'Other Issue'), string="Selection Field")
    exception_details = fields.Text('Exception Details')
    resolution_action = fields.Text('Resolution Action Taken')
    
    # Compliance fields
    naid_compliance_verified = fields.Boolean('NAID Compliance Verified', default=False)
    chain_of_custody_intact = fields.Boolean('Chain of Custody Intact', default=True)
    documentation_complete = fields.Boolean('Documentation Complete', default=False)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft',
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('exception', 'Exception'),
        ('verified', 'Verified')
    
    # Audit trail), string="Selection Field"
    created_by = fields.Many2one('res.users', string='Created By', 
                                default=lambda self: self.env.user, readonly=True
    verified_by = fields.Many2one('res.users', string='Verified By')
    verification_date = fields.Datetime('Verification Date')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company
    active = fields.Boolean('Active', default=True)
    
    @api.model
    def create(self, vals):
        """Generate sequence for event reference"""
        if vals.get('name', '/') == '/':
    pass
            vals['name'] = self.env['ir.sequence'].next_by_code('naid.custody.event') or '/'
        return super().create(vals)
    
    @api.constrains('event_datetime')
    def _check_event_datetime(self):
        """Validate event datetime is not in future (unless draft)"""
        for record in self:
            if record.state != 'draft' and record.event_datetime > fields.Datetime.now():
    pass
                raise ValidationError(_('Event datetime cannot be in the future for completed events'))
    
    def action_verify_event(self):
        """Verify the custody event"""
        self.ensure_one()
        self.write({
            'state': 'verified',
            'verified_by': self.env.user.id,
            'verification_date': fields.Datetime.now(),
            'naid_compliance_verified': True,
            'documentation_complete': True
        }
    
    def action_mark_exception(self):
        """Mark event as having an exception"""
        self.ensure_one()
        self.write({
            'state': 'exception',
            'exception_occurred': True
        }
