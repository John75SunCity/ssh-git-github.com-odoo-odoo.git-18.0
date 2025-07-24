# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Phase 1: Explicit Activity Field (1 field)