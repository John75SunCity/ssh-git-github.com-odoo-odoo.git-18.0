# -*- coding: utf-8 -*-
"""Document Retrieval Performance Metrics Report

Aggregates retrieval performance KPIs and quality scoring.
"""
from odoo import models, api


class DocumentRetrievalMetricsReport(models.AbstractModel):
    _name = "report.records_management.retrieval_metrics_report"
    _description = "Document Retrieval Performance Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["retrieval.metric"].browse(docids)
        metrics_by_type = {}
        for doc in docs:
            metrics_by_type.setdefault(doc.metric_type, []).append(doc)
        performance_stats = {
            "excellent": docs.filtered(lambda d: d.performance_rating == "excellent"),
            "good": docs.filtered(lambda d: d.performance_rating == "good"),
            "acceptable": docs.filtered(lambda d: d.performance_rating == "acceptable"),
            "poor": docs.filtered(lambda d: d.performance_rating == "poor"),
            "unacceptable": docs.filtered(lambda d: d.performance_rating == "unacceptable"),
        }
        averages = {}
        for metric_type, records in metrics_by_type.items():
            if records:
                averages[metric_type] = {
                    "avg_value": sum(r.metric_value for r in records) / len(records),
                    "avg_quality": sum(r.quality_score for r in records) / len(records),
                    "count": len(records),
                }
        return {
            "doc_ids": docids,
            "doc_model": "retrieval.metric",
            "docs": docs,
            "metrics_by_type": metrics_by_type,
            "performance_stats": performance_stats,
            "averages": averages,
            "overall_quality_avg": sum(docs.mapped("quality_score")) / len(docs) if docs else 0,
        }
