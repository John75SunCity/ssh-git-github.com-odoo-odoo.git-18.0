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
        docs = self.env["records.audit.log"].browse(docids)
        action_summary = {}
        for doc in docs:
            action_type = getattr(doc, 'action_type', 'unknown')
            if action_type not in action_summary:
                action_summary[action_type] = {"count": 0, "total_impact": 0, "records": []}
            summary = action_summary[action_type]
            summary["count"] += 1
            summary["total_impact"] += getattr(doc, 'financial_impact', 0)
            summary["records"].append(doc)
        approval_stats = {
            "pending": docs.filtered(lambda d: getattr(d, 'approval_status', None) == "pending"),
            "approved": docs.filtered(lambda d: getattr(d, 'approval_status', None) == "approved"),
            "rejected": docs.filtered(lambda d: getattr(d, 'approval_status', None) == "rejected"),
        }
        return {
            "doc_ids": docids,
            "doc_model": "records.audit.log",
            "docs": docs,
            "action_summary": action_summary,
            "approval_stats": approval_stats,
            "total_financial_impact": sum(getattr(doc, 'financial_impact', 0) for doc in docs),
        }
