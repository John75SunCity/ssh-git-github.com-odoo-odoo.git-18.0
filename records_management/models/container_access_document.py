# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ContainerAccessDocument(models.Model):
    """Document generated/attached during a container access activity."""

    _name = 'container.access.document'
    _description = 'Container Access Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('Activity Document'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company)

    activity_id = fields.Many2one(
        comodel_name='container.access.activity',
        string='Access Activity',
        required=True,
        index=True,
        ondelete='cascade',
    )

    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    description = fields.Text(string='Description')
