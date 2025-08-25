from odoo import models, fields, api, _

class PaperBaleLine(models.Model):
    _name = 'paper.bale.line'
    _description = 'Paper Bale Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'bale_id, sequence'
    _rec_name = 'display_name'

    name = fields.Char(string='Line Reference', required=True, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    bale_id = fields.Many2one('paper.bale', string='Bale')
    weight_lbs = fields.Float(string='Weight (lbs)')
    material_type = fields.Selection([
        ('white_paper', 'White Paper'),
        ('mixed_paper', 'Mixed Paper'),
        ('cardboard', 'Cardboard'),
    ], string='Material Type', required=True)
    notes = fields.Text(string='Notes')

    @api.depends('name', 'material_type')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name or ''} - {rec.material_type or ''}"
