from odoo import fields, models


class NaidCertificateItem(models.Model):
    _name = "naid.certificate.item"
    _description = "NAID Certificate Destroyed Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    certificate_id = fields.Many2one(
        "naid.certificate", string="Certificate", required=True, ondelete="cascade"
    )
    name = fields.Char(string="Description", required=True)
    weight = fields.Float(
        string="Weight (kg)",
        default=0.0,
        help="Weight of the destroyed item in kilograms",
    )
    quantity = fields.Integer(
        string="Quantity", default=1, help="Number of items destroyed"
    )
    material_type = fields.Char(
        string="Material Type", help="e.g., Paper, Hard Drives, Tapes"
    )
