# -*- coding: utf-8 -*-
"""
Records Department Billing Contact

Model to support departmental billing contact dashboards, analytics, and
approval history as referenced in existing views.
"""

from odoo import models, fields, api, _


class RecordsDepartmentBillingContact(models.Model):
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'department_id, contact_name'

    # Identity
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    contact_name = fields.Char(string='Contact Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)

    # Relations
    department_id = fields.Many2one(comodel_name='records.department', string='Department', required=True, ondelete='cascade', tracking=True)

    # Contact details
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')

    # Billing role & budgets
    billing_role = fields.Selection([
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
        ('approver', 'Approver'),
    ], string='Billing Role', default='manager', required=True)

    monthly_budget = fields.Monetary(string="Monthly Budget", currency_field="currency_id")
    current_month_charges = fields.Monetary(string="Current Month Charges", currency_field="currency_id")
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True, readonly=True, comodel_name='res.currency')
    budget_utilization = fields.Float(string='Budget Utilization %', compute='_compute_budget_utilization', store=True)

    # Approvals
    approval_authority = fields.Boolean(string='Approval Authority')
    approval_limit = fields.Monetary(string="Approval Limit", currency_field="currency_id")
    approval_history_ids = fields.One2many(
        comodel_name='records.department.billing.approval',
        inverse_name='billing_contact_id',
        string='Approval History'
    )
    approval_count = fields.Integer(string='Approvals', compute='_compute_approval_count', store=True)

    # Analytics - Current period
    current_month_budget = fields.Monetary(string="Current Month Budget", currency_field="currency_id")
    current_month_actual = fields.Monetary(string="Current Month Actual", currency_field="currency_id")
    current_month_variance = fields.Monetary(
        string="Current Month Variance", compute="_compute_variances", store=True, currency_field="currency_id"
    )
    current_month_forecast = fields.Monetary(string="Current Month Forecast", currency_field="currency_id")

    # Analytics - YTD
    ytd_budget = fields.Monetary(string="YTD Budget", currency_field="currency_id")
    ytd_actual = fields.Monetary(string="YTD Actual", currency_field="currency_id")
    ytd_variance = fields.Monetary(
        string="YTD Variance", compute="_compute_variances", store=True, currency_field="currency_id"
    )
    ytd_variance_percentage = fields.Float(string='YTD Variance %', compute='_compute_variances', store=True)

    # Notifications
    budget_alert_threshold = fields.Float(string='Budget Alert Threshold (%)', default=90.0)
    email_notifications = fields.Boolean(string='Email Notifications')
    weekly_reports = fields.Boolean(string='Weekly Reports')
    monthly_statements = fields.Boolean(string='Monthly Statements')
    cc_finance_team = fields.Boolean(string='CC Finance Team')
    cc_department_head = fields.Boolean(string='CC Department Head')
    cc_additional_emails = fields.Text(string='Additional CC Emails')

    # Grouping helper
    budget_range = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Budget Range', compute='_compute_budget_range', store=True)

    @api.depends('contact_name', 'department_id')
    def _compute_name(self):
        for rec in self:
            if rec.department_id and rec.contact_name:
                rec.name = f"{rec.department_id.display_name} / {rec.contact_name}"
            else:
                rec.name = rec.contact_name or _('New')

    @api.depends('monthly_budget', 'current_month_charges')
    def _compute_budget_utilization(self):
        for rec in self:
            if rec.monthly_budget:
                rec.budget_utilization = round((rec.current_month_charges or 0.0) / rec.monthly_budget * 100.0, 2)
            else:
                rec.budget_utilization = 0.0

    @api.depends('approval_history_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.approval_history_ids)

    @api.depends('current_month_budget', 'current_month_actual', 'ytd_budget', 'ytd_actual')
    def _compute_variances(self):
        for rec in self:
            rec.current_month_variance = (rec.current_month_budget or 0.0) - (rec.current_month_actual or 0.0)
            rec.ytd_variance = (rec.ytd_budget or 0.0) - (rec.ytd_actual or 0.0)
            if rec.ytd_budget:
                rec.ytd_variance_percentage = round((rec.ytd_variance / rec.ytd_budget) * 100.0, 2)
            else:
                rec.ytd_variance_percentage = 0.0

    @api.depends('monthly_budget')
    def _compute_budget_range(self):
        for rec in self:
            amt = rec.monthly_budget or 0.0
            if amt > 10000:
                rec.budget_range = 'high'
            elif amt > 1000:
                rec.budget_range = 'medium'
            else:
                rec.budget_range = 'low'

    # Basic actions referenced in views
    def action_view_approvals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approval History'),
            'res_model': 'records.department.billing.approval',
            'view_mode': 'tree,form',
            'domain': [('billing_contact_id', '=', self.id)],
            'context': {'default_billing_contact_id': self.id},
        }

    def action_budget_report(self):
        # Placeholder for PDF/XLS generation
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def action_send_bill_notification(self):
        # Placeholder for email notification logic
        self.ensure_one()
        self.message_post(body=_('Billing notification sent.'))
        return True
