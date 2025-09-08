# -*- coding: utf-8 -*-
"""Revenue Forecast Report

Provides forecast vs actual revenue variance analysis.
"""
from odoo import models, api


class RevenueForecastReport(models.AbstractModel):
    _name = "report.records_management.revenue_forecast_report"
    _description = "Revenue Forecast Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["revenue.forecaster"].browse(docids)
        total_forecasted = sum(docs.mapped("total_forecasted_revenue"))
        total_actual = sum(docs.mapped("total_actual_revenue"))
        total_variance = total_forecasted - total_actual
        forecast_lines = self.env["revenue.forecast.line"].search([
            ("forecast_id", "in", docids)
        ], order="forecast_id, customer_id, service_type")
        forecasts_with_lines = {doc: forecast_lines.filtered(lambda l, d=doc: l.forecast_id.id == d.id) for doc in docs}
        return {
            "doc_ids": docids,
            "doc_model": "revenue.forecaster",
            "docs": docs,
            "forecasts_with_lines": forecasts_with_lines,
            "total_forecasted": total_forecasted,
            "total_actual": total_actual,
            "total_variance": total_variance,
            "variance_percentage": (total_variance / total_forecasted * 100) if total_forecasted else 0,
        }
