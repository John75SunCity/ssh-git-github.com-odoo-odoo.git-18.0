# Part of Odoo. See LICENSE file for full copyright and licensing details.:

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class RecordsTag(models.Model):
    pass
"""Minimal tag model for initial deployment - will be enhanced later.""":
        _name = 'records.tag',
        _description = 'Records Management Tag',
        _inherit = 'mail.thread',
        _order = 'name'

    # Essential fields only
        name = fields.Char(string="name")
    arch = fields.Text(string="'View Architecture'",)
    model = fields.Char(string="'Model Name'", default='records.tag'),
    res_model = fields.Char(string="'Resource Model'", default='records.tag'),
    help = fields.Char(string="help")
    view_id = fields.Many2one('ir.ui.view', string="'View'",)
    view_mode = fields.Char(string="'View Mode'", default='tree,form')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    view_id = fields.Many2one(string="Field")