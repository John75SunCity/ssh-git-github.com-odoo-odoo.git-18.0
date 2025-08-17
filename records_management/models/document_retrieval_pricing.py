from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields


class DocumentRetrievalPricing(models.Model):
    _name = 'document.retrieval.pricing'
    _description = 'Document Retrieval Pricing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_type, priority_level'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    service_type = fields.Selection()
    currency_id = fields.Many2one()
    base_fee = fields.Monetary(string='Base Fee')
    per_document_fee = fields.Monetary()
    per_hour_fee = fields.Monetary(string='Per Hour Fee')
    per_box_fee = fields.Monetary(string='Per Box Fee')
    volume_threshold = fields.Integer(string='Volume Threshold')
    volume_discount_percent = fields.Float(string='Volume Discount (%)')
    priority_level = fields.Selection()
    priority_multiplier = fields.Float()
    delivery_included = fields.Boolean(string='Delivery Included')
    delivery_fee = fields.Monetary(string='Delivery Fee')
    delivery_radius_km = fields.Float(string='Delivery Radius (km)')
    scanning_fee = fields.Monetary(string='Scanning Fee')
    ocr_fee = fields.Monetary(string='OCR Fee')
    digital_delivery_fee = fields.Monetary()
    same_day_multiplier = fields.Float()
    next_day_multiplier = fields.Float()
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    partner_id = fields.Many2one('res.partner')
    customer_tier = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    state = fields.Selection()
