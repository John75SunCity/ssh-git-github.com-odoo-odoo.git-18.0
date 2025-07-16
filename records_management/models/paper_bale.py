# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic fields structure - ready for your code
    name = fields.Char(string='Bale Reference', required=True, default='New', tracking=True)
    shredding_id = fields.Many2one('shredding.service', string='Related Shredding Service')
    paper_type = fields.Selection([
        ('white', 'White Paper'),
        ('mixed', 'Mixed Paper'),
    ], string='Paper Type', required=True, default='white')
    weight = fields.Float(string='Weight (lbs)', tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale') or 'New'
        return super().create(vals)
