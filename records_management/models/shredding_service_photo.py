from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class ShreddingServicePhoto(models.Model):
    _name = 'shredding.service.photo'
    _description = 'Shredding Service Photo Documentation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'shredding_service_id, sequence, photo_type'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    shredding_service_id = fields.Many2one()
    photo_type = fields.Selection()
    photo_data = fields.Binary()
    photo_filename = fields.Char()
    photo_date = fields.Datetime()
    witness_name = fields.Char()
    witness_signature = fields.Binary()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
