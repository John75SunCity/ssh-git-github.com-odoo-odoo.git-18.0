# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class RecordsTag(models.Model):
    """Model for tags in records management with unique constraint."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _order = 'name'

    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True,
        help="Unique name for this tag"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this tag"
    )
    color = fields.Integer(
        string='Color Index',
        help="Color used to display this tag"
    )
    description = fields.Text(
        string='Description', 
        translate=True,
        help="Description of what this tag represents"
    )

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name

    def toggle_active(self):
        """Toggle the active state of the tag."""
        for record in self:
            record.active = not record.active
        return True

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!")
    ]
