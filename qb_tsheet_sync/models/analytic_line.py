from odoo import _, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    tsheets_id = fields.Char(
        string="TSheets Entry ID",
        copy=False,
        index=True,
        help="Identifier of the TSheets entry used to prevent duplicate imports.",
    )

    _sql_constraints = [
        (
            "tsheets_id_unique",
            "unique(tsheets_id)",
            _("This TSheets entry has already been synchronized."),
        )
    ]
