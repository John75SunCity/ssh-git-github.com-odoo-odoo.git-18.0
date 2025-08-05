from odoo import models, fields


class StockMoveSMSValidation(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    """
    Model for validating stock moves via SMS codes.
    """

    _name = "stock.move.sms.validation"
    _description = "Stock Move SMS Validation"
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)


    name = fields.Char(required=True)
    move_id = fields.Many2one("stock.move", string="Stock Move")
    sms_code = fields.Char(string="SMS Code")
    validated = fields.Boolean(string="Validated")
