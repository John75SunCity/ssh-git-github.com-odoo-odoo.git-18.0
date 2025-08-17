from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields


class StockMoveSMSValidation(models.Model):
    _name = 'stock.move.sms.validation'
    _description = 'Stock Move SMS Validation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    name = fields.Char(required=True)
    move_id = fields.Many2one('stock.move')
    sms_code = fields.Char(string='SMS Code')
    validated = fields.Boolean(string='Validated')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
