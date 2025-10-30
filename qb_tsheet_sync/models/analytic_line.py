from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    tsheets_id = fields.Char(
        string="TSheets Entry ID",
        copy=False,
        index=True,
        help="Identifier of the TSheets entry used to prevent duplicate imports.",
    )
    
    time_formatted_colon = fields.Char(
        string="Time (HH:MM)",
        compute="_compute_time_formatted",
        store=False,
        help="Hours and minutes in HH:MM format (e.g., 8:30)"
    )
    
    time_formatted_decimal = fields.Char(
        string="Time (HH.MM)",
        compute="_compute_time_formatted",
        store=False,
        help="Hours and minutes in HH.MM decimal format (e.g., 8.50)"
    )

    _sql_constraints = [
        (
            "tsheets_id_unique",
            "unique(tsheets_id)",
            "This TSheets entry has already been synchronized.",
        )
    ]

    @api.depends('unit_amount')
    def _compute_time_formatted(self):
        """
        Compute time in HH:MM and HH.MM formats.
        unit_amount is in decimal hours (e.g., 8.5 = 8 hours 30 minutes)
        """
        for record in self:
            if record.unit_amount:
                hours = int(record.unit_amount)
                minutes = int((record.unit_amount - hours) * 60)
                
                # HH:MM format (e.g., "8:30")
                record.time_formatted_colon = "%d:%02d" % (hours, minutes)
                
                # HH.MM format (e.g., "8.50" - decimal hours with 2 decimals)
                record.time_formatted_decimal = "%.2f" % record.unit_amount
            else:
                record.time_formatted_colon = "0:00"
                record.time_formatted_decimal = "0.00"
