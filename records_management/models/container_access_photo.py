# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ContainerAccessPhoto(models.Model):
    """Photo record linked to a container access activity.

    Minimal model to satisfy One2many on container.access.activity.photo_ids
    and provide a clean place to store either a reference to a generic Photo
    or an inline image, depending on usage.
    """

    _name = 'container.access.photo'
    _description = 'Container Access Photo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: "Activity Photo")
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company)

    # Link back to the access activity (inverse field for One2many)
    activity_id = fields.Many2one(
        comodel_name='container.access.activity',
        string='Access Activity',
        required=True,
        index=True,
        ondelete='cascade',
    )

    # Either link to a generic Photo record or store the binary inline
    photo_id = fields.Many2one(comodel_name='photo', string='Photo Record')
    image = fields.Binary(string='Image')
    image_filename = fields.Char(string='Image Filename')
