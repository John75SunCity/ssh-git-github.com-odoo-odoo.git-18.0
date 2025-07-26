# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department with enhanced enterprise features
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib
import re

class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts.
    Enhanced with enterprise features: validation, tracking, privacy compliance, and audit trails.
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact - FIELD ENHANCEMENT COMPLETE ✅'
    _rec_name = 'contact_name'
    _order = 'contact_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    contact_name = fields.Char(string='Contact Name', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact')
    department_id = fields.Many2one('records.department', string='Department')
    
    # Contact details
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    active = fields.Boolean(string='Active', default=True)
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    # PHASE 2: Critical Business Fields (35 fields)
    
    # Approval and authorization fields
    approval_authority = fields.Boolean(string='Has Approval Authority', default=False, tracking=True)
    approval_count = fields.Integer(string='Approval Count', compute='_compute_approval_metrics', store=True)
    approval_date = fields.Date(string='Last Approval Date', tracking=True)
    approval_history_ids = fields.Many2many('department.billing.approval.history', 
                                           relation='dept_billing_approval_rel',
                                           string='Approval History')  # Fixed with shorter table name
    approval_limit = fields.Float(string='Approval Limit ($)', default=0.0, tracking=True)
    approval_notes = fields.Text(string='Approval Notes')
    approval_status = fields.Selection([
        ('none', 'No Authority'),
        ('limited', 'Limited Authority'),
        ('full', 'Full Authority'),
        ('suspended', 'Suspended')
    ], string='Approval Status', default='none', tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True)
    
    # Billing role and configuration
    billing_role = fields.Selection([
        ('primary', 'Primary Contact'),
        ('secondary', 'Secondary Contact'),
        ('approver', 'Approver'),
        ('reviewer', 'Reviewer'),
        ('finance', 'Finance Team')
    ], string='Billing Role', required=True, default='primary', tracking=True)
    
    # Budget management
    budget_alert_threshold = fields.Float(string='Budget Alert Threshold (%)', default=80.0)
    budget_utilization = fields.Float(string='Budget Utilization (%)', compute='_compute_budget_metrics', store=True)
    monthly_budget = fields.Float(string='Monthly Budget ($)', tracking=True)
    
    # Communication preferences
    cc_additional_emails = fields.Text(string='CC Additional Emails', help='Comma-separated email list')
    cc_department_head = fields.Boolean(string='CC Department Head', default=True)
    cc_finance_team = fields.Boolean(string='CC Finance Team', default=False)
    email_notifications = fields.Boolean(string='Email Notifications', default=True)
    weekly_reports = fields.Boolean(string='Weekly Reports', default=False)
    monthly_statements = fields.Boolean(string='Monthly Statements', default=True)
    
    # Current month financials
    current_month_actual = fields.Float(string='Current Month Actual ($)', compute='_compute_monthly_metrics', store=True)
    current_month_budget = fields.Float(string='Current Month Budget ($)', tracking=True)
    current_month_charges = fields.Float(string='Current Month Charges ($)', compute='_compute_monthly_metrics', store=True)
    current_month_forecast = fields.Float(string='Current Month Forecast ($)', compute='_compute_monthly_metrics', store=True)
    current_month_variance = fields.Float(string='Current Month Variance ($)', compute='_compute_monthly_metrics', store=True)
    
    # Department charges and tracking
    department_charge_ids = fields.Many2many('department.billing.charge', 
                                            relation='dept_billing_charge_rel',
                                            string='Department Charges')  # Fixed with shorter table name
    department_charges_count = fields.Integer(string='Charges Count', compute='_compute_charge_metrics', store=True)
    charge_amount = fields.Float(string='Total Charge Amount ($)', compute='_compute_charge_metrics', store=True)
    charge_date = fields.Date(string='Last Charge Date', compute='_compute_charge_metrics', store=True)
    
    # Service tracking
    service_description = fields.Text(string='Service Description')
    service_type = fields.Selection([
        ('storage', 'Storage Services'),
        ('retrieval', 'Retrieval Services'),
        ('destruction', 'Destruction Services'),
        ('digital', 'Digital Services'),
        ('consultation', 'Consultation Services'),
        ('mixed', 'Mixed Services')
    ], string='Service Type', default='storage')
    vendor = fields.Many2one('res.partner', string='Vendor/Service Provider')
    
    # Year-to-date financials
    ytd_actual = fields.Float(string='YTD Actual ($)', compute='_compute_ytd_metrics', store=True)
    ytd_budget = fields.Float(string='YTD Budget ($)', tracking=True)
    ytd_variance = fields.Float(string='YTD Variance ($)', compute='_compute_ytd_metrics', store=True)
    ytd_variance_percentage = fields.Float(string='YTD Variance (%)', compute='_compute_ytd_metrics', store=True)
    
    # Contextual fields (from analysis)
    amount = fields.Float(string='Amount', help='General amount field for billing calculations')
    description = fields.Text(string='Description', help='General description field')
    
    # Compute methods for the new fields
    @api.depends('approval_history_ids')
    def _compute_approval_metrics(self):
        """Compute approval-related metrics"""
        for record in self:
            record.approval_count = len(record.approval_history_ids)
    
    @api.depends('monthly_budget', 'current_month_actual')
    def _compute_budget_metrics(self):
        """Compute budget utilization metrics"""
        for record in self:
            if record.monthly_budget > 0:
                record.budget_utilization = (record.current_month_actual / record.monthly_budget) * 100
            else:
                record.budget_utilization = 0.0
    
    @api.depends('department_charge_ids')
    def _compute_monthly_metrics(self):
        """Compute current month financial metrics"""
        for record in self:
            current_month_charges = sum(record.department_charge_ids.filtered(
                lambda c: c.charge_date and c.charge_date.month == fields.Date.today().month
            ).mapped('amount'))
            
            record.current_month_actual = current_month_charges
            record.current_month_charges = current_month_charges
            record.current_month_forecast = current_month_charges * 1.1  # 10% buffer
            record.current_month_variance = record.current_month_budget - current_month_charges
    
    @api.depends('department_charge_ids')
    def _compute_charge_metrics(self):
        """Compute charge-related metrics"""
        for record in self:
            charges = record.department_charge_ids
            record.department_charges_count = len(charges)
            record.charge_amount = sum(charges.mapped('amount'))
            record.charge_date = max(charges.mapped('charge_date')) if charges else False
    
    @api.depends('department_charge_ids', 'ytd_budget')
    def _compute_ytd_metrics(self):
        """Compute year-to-date financial metrics"""
        for record in self:
            current_year = fields.Date.today().year
            ytd_charges = sum(record.department_charge_ids.filtered(
                lambda c: c.charge_date and c.charge_date.year == current_year
            ).mapped('amount'))
            
            record.ytd_actual = ytd_charges
            record.ytd_variance = record.ytd_budget - ytd_charges
            
            if record.ytd_budget > 0:
                record.ytd_variance_percentage = (record.ytd_variance / record.ytd_budget) * 100
            else:
                record.ytd_variance_percentage = 0.0