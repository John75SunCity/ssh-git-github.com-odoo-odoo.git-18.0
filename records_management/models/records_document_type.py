# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class RecordsDocumentType(models.Model):
    """Model for document types in records management."""
    _name = 'records.document.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Record Document Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True
    )

    # Phase 2: Audit & Compliance Fields (10 fields) 
    audit_required = fields.Boolean(
        string='Audit Required',
        default=False
    )
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review')
    ], string='Compliance Status', default='pending')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False
    )
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    security_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret')
    ], string='Security Classification', default='internal')
    retention_compliance = fields.Boolean(
        string='Retention Compliance',
        default=True
    )
    compliance_notes = fields.Text(string='Compliance Notes')

    # Enhanced tracking and technical fields for records management