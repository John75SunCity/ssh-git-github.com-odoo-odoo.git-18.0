from odoo import _, api, fields, models


class TsheetsSyncConfig(models.Model):
    _name = "qb.tsheets.sync.config"
    _description = "TSheets Synchronization Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "company_id, name"

    name = fields.Char(
        string="Configuration Name",
        required=True,
        default="TSheets Sync",
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    api_token = fields.Char(
        string="API Access Token",
        required=True,
        copy=False,
        tracking=True,
        help="OAuth Access Token from TSheets. Copy from the 'Token' column in your TSheets App configuration.",
    )
    oauth_client_id = fields.Char(
        string="OAuth Client ID",
        copy=False,
        help="OAuth Client ID from TSheets API Application Details (optional, for reference).",
    )
    oauth_client_secret = fields.Char(
        string="OAuth Client Secret",
        copy=False,
        help="OAuth Client Secret from TSheets API Application Details (optional, for reference).",
    )
    base_url = fields.Char(
        string="API Base URL",
        required=True,
        default="https://api.tsheets.com/api/v1",
        help="Root endpoint for the TSheets API.",
    )
    default_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Default Project",
        help="Project applied to imported timesheets when no specific mapping is found.",
    )
    default_task_id = fields.Many2one(
        comodel_name="project.task",
        string="Default Task",
        help="Task applied to imported timesheets when no specific mapping is provided.",
    )
    employee_map_ids = fields.One2many(
        comodel_name="qb.tsheets.employee.map",
        inverse_name="config_id",
        string="Employee Mappings",
        help="Employees linked to their corresponding TSheets user identifiers.",
    )
    auto_sync = fields.Boolean(
        string="Enable Automatic Sync",
        default=True,
        help="If enabled, the scheduled job will synchronize entries automatically.",
    )
    sync_lookback_days = fields.Integer(
        string="Sync Lookback (days)",
        default=2,
        help="Number of days to look back when fetching timesheets to ensure updates are captured.",
    )
    last_attempt_at = fields.Datetime(
        string="Last Attempt",
        readonly=True,
        tracking=True,
    )
    last_success_at = fields.Datetime(
        string="Last Success",
        readonly=True,
        tracking=True,
    )
    last_message = fields.Text(
        string="Last Message",
        readonly=True,
        tracking=True,
    )

    _sql_constraints = [
        (
            "company_unique_config",
            "unique(company_id)",
            _("Only one TSheets configuration is allowed per company."),
        )
    ]

    @api.constrains("sync_lookback_days")
    def _check_sync_lookback_days(self):
        for record in self:
            if record.sync_lookback_days is not None and record.sync_lookback_days < 0:
                raise models.ValidationError(
                    _("The sync lookback window must be zero or a positive number of days."),
                )

    def action_sync_now(self):
        self.ensure_one()
        service = self.env["qb.tsheets.sync.service"]
        result = service.manual_sync(self)
        return result or True
