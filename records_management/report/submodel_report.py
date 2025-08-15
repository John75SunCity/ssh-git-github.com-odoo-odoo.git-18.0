# -*- coding: utf-8 -*-
"""
Revenue Forecast Report

Comprehensive revenue forecasting report with variance analysis.
"""

from odoo import models, api, fields


class RevenueforecastReport(models.AbstractModel):
    """Revenue Forecast Report"""
    
    _name = 'report.records_management.revenue_forecast_report'
    _description = 'Revenue Forecast Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        """Get values for revenue forecast report"""
        docs = self.env['revenue.forecaster'].browse(docids)
        
        # Calculate summary statistics
        total_forecasted = sum(docs.mapped('total_forecasted_revenue'))
        total_actual = sum(docs.mapped('total_actual_revenue'))
        total_variance = total_forecasted - total_actual
        
        # Get forecast lines with details
        forecast_lines = self.env['revenue.forecast.line'].search([
            ('forecast_id', 'in', docids)
        ], order='forecast_id, customer_id, service_type')
        
        # Group by forecast for better reporting
        forecasts_with_lines = {}
        for doc in docs:
            lines = forecast_lines.filtered(lambda l: l.forecast_id.id == doc.id)
            forecasts_with_lines[doc] = lines
        
        return {
            'doc_ids': docids,
            'doc_model': 'revenue.forecaster',
            'docs': docs,
            'forecasts_with_lines': forecasts_with_lines,
            'total_forecasted': total_forecasted,
            'total_actual': total_actual,
            'total_variance': total_variance,
            'variance_percentage': (total_variance / total_forecasted * 100) if total_forecasted else 0,
        }


class BillingConfigAuditReport(models.AbstractModel):
    """Billing Config Audit Report"""
    
    _name = 'report.records_management.billing_config_audit_report'
    _description = 'Billing Configuration Audit Trail Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        """Get values for billing config audit report"""
        docs = self.env['records.billing.config.audit'].browse(docids)
        
        # Group by action type for analysis
        action_summary = {}
        for doc in docs:
            action_type = doc.action_type
            if action_type not in action_summary:
                action_summary[action_type] = {
                    'count': 0,
                    'total_impact': 0,
                    'records': []
                }
            action_summary[action_type]['count'] += 1
            action_summary[action_type]['total_impact'] += doc.financial_impact
            action_summary[action_type]['records'].append(doc)
        
        # Calculate approval statistics
        approval_stats = {
            'pending': docs.filtered(lambda d: d.approval_status == 'pending'),
            'approved': docs.filtered(lambda d: d.approval_status == 'approved'),
            'rejected': docs.filtered(lambda d: d.approval_status == 'rejected'),
        }
        
        return {
            'doc_ids': docids,
            'doc_model': 'records.billing.config.audit',
            'docs': docs,
            'action_summary': action_summary,
            'approval_stats': approval_stats,
            'total_financial_impact': sum(docs.mapped('financial_impact')),
        }


class DocumentRetrievalMetricsReport(models.AbstractModel):
    """Document Retrieval Performance Metrics Report"""
    
    _name = 'report.records_management.retrieval_metrics_report'
    _description = 'Document Retrieval Performance Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        """Get values for retrieval metrics report"""
        docs = self.env['document.retrieval.metrics'].browse(docids)
        
        # Group by metric type for analysis
        metrics_by_type = {}
        for doc in docs:
            metric_type = doc.metric_type
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(doc)
        
        # Calculate performance statistics
        performance_stats = {
            'excellent': docs.filtered(lambda d: d.performance_rating == 'excellent'),
            'good': docs.filtered(lambda d: d.performance_rating == 'good'),
            'acceptable': docs.filtered(lambda d: d.performance_rating == 'acceptable'),
            'poor': docs.filtered(lambda d: d.performance_rating == 'poor'),
            'unacceptable': docs.filtered(lambda d: d.performance_rating == 'unacceptable'),
        }
        
        # Calculate averages by metric type
        averages = {}
        for metric_type, records in metrics_by_type.items():
            if records:
                averages[metric_type] = {
                    'avg_value': sum(r.metric_value for r in records) / len(records),
                    'avg_quality': sum(r.quality_score for r in records) / len(records),
                    'count': len(records)
                }
        
        return {
            'doc_ids': docids,
            'doc_model': 'document.retrieval.metrics',
            'docs': docs,
            'metrics_by_type': metrics_by_type,
            'performance_stats': performance_stats,
            'averages': averages,
            'overall_quality_avg': sum(docs.mapped('quality_score')) / len(docs) if docs else 0,
        }
