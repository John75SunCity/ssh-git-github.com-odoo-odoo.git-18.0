# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class RecordsTag(models.Model):
    """Minimal tag model for initial deployment - will be enhanced later."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _order = 'name'

    # Essential fields only
    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True,
        help="Unique name for this tag"
    )
    color = fields.Integer(
        string='Color Index',
        help="Color used to display this tag"
    )
    
    # TODO: Enhanced fields will be added in next deployment phase:
    # - active field
    # - description field  
    # - category selection
    # - analytics fields
    # - automation features
