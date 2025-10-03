from datetime import date

from odoo import models, api


class ManagementDashboardReport(models.AbstractModel):
    _name = "report.records_management.report_management_dashboard"
    _description = "Management Dashboard Aggregate Report"

    @api.model
    def _compute_metrics(self):
        """Return core dashboard metrics as a dictionary.

        Designed so both the report and the snapshot model helper can reuse
        a single implementation. Metrics are intentionally lightweight to
        keep the report fast and safe for automated test execution.
        """
        company = self.env.company
        # Containers
        total_boxes = self.env["records.container"].search_count([("company_id", "=", company.id)])

        # Shredding Services current month
        today = date.today()
        month_start = today.replace(day=1)
        shredding_domain = [
            ("company_id", "=", company.id),
            ("service_date", ">=", month_start),
            ("service_date", "<=", today),
        ]
        monthly_shredded = self.env["shredding.service"].search_count(shredding_domain)

        # Revenue (confirmed billing in current month)
        billing_domain = [
            ("company_id", "=", company.id),
            ("billing_date", ">=", month_start),
            ("billing_date", "<=", today),
            ("state", "=", "confirmed"),
        ]
        monthly_revenue = sum(self.env["records.billing"].search(billing_domain).mapped("total_amount"))

        return {
            "total_boxes": total_boxes,
            "monthly_shredded": monthly_shredded,
            "monthly_revenue": monthly_revenue,
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        # If specific dashboard records are requested use them; otherwise compute fresh metrics.
        dashboards = self.env["records.management.dashboard"].browse(docids) if docids else self.env["records.management.dashboard"]
        metrics = self._compute_metrics()
        # Template expects `docs` to support .get; provide metrics dict directly.
        return {
            "doc_ids": docids,
            "doc_model": "records.management.dashboard",
            "docs": metrics,
            "dashboards": dashboards,
        }
