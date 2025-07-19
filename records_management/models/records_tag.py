# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class RecordsTag(models.Model):
    """Model for tags in records management with unique constraint."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    description = fields.Text(string='Description', translate=True,
                             help="Description of what this tag represents")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!")
    ]
