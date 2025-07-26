# -*- coding: utf-8 -*-
"""
NAID Certificate Management
Tracks NAID compliance certificates and certifications
"""

from odoo import models, fields, api
from datetime import datetime, timedelta

class NAIDCertificate(models.Model):
    _name = 'naid.certificate'
    _description = 'NAID Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'certificate_date desc, name'
    _rec_name = 'name'

    # Core identification
    name = fields.Char('Certificate Name', required=True, tracking=True)
    certificate_number = fields.Char('Certificate Number', required=True, tracking=True)
    certificate_type = fields.Selection([
        ('aaa', 'NAID AAA Certification'),
        ('plant', 'Plant Certification'),
        ('mobile', 'Mobile Unit Certification'),
        ('employee', 'Employee Certification'),
        ('auditor', 'Auditor Certification'),
        ('facility', 'Facility Certification')
    ], string='Certificate Type', required=True, tracking=True)
    
    # NAID compliance relationship
    compliance_id = fields.Many2one('naid.compliance', string='NAID Compliance Record', tracking=True)
    
    # Certificate details
    certificate_date = fields.Date('Certificate Date', required=True, tracking=True)
    expiry_date = fields.Date('Expiry Date', required=True, tracking=True)
    issued_by = fields.Char('Issued By', required=True)
    certification_body = fields.Char('Certification Body')
    
    # Status and validity
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('pending', 'Pending Renewal')
    ], string='Status', default='active', tracking=True)
    
    is_valid = fields.Boolean('Is Valid', compute='_compute_validity', store=True)
    days_until_expiry = fields.Integer('Days Until Expiry', compute='_compute_validity', store=True)
    
    # Company and user context
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    
    # Additional details
    description = fields.Text('Description')
    notes = fields.Text('Notes')
    attachment_ids = fields.Many2many('ir.attachment', relation='attachment_ids_rel', 
                                   domain=[('res_model', '=', 'naid.certificate')  # Fixed: was One2many with missing inverse field],
                                   string='Attachments')
    
    @api.depends('expiry_date', 'status')
    def _compute_validity(self):
        """Compute certificate validity and days until expiry"""
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                delta = record.expiry_date - today
                record.days_until_expiry = delta.days
                record.is_valid = (record.status == 'active' and delta.days >= 0)
            else:
                record.days_until_expiry = 0
                record.is_valid = False
                
    def action_renew_certificate(self):
        """Action to renew certificate"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renew Certificate',
            'res_model': 'naid.certificate.renewal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_certificate_id': self.id}
        }
