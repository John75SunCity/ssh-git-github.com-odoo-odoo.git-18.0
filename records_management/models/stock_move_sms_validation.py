from odoo import models, fields


class StockMoveSMSValidation(models.Model):
    """
    Model for validating stock moves via SMS codes.
    """

    _name = "stock.move.sms.validation"
    _description = "Stock Move SMS Validation"

    name = fields.Char(required=True)
    move_id = fields.Many2one("stock.move", string="Stock Move")
    sms_code = fields.Char(string="SMS Code")
    validated = fields.Boolean(string="Validated")
