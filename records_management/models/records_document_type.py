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

    # Phase 2: Audit & Compliance Fields (10 fields)
    audit_required = fields.Boolean(
        string='Audit Required',
        default=False
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'), string="Selection Field")
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'), string="Selection Field")
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    security_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'), string="Selection Field")
    retention_compliance = fields.Boolean(
        string='Retention Compliance',
        default=True
    compliance_notes = fields.Text(string='Compliance Notes')
    
    # Analytics and assessment fields (missing from views
    audit_readiness_level = fields.Selection([
        ('not_ready', 'Not Ready'),
        ('partially_ready', 'Partially Ready'),
        ('ready', 'Ready'),
        ('audit_complete', 'Audit Complete'), string="Selection Field")
    auto_classification_potential = fields.Float(
        string='Auto Classification Potential',
        digits=(3, 2),
        help='Potential for automatic classification (0.0-1.0')
    classification_accuracy_score = fields.Float(
        string='Classification Accuracy Score',
        digits=(3, 2),
        help='Accuracy score for document classification',
    compliance_risk_assessment = fields.Text(
        string='Compliance Risk Assessment',
        help='Detailed risk assessment for compliance',
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        help='Number of documents of this type',
    document_type_utilization = fields.Float(
        string='Document Type Utilization',
        digits=(5, 2),
        help='Utilization percentage of this document type',
    growth_trend_indicator = fields.Selection([
        ('declining', 'Declining'),
        ('stable', 'Stable'),
        ('growing', 'Growing'),
        ('rapid_growth', 'Rapid Growth'), string="Selection Field")
    regulatory_compliance_score = fields.Float(
        string='Regulatory Compliance Score',
        digits=(3, 2),
        help='Score for regulatory compliance (0.0-100.0')
    seasonal_pattern_score = fields.Float(
        string='Seasonal Pattern Score',
        digits=(3, 2),
        help='Score indicating seasonal usage patterns',
    type_complexity_rating = fields.Selection([
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('very_complex', 'Very Complex')

    # Enhanced tracking and technical fields for records management
    
    @api.depends(), string="Selection Field"
    def _compute_document_count(self):
        """Compute the number of documents of this type."""
        for record in self:
            document_count = self.env['records.document'].search_count([
                ('document_type_id', '=', record.id)
            ]
            record.document_count = document_count