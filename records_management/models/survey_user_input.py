# -*- coding: utf-8 -*-

from odoo import fields, models


class SurveyUserInput(models.Model):
    """Extension of survey.user_input to support NAID audit requirements"""
    _inherit = 'survey.user_input'

    audit_requirement_id = fields.Many2one(
        'naid.audit.requirement',
        string='NAID Audit Requirement',
        help='Links this survey response to a specific NAID audit requirement',
        index=True
    )
