# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ContainerAccessReport(models.Model):
    """Formal report generated from a container access activity."""

    _name = 'container.access.report'
    _description = 'Container Access Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Report Name', default=lambda self: _('Access Report'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company)

    activity_id = fields.Many2one(
        comodel_name='container.access.activity',
        string='Access Activity',
        required=True,
        index=True,
        ondelete='cascade',
    )

    content = fields.Text(string='Report Content')
    attachment_id = fields.Many2one(comodel_name='ir.attachment', string='Report Attachment')
