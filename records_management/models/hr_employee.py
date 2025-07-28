# -*- coding: utf-8 -*-
"""
HR Employee Extension for Records Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    """
    HR Employee Extension for Records Management
    Extends the core HR Employee model with comprehensive records-specific functionality
    """
    
    _inherit = 'hr.employee'
    
    # Core fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    
    # Records Management Department Assignment
    records_department_id = fields.Many2one(
        'records.department', 
        string='Records Department',
        help='Department for records management access control',
        tracking=True
    )
    
    # Access Control and Security
    records_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator')
    ], string='Records Access Level', default='none', tracking=True)
    
    naid_access_level = fields.Selection([
        ('none', 'No Access'),
        ('basic', 'Basic Access'),
        ('certified', 'NAID Certified'),
        ('supervisor', 'Supervisor'),
        ('auditor', 'Auditor')
    ], string='NAID Access Level', default='none', tracking=True)
    
    # Authorization Levels
    destruction_authorized = fields.Boolean(
        string='Authorized for Destruction',
        help='Employee is authorized to approve document destruction',
        default=False,
        tracking=True
    )
    
    pickup_authorized = fields.Boolean(
        string='Authorized for Pickup',
        help='Employee can authorize pickup requests',
        default=False,
        tracking=True
    )
    
    shredding_authorized = fields.Boolean(
        string='Authorized for Shredding',
        help='Employee can supervise shredding operations',
        default=False,
        tracking=True
    )
    
    # Security Clearance for Sensitive Documents
    security_clearance = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('secret', 'Secret')
    ], string='Security Clearance', default='public', tracking=True)
    
    # Certification and Training
    naid_certification_number = fields.Char(string='NAID Certification Number')
    naid_certification_date = fields.Date(string='NAID Certification Date')
    naid_certification_expiry = fields.Date(string='NAID Certification Expiry')
    
    records_training_completed = fields.Boolean(
        string='Records Training Completed',
        help='Employee has completed records management training',
        default=False
    )
    training_completion_date = fields.Date(string='Training Completion Date')
    
    # Operational Fields
    employee_signature = fields.Binary(string='Digital Signature')
    badge_number = fields.Char(string='Badge Number')
    emergency_contact = fields.Char(string='Emergency Contact')
    
    # Workflow and Assignment
    current_assignments = fields.Text(string='Current Assignments')
    specializations = fields.Text(string='Specializations')
    
    # Tracking and Audit
    last_audit_date = fields.Date(string='Last Audit Date')
    audit_notes = fields.Text(string='Audit Notes')
    
    # Performance Metrics
    destruction_count = fields.Integer(
        string='Documents Destroyed',
        help='Total number of destruction operations supervised',
        default=0
    )
    pickup_count = fields.Integer(
        string='Pickups Completed',
        help='Total number of pickup operations completed',
        default=0
    )
    
    # Contact Information
    work_phone = fields.Char(string='Work Phone')
    work_mobile = fields.Char(string='Work Mobile Phone')
    work_location = fields.Char(string='Primary Work Location')
    
    # Computed Fields
    certification_status = fields.Selection([
        ('none', 'Not Certified'),
        ('valid', 'Valid Certification'),
        ('expired', 'Expired'),
        ('expiring', 'Expiring Soon')
    ], string='Certification Status', compute='_compute_certification_status', store=True)
    
    access_summary = fields.Char(
        string='Access Summary',
        compute='_compute_access_summary',
        help='Summary of employee access levels and authorizations'
    )
    
    @api.depends('naid_certification_date', 'naid_certification_expiry')
    def _compute_certification_status(self):
        """Compute certification status based on dates"""
        today = fields.Date.today()
        for record in self:
            if not record.naid_certification_date or not record.naid_certification_expiry:
                record.certification_status = 'none'
            elif record.naid_certification_expiry < today:
                record.certification_status = 'expired'
            elif (record.naid_certification_expiry - today).days <= 30:
                record.certification_status = 'expiring'
            else:
                record.certification_status = 'valid'
    
    @api.depends('records_access_level', 'naid_access_level', 'destruction_authorized', 
                 'pickup_authorized', 'shredding_authorized')
    def _compute_access_summary(self):
        """Compute a summary of employee access and authorizations"""
        for record in self:
            summary_parts = []
            
            if record.records_access_level != 'none':
                summary_parts.append(f"Records: {record.records_access_level}")
            
            if record.naid_access_level != 'none':
                summary_parts.append(f"NAID: {record.naid_access_level}")
            
            authorizations = []
            if record.destruction_authorized:
                authorizations.append('Destruction')
            if record.pickup_authorized:
                authorizations.append('Pickup')
            if record.shredding_authorized:
                authorizations.append('Shredding')
            
            if authorizations:
                summary_parts.append(f"Auth: {', '.join(authorizations)}")
            
            record.access_summary = ' | '.join(summary_parts) if summary_parts else 'No Access'
    
    @api.constrains('naid_certification_date', 'naid_certification_expiry')
    def _check_certification_dates(self):
        """Validate certification dates"""
        for record in self:
            if record.naid_certification_date and record.naid_certification_expiry:
                if record.naid_certification_expiry <= record.naid_certification_date:
                    raise UserError(_('Certification expiry date must be after certification date.'))
    
    def action_renew_certification(self):
        """Action to renew NAID certification"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renew NAID Certification',
            'res_model': 'hr.employee',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_naid_certification_date': fields.Date.today()}
        }
    
    def action_complete_training(self):
        """Mark training as completed"""
        self.write({
            'records_training_completed': True,
            'training_completion_date': fields.Date.today()
        })
        return True
