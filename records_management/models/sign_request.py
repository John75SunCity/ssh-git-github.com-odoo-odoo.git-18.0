from odoo import models, fields

class SignRequest(models.Model):
    _inherit = 'sign.request'

    # NAID Audit Requirement relationship
    audit_requirement_id = fields.Many2one(
        'naid.audit.requirement',
        string='NAID Audit Requirement',
        help='Related NAID audit requirement for this sign request'
    )
