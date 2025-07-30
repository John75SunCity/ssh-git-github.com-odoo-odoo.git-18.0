# -*- coding: utf-8 -*-
from odoo import models, fields, api

class NaidCompliance(models.Model):
    _name = 'naid.compliance'
    _description = 'NAID Compliance Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Compliance Check', required=True)
    check_date = fields.Date(string='Check Date', required=True)
    compliance_level = fields.Selection([
        ('aaa', 'AAA Certified'),
        ('aa', 'AA Certified'),
        ('a', 'A Certified')
    ], string='NAID Level')
    certificate_id = fields.Many2one('naid.certificate', string='Certificate')
    audit_results = fields.Text(string='Audit Results')
    corrective_actions = fields.Text(string='Corrective Actions')
    next_review_date = fields.Date(string='Next Review Date')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant')
    ], default='pending')
