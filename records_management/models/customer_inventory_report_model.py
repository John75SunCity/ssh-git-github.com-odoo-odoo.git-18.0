# -*- coding: utf-8 -*-
"""
Persistent Customer Inventory Report model

Implements the comodel referenced by customer.inventory.report.line (report_id)
and by report bindings/cron. Minimal fields to satisfy relations and basic
reporting needs.
"""

from odoo import models, fields, api, _


class CustomerInventoryReport(models.Model):
    _name = 'customer.inventory.report'
    _description = 'Customer Inventory Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, partner_id'

    # Core
    name = fields.Char(string='Name', default=lambda self: _('Customer Inventory Report'), tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Report parameters
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department')
    report_date = fields.Date(string='Report Date', default=fields.Date.context_today, tracking=True)

    # Lines
    line_ids = fields.One2many(
        comodel_name='customer.inventory.report.line',
        inverse_name='report_id',
        string='Lines',
    )

    # Totals (optional, non-blocking)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True, readonly=True, comodel_name='res.currency')
    total_documents = fields.Integer(string='Total Documents', compute='_compute_totals', store=True)
    total_monthly_cost = fields.Monetary(string='Total Monthly Cost', compute='_compute_totals', store=True, currency_field='currency_id')

    @api.depends('line_ids.document_count', 'line_ids.monthly_storage_cost')
    def _compute_totals(self):
        for rec in self:
            rec.total_documents = sum(rec.line_ids.mapped('document_count')) if rec.line_ids else 0
            rec.total_monthly_cost = sum(rec.line_ids.mapped('monthly_storage_cost')) if rec.line_ids else 0.0

    # Cron entry point (kept minimal for now)
    @api.model
    def generate_monthly_reports(self):
        """Hook for scheduled action. Implement business logic later.

        For now, it's a safe no-op to satisfy the cron reference and audits.
        """
        return True
