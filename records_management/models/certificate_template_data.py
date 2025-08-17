from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class CertificateTemplateData(models.Model):
    _name = 'certificate.template.data'
    _description = 'Certificate Template Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    template_type = fields.Selection()
    template_format = fields.Selection()
    header_text = fields.Html()
    body_template = fields.Html()
    footer_text = fields.Html()
    logo_image = fields.Binary()
    company_address = fields.Text()
    certification_authority = fields.Char()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
