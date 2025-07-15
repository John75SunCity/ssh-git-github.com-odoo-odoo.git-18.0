# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBale(models.Model):
    """Paper Bale model for recycled paper tracking."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Bale #',
        required=True,
        default='New',
        copy=False
    )
    paper_type = fields.Selection([
        ('white', 'White'),
        ('mix', 'Mix'),
        ('cardboard', 'Cardboard')
    ], string='Paper Type', required=True)
    weight = fields.Float(
        string='Weight (lbs)',
        required=True,
        digits=(16, 2)
    )
    technician_id = fields.Many2one(
        'res.users',
        string='Technician',
        default=lambda self: self.env.user
    )
    signature = fields.Binary(string='Technician Signature')
    date = fields.Date(string='Date', default=fields.Date.today)
    shredding_id = fields.Many2one(
        'shredding.service',
        string='Source Shredding'
    )
    trailer_load_id = fields.Many2one('trailer.load', string='Trailer Load')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('weighed', 'Weighed'),
        ('loaded', 'Loaded'),
        ('sold', 'Sold')
    ], default='draft', tracking=True)
    label_printed = fields.Boolean(string='Label Printed', default=False)

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'PaperBale':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('paper.bale')
                    or 'New'
                )
        return super().create(vals_list)

    def action_weigh(self):
        """Action to mark as weighed."""
        self.write({'state': 'weighed'})
        self._generate_label()

    def _generate_label(self):
        """Generate bale label report."""
        report = self.env.ref('records_management.bale_label_report')
        pdf = report._render_qweb_pdf(self.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': f'Bale_Label_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf,
            'res_model': self._name,
            'res_id': self.id,
        })
        self.label_printed = True
        self.message_post(
            body=_('Bale label generated.'),
            attachment_ids=[attachment.id]
        )
