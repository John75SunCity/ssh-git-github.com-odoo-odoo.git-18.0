# -*- coding: utf-8 -*-
"""
NAID Chain of Custody Model
Tracks complete chain of custody for NAID AAA compliance
"""

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class NAIDChainOfCustody(models.Model):
    """
    NAID Chain of Custody Record
    Maintains complete custody chain for compliance
    """
    _name = 'naid.chain.custody'
    _description = 'NAID Chain of Custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Custody Reference',
        required=True,
        default='New'
    )
    
    # Related records
    service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service',
        help='Related shredding service'
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )
    
    # Custody timeline
    start_date = fields.Datetime(
        string='Custody Start',
        required=True,
        default=fields.Datetime.now
    )
    
    end_date = fields.Datetime(
        string='Custody End'
    )
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('transferred', 'Transferred'),
        ('terminated', 'Terminated')
    ], string='Status', default='active', required=True)
    
    # Custody events
    custody_events = fields.One2many(
        'naid.custody.event',
        'custody_id',
        string='Custody Events'
    )
    
    # Current custodian
    current_custodian_id = fields.Many2one(
        'hr.employee',
        string='Current Custodian',
        compute='_compute_current_custodian',
        store=True
    )
    
    # Materials description
    materials_description = fields.Text(
        string='Materials Description',
        help='Description of materials under custody'
    )
    
    total_weight = fields.Float(
        string='Total Weight (lbs)',
        help='Total weight of materials'
    )
    
    # Security information
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    ], string='Security Level', default='confidential')
    
    # Compliance
    compliance_verified = fields.Boolean(
        string='Compliance Verified',
        default=False
    )
    
    verification_notes = fields.Text(
        string='Verification Notes'
    )

    @api.depends('custody_events.timestamp')
    def _compute_current_custodian(self):
        """Compute current custodian from latest event"""
        for record in self:
            latest_event = record.custody_events.sorted('timestamp', reverse=True)[:1]
            if latest_event:
                record.current_custodian_id = latest_event.employee_id
            else:
                record.current_custodian_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequence number"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('naid.chain.custody') or 'New'
        return super().create(vals_list)

    def action_transfer_custody(self):
        """Transfer custody to another employee"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer Custody',
            'res_model': 'naid.custody.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_custody_id': self.id}
        }

    def action_complete_custody(self):
        """Complete the chain of custody"""
        self.write({
            'status': 'completed',
            'end_date': fields.Datetime.now()
        })
        
        # Log completion event
        self.env['naid.custody.event'].create({
            'custody_id': self.id,
            'event_type': 'completed',
            'timestamp': fields.Datetime.now(),
            'employee_id': self.env.user.employee_id.id,
            'description': 'Chain of custody completed'
        })

    def action_view_events(self):
        """View custody events"""
        self.ensure_one()
        return {
            'name': _('Custody Events'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.custody.event',
            'view_mode': 'tree,form',
            'domain': [('custody_id', '=', self.id)],
            'context': {'default_custody_id': self.id},
        }

    def action_add_event(self):
        """Add custody event"""
        self.ensure_one()
        return {
            'name': _('Add Event'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.custody.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_custody_id': self.id},
        }

    def action_print_custody_form(self):
        """Print custody form"""
        self.ensure_one()
        return {
            'name': _('Print Custody Form'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.custody_form_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.custody_form_report',
            'context': {'active_ids': [self.id]},
        }

    def action_verify_chain(self):
        """Verify chain of custody"""
        self.ensure_one()
        return {
            'name': _('Verify Chain'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.verification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_custody_id': self.id},
        }

    def action_breach_report(self):
        """Report custody breach"""
        self.ensure_one()
        return {
            'name': _('Report Breach'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.breach.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_custody_id': self.id},
        }

class NAIDCustodyEvent(models.Model):
    """
    Individual events in the chain of custody
    """
    _name = 'naid.custody.event'
    _description = 'NAID Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'timestamp desc'

    custody_id = fields.Many2one(
        'naid.chain.custody',
        string='Chain of Custody',
        required=True,
        ondelete='cascade'
    )
    
    event_type = fields.Selection([
        ('received', 'Materials Received'),
        ('transferred', 'Custody Transferred'),
        ('stored', 'Materials Stored'),
        ('moved', 'Materials Moved'),
        ('processed', 'Materials Processed'),
        ('destroyed', 'Materials Destroyed'),
        ('completed', 'Custody Completed')
    ], string='Event Type', required=True)
    
    timestamp = fields.Datetime(
        string='Event Time',
        required=True,
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        help='Employee involved in this event'
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        help='Detailed description of the event'
    )
    
    location = fields.Char(
        string='Location',
        help='Where the event took place'
    )
    
    witness_employee_ids = fields.Many2many(
        'hr.employee',
        'custody_event_witness_rel',
        'event_id',
        'employee_id',
        string='Witnesses',
        help='Employees who witnessed this event'
    )
    
    # Evidence
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Evidence',
        help='Photos, documents, or other evidence'
    )
    
    # GPS coordinates
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    
    # Temperature and environmental conditions
    temperature = fields.Float(string='Temperature (°F)')
    humidity = fields.Float(string='Humidity (%)')
    
    notes = fields.Text(string='Additional Notes')

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-log custody event in audit log"""
        events = super().create(vals_list)
        
        # Create corresponding audit log for each event
        for event in events:
            self.env['naid.audit.log'].log_event(
                'document_handling',
                f"Custody event: {event.event_type} - {event.description}",
                employee_id=event.employee_id.id,
                partner_id=event.custody_id.customer_id.id,
                risk_level='medium',
                compliance_status='compliant',
                custody_chain=f"Chain of Custody: {event.custody_id.name}"
            )
        
        return events
