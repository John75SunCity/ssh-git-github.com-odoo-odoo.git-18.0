from odoo import models, fields

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # NAID Audit Requirement relationship
    audit_requirement_id = fields.Many2one(
        'naid.audit.requirement',
        string='NAID Audit Requirement',
        help='Related NAID audit requirement for this calendar event'
    )
