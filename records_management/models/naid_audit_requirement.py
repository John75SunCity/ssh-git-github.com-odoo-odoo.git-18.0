# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NAIDAuditRequirement(models.Model):
    _name = 'naid.audit.requirement'
    _description = 'NAID Audit Requirement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'frequency_months, audit_type'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Requirement Name',
        required=True,
        help='Name of the audit requirement'
    )
    audit_type = fields.Selection([
        ('certification', 'Certification Audit'),
        ('internal', 'Internal Audit'),
        ('compliance', 'Compliance Review'),
        ('security', 'Security Assessment'),
        ('performance', 'Performance Review')
    ], string='Audit Type', required=True, default='internal')

    frequency_months = fields.Integer(
        string='Frequency (Months)',
        required=True,
        default=12,
        help='How often this audit must be performed in months'
    )

    # Audit Details
    scope = fields.Text(
        string='Audit Scope',
        help='Description of what areas and processes this audit covers'
    )
    auditor_requirements = fields.Text(
        string='Auditor Requirements',
        help='Qualifications and requirements for auditors performing this audit'
    )
    documentation_requirements = fields.Text(
        string='Documentation Requirements',
        help='Documentation that must be available and reviewed during audit'
    )

    # Active status
    active = fields.Boolean(string='Active', default=True)

    @api.depends('name', 'audit_type')
    def _compute_display_name(self):
        for record in self:
            if record.audit_type and record.name:
                audit_type_display = dict(record._fields['audit_type'].selection).get(record.audit_type, record.audit_type)
                record.display_name = f"{record.name} ({audit_type_display})"
            else:
                record.display_name = record.name or 'New Audit Requirement'
