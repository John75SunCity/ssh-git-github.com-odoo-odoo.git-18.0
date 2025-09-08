# -*- coding: utf-8 -*-
"""Billing Configuration Audit Report

Summarizes billing configuration changes with impact and approval stats.
"""
from odoo import models, api


class BillingConfigAuditReport(models.AbstractModel):
    _name = "report.records_management.billing_config_audit_report"
    _description = "Billing Configuration Audit Trail Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["records.billing.config.audit"].browse(docids)
        action_summary = {}
        for doc in docs:
            action_type = doc.action_type
            if action_type not in action_summary:
                action_summary[action_type] = {"count": 0, "total_impact": 0, "records": []}
            summary = action_summary[action_type]
            summary["count"] += 1
            summary["total_impact"] += doc.financial_impact
            summary["records"].append(doc)
        approval_stats = {
            "pending": docs.filtered(lambda d: d.approval_status == "pending"),
            "approved": docs.filtered(lambda d: d.approval_status == "approved"),
            "rejected": docs.filtered(lambda d: d.approval_status == "rejected"),
        }
        return {
            "doc_ids": docids,
            "doc_model": "records.billing.config.audit",
            "docs": docs,
            "action_summary": action_summary,
            "approval_stats": approval_stats,
            "total_financial_impact": sum(docs.mapped("financial_impact")),
        }
