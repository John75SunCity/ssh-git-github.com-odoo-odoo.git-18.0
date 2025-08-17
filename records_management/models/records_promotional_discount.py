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
from odoo import api, fields, models


class RecordsPromotionalDiscount(models.Model):
    _name = 'records.promotional.discount'
    _description = 'Records Promotional Discount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, start_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    config_id = fields.Many2one()
    name = fields.Char(string='Promotion Name')
    promotion_code = fields.Char(string='Promotion Code')
    discount_type = fields.Selection()
    discount_value = fields.Float()
    currency_id = fields.Many2one()
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    minimum_order = fields.Monetary()
    maximum_discount = fields.Monetary()
    usage_limit = fields.Integer(string='Usage Limit')
    times_used = fields.Integer(string='Times Used')
    active = fields.Boolean(string='Active')
    state = fields.Selection()
