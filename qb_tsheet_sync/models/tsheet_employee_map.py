from odoo import _, api, fields, models


class TsheetsEmployeeMap(models.Model):
    _name = "qb.tsheets.employee.map"
    _description = "TSheets Employee Mapping"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "employee_id, tsheets_user_id"

    name = fields.Char(compute="_compute_name", store=True)
    config_id = fields.Many2one(
        comodel_name="qb.tsheets.sync.config",
        string="Configuration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    tsheets_user_id = fields.Char(
        string="TSheets User ID",
        required=True,
        tracking=True,
        help="Identifier returned by the TSheets API for this employee.",
    )
    company_id = fields.Many2one(
        related="config_id.company_id",
        comodel_name="res.company",
        string="Company",
        store=True,
        readonly=True,
    )
    last_synced_at = fields.Datetime(
        string="Last Synced",
        readonly=True,
        help="Datetime of the most recent successful synchronization for this employee.",
    )
    note = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "tsheets_user_company_unique",
            "unique(tsheets_user_id, config_id)",
            _("A TSheets user can only be mapped to one employee per configuration."),
        )
    ]

    @api.depends("employee_id", "tsheets_user_id")
    def _compute_name(self):
        for record in self:
            parts = []
            if record.employee_id:
                parts.append(record.employee_id.name or "")
            if record.tsheets_user_id:
                parts.append("TSheets #%s" % record.tsheets_user_id)
            record.name = " - ".join([p for p in parts if p]) or False

    def mark_synced(self):
        timestamp = fields.Datetime.now()
        for record in self:
            record.last_synced_at = timestamp
