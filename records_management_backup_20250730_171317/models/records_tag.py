# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class RecordsTag(models.Model):
    """Minimal tag model for initial deployment - will be enhanced later."""
    _name = 'records.tag'
    _description = 'Records Management Tag'
    _inherit = 'mail.thread'
    _order = 'name'

    # Essential fields only
    name = fields.Char(
        string='Name', 
        required=True, 
        translate=True,
        help="Unique name for this tag"
    )
    
    description = fields.Text(
        string='Description',
        help="Detailed description of this tag's purpose and usage"
    )
    
    color = fields.Integer(
        string='Color Index',
        help="Color used to display this tag"
    )

    # Phase 1 Critical Fields - Added by automated script
    
    # Technical fields for view compatibility
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='records.tag')
    res_model = fields.Char(string='Resource Model', default='records.tag')
    help = fields.Text(string='Help Text')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_id = fields.Many2one('ir.ui.view', string='View')
    view_mode = fields.Char(string='View Mode', default='tree,form')