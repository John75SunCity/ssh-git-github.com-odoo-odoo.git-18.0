from datetime import date

from odoo import models, fields, api, _


class RecordsManagementDashboard(models.Model):
    """Lightweight management dashboard aggregate model

    This model exists primarily to back the PDF/QWeb report
    `records_management.report_management_dashboard` which expects a
    business model for `ir.actions.report.model` resolution.

    It intentionally stores only snapshot values so report executions
    can either target existing records or (more commonly) create a
    single transient-like persistent record for auditing consistency.
    """

    _name = "records.management.dashboard"
    _description = "Records Management Dashboard"
    _order = "create_date desc"

    name = fields.Char(string="Name", required=True, default=lambda self: "Management Dashboard")
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", required=True, default=lambda self: self.env.company
    )
    snapshot_date = fields.Date(string="Snapshot Date", default=lambda self: date.today(), required=True)

    # Stored snapshot metrics (on-demand compute; also live compute fields below)
    total_boxes = fields.Integer(string="Total Containers Snapshot")
    monthly_shredded = fields.Integer(string="Shredded This Month Snapshot")
    monthly_revenue = fields.Monetary(string="Revenue This Month Snapshot", currency_field="currency_id")
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True, comodel_name="res.currency")

    # Live KPIs (computed) ----------------------------------------------------
    kpi_total_containers = fields.Integer(string="Total Containers", compute="_compute_kpis")
    kpi_active_containers = fields.Integer(string="Active Containers", compute="_compute_kpis")
    kpi_monthly_revenue = fields.Monetary(string="Revenue (Month)", currency_field="currency_id", compute="_compute_kpis")
    kpi_monthly_shredded = fields.Integer(string="Shredding Jobs (Month)", compute="_compute_kpis")
    kpi_pending_portal_requests = fields.Integer(string="Pending Portal Requests", compute="_compute_kpis")
    kpi_avg_location_utilization = fields.Float(string="Avg Location Utilization %", compute="_compute_kpis")
    kpi_capacity_warnings = fields.Integer(string="Capacity Warnings", compute="_compute_kpis")

    def _compute_kpis(self):
        from datetime import date
        today = date.today()
        month_start = today.replace(day=1)
        Container = self.env["records.container"]
        Shredding = self.env["shredding.service"]
        Billing = self.env["records.billing"]
        PortalRequest = self.env["portal.request"]
        Location = self.env["stock.location"]
        for rec in self:
            company = rec.company_id
            c_domain = [("company_id", "=", company.id)]
            containers = Container.search(c_domain)
            rec.kpi_total_containers = len(containers)
            rec.kpi_active_containers = len(containers.filtered(lambda c: c.state in ("active", "in_storage")))
            shredding_jobs = Shredding.search_count([
                ("company_id", "=", company.id),
                ("service_date", ">=", month_start),
                ("service_date", "<=", today),
            ])
            rec.kpi_monthly_shredded = shredding_jobs
            billing_revenue = sum(Billing.search([
                ("company_id", "=", company.id),
                ("billing_date", ">=", month_start),
                ("billing_date", "<=", today),
                ("state", "=", "confirmed"),
            ]).mapped("total_amount"))
            rec.kpi_monthly_revenue = billing_revenue
            rec.kpi_pending_portal_requests = PortalRequest.search_count([
                ("company_id", "=", company.id), ("state", "in", ["draft", "submitted"])])
            locations = Location.search([("company_id", "=", company.id)])
            utilizations = [l.utilization_percentage for l in locations if l.utilization_percentage]
            rec.kpi_avg_location_utilization = sum(utilizations) / len(utilizations) if utilizations else 0.0
            rec.kpi_capacity_warnings = len([l for l in locations if l.utilization_percentage and l.utilization_percentage >= 90])

    @api.model
    def create_snapshot(self):
        """Utility to create a fresh snapshot record with current metrics.

        Returns the created record (single recordset). The metrics mirror
        those produced by the accompanying report parser helper.
        """
        metrics = self.env["report.records_management.report_management_dashboard"]._compute_metrics()
        return self.create(
            {
                "total_boxes": metrics["total_boxes"],
                "monthly_shredded": metrics["monthly_shredded"],
                "monthly_revenue": metrics["monthly_revenue"],
            }
        )

    # User action to refresh snapshot from live metrics ----------------------
    def action_refresh_snapshot(self):
        self.ensure_one()
        values = self.env["report.records_management.report_management_dashboard"]._compute_metrics()
        self.write({
            "total_boxes": values["total_boxes"],
            "monthly_shredded": values["monthly_shredded"],
            "monthly_revenue": values["monthly_revenue"],
            "snapshot_date": date.today(),
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Dashboard Updated"),
                "message": _("Snapshot metrics refreshed."),
                "type": "success",
            },
        }
