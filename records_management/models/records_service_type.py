"""Odoo model for managing service types in the Records Management module.

Defines the 'records.service.type' model, which represents different types of services
offered in the records management workflow (e.g., shredding, pickup, storage).
Includes fields for name, code, description, company, and active status.
"""

from odoo import models, fields, _

class RecordsServiceType(models.Model):
    """Model for defining service types used in records management operations.

    Fields:
        name (Char): The name of the service type.
        code (Char): Unique code for the service type.
        active (Boolean): Status indicating if the service type is active.
        description (Text): Optional description of the service type.
        company_id (Many2one): Company to which the service type belongs.
    """

    _name = 'records.service.type'
    _description = 'Records Service Type (Placeholder)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_('Service Type Name'), required=True, tracking=True)
    code = fields.Char(string=_('Code'), required=True, tracking=True)
    sequence = fields.Integer(string=_('Sequence'), default=10, help="Used to order service types")
    active = fields.Boolean(default=True, tracking=True)
    description = fields.Text(string=_('Description'))
    company_id = fields.Many2one('res.company', string=_('Company'), default=lambda self: self.env.company, required=True, readonly=True)
    records_ids = fields.One2many('records.record', 'service_type_id', string=_('Records'))  # assumes records.record model exists

    # Optional: workflow state placeholder
    state = fields.Selection([
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('archived', _('Archived')),
    ], string=_('Status'), default='active', tracking=True)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', _('The code must be unique per company!')),
    ]
