"""Odoo model for managing service types in the Records Management module.

Defines the 'records.service.type' model, which represents different types of services
offered in the records management workflow (e.g., shredding, pickup, storage).
Includes fields for name, code, description, company, and active status.
"""

from odoo import models, fields

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

    name = fields.Char(string='Service Type Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Used to order service types")
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # Optional: workflow state placeholder
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string='Status', default='active', tracking=True)

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'The code must be unique per company!'),
    ]
