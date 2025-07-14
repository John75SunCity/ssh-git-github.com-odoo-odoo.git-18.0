# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _


class RecordsTag(models.Model):
    """Model for tags in records management with unique constraint."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _("Tag name already exists!"))
    ]
