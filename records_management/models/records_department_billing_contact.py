# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsDepartmentBillingContact(models.Model):
    """Model for department billing contacts."""
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'department_id, sequence, name'

    # Core fields
    name = fields.Char('Contact Name', required=True, tracking=True)
    sequence = fields.Integer('Sequence', default=10)
    
    # Contact relationships
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  domain="[('is_company', '=', True)]",
                                  help='Customer this contact belongs to')
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact',
                                         help='Specific billing contact person')
    department_id = fields.Many2one('records.department', string='Department')
    
    # Contact details
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Phone', tracking=True)
    mobile = fields.Char('Mobile')
    
    # Billing preferences
    contact_type = fields.Selection([
        ('primary', 'Primary Contact'),
        ('billing', 'Billing Contact'), 
        ('technical', 'Technical Contact'),
        ('backup', 'Backup Contact')
    ], string='Contact Type', default='billing', required=True)
    
    # Communication preferences
    receives_invoices = fields.Boolean('Receives Invoices', default=True)
    receives_statements = fields.Boolean('Receives Statements', default=True)
    receives_notifications = fields.Boolean('Receives Notifications', default=True)
    
    # Preferred communication method
    communication_method = fields.Selection([
        ('email', 'Email'),
        ('mail', 'Postal Mail'),
        ('phone', 'Phone'),
        ('portal', 'Customer Portal')
    ], string='Preferred Method', default='email')
    
    # Status and dates
    active = fields.Boolean('Active', default=True, tracking=True)
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date')
    
    # Notes and additional info
    notes = fields.Text('Notes')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    # Additional Critical Business Fields for Department Billing
    
    # Financial and Budget Management
    approval_authority = fields.Boolean(string='Has Approval Authority', default=False, tracking=True)
    approval_limit = fields.Float(string='Approval Limit', default=0.0, tracking=True)
    approval_count = fields.Integer(string='Approvals Count', compute='_compute_approval_count')
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ], string='Current Approval Status', default='pending', tracking=True)
    approval_date = fields.Datetime(string='Last Approval Date', tracking=True)
    approval_notes = fields.Text(string='Approval Notes')
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True)
    approval_history_ids = fields.One2many('department.billing.approval.history', 'contact_id', string='Approval History')
    
    # Billing Role and Responsibilities
    billing_role = fields.Selection([
        ('approver', 'Approver'),
        ('reviewer', 'Reviewer'),
        ('recipient', 'Recipient'),
        ('admin', 'Administrator')
    ], string='Billing Role', default='recipient', required=True, tracking=True)
    
    # Budget Tracking and Alerts
    monthly_budget = fields.Float(string='Monthly Budget', default=0.0, tracking=True)
    budget_alert_threshold = fields.Float(string='Budget Alert Threshold (%)', default=80.0)
    budget_utilization = fields.Float(string='Budget Utilization (%)', compute='_compute_budget_utilization')
    
    # Current Month Financial Tracking
    current_month_budget = fields.Float(string='Current Month Budget', compute='_compute_current_month_budget')
    current_month_actual = fields.Float(string='Current Month Actual', compute='_compute_current_month_actual')
    current_month_forecast = fields.Float(string='Current Month Forecast', compute='_compute_current_month_forecast')
    current_month_variance = fields.Float(string='Current Month Variance', compute='_compute_current_month_variance')
    current_month_charges = fields.Float(string='Current Month Charges', compute='_compute_current_month_charges')
    
    # Year-to-Date Tracking
    ytd_budget = fields.Float(string='YTD Budget', compute='_compute_ytd_budget')
    ytd_actual = fields.Float(string='YTD Actual', compute='_compute_ytd_actual')
    ytd_variance = fields.Float(string='YTD Variance', compute='_compute_ytd_variance')
    ytd_variance_percentage = fields.Float(string='YTD Variance %', compute='_compute_ytd_variance_percentage')
    
    # Charge Management
    department_charge_ids = fields.One2many('department.billing.charge', 'contact_id', string='Department Charges')
    department_charges_count = fields.Integer(string='Department Charges Count', compute='_compute_department_charges_count')
    charge_amount = fields.Float(string='Latest Charge Amount')
    charge_date = fields.Date(string='Latest Charge Date')
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning'),
        ('consultation', 'Consultation')
    ], string='Primary Service Type')
    service_description = fields.Text(string='Service Description')
    vendor = fields.Many2one('res.partner', string='Primary Vendor', domain="[('supplier_rank', '>', 0)]")
    
    # Email and Notification Configuration
    email_notifications = fields.Boolean(string='Email Notifications Enabled', default=True, tracking=True)
    cc_additional_emails = fields.Char(string='CC Additional Emails', help='Comma-separated email addresses')
    cc_department_head = fields.Boolean(string='CC Department Head', default=False)
    cc_finance_team = fields.Boolean(string='CC Finance Team', default=False)
    monthly_statements = fields.Boolean(string='Receive Monthly Statements', default=True)
    weekly_reports = fields.Boolean(string='Receive Weekly Reports', default=False)
    
    # Additional fields for complete coverage
    amount = fields.Float(string='Amount')  # Contextual field
    description = fields.Text(string='Description')  # Contextual field
    contact_name = fields.Char(string='Contact Name', related='name', store=True)  # Explicit field for views
    
    # Compute Methods for Department Billing Contact
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_history_ids)
    
    @api.depends('monthly_budget', 'current_month_actual')
    def _compute_budget_utilization(self):
        for record in self:
            if record.monthly_budget:
                record.budget_utilization = (record.current_month_actual / record.monthly_budget) * 100
            else:
                record.budget_utilization = 0.0
    
    def _compute_current_month_budget(self):
        # Placeholder for current month budget calculation
        for record in self:
            record.current_month_budget = record.monthly_budget
    
    def _compute_current_month_actual(self):
        # Calculate actual charges for current month
        for record in self:
            current_month_charges = record.department_charge_ids.filtered(
                lambda c: c.charge_date and c.charge_date.month == fields.Date.today().month
            )
            record.current_month_actual = sum(current_month_charges.mapped('amount'))
    
    def _compute_current_month_forecast(self):
        # Forecast based on current actuals and trends
        for record in self:
            record.current_month_forecast = record.current_month_actual * 1.1  # Simple 10% buffer
    
    @api.depends('current_month_budget', 'current_month_actual')
    def _compute_current_month_variance(self):
        for record in self:
            record.current_month_variance = record.current_month_actual - record.current_month_budget
    
    def _compute_current_month_charges(self):
        for record in self:
            record.current_month_charges = record.current_month_actual
    
    def _compute_ytd_budget(self):
        # Calculate year-to-date budget
        for record in self:
            current_month = fields.Date.today().month
            record.ytd_budget = record.monthly_budget * current_month
    
    def _compute_ytd_actual(self):
        # Calculate year-to-date actual charges
        for record in self:
            year_start = fields.Date.today().replace(month=1, day=1)
            ytd_charges = record.department_charge_ids.filtered(
                lambda c: c.charge_date and c.charge_date >= year_start
            )
            record.ytd_actual = sum(ytd_charges.mapped('amount'))
    
    @api.depends('ytd_budget', 'ytd_actual')
    def _compute_ytd_variance(self):
        for record in self:
            record.ytd_variance = record.ytd_actual - record.ytd_budget
    
    @api.depends('ytd_variance', 'ytd_budget')
    def _compute_ytd_variance_percentage(self):
        for record in self:
            if record.ytd_budget:
                record.ytd_variance_percentage = (record.ytd_variance / record.ytd_budget) * 100
            else:
                record.ytd_variance_percentage = 0.0
    
    def _compute_department_charges_count(self):
        for record in self:
            record.department_charges_count = len(record.department_charge_ids)
    
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate date constraints"""
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(_('End date cannot be earlier than start date'))
    
    @api.onchange('billing_contact_id')
    def _onchange_billing_contact(self):
        """Update contact details when billing contact changes"""
        if self.billing_contact_id:
            self.email = self.billing_contact_id.email
            self.phone = self.billing_contact_id.phone
            self.mobile = self.billing_contact_id.mobile
            if not self.name:
                self.name = self.billing_contact_id.name


# Related Models for One2many relationships
class DepartmentBillingApprovalHistory(models.Model):
    _name = 'department.billing.approval.history'
    _description = 'Department Billing Approval History'
    
    contact_id = fields.Many2one('records.department.billing.contact', string='Contact', required=True, ondelete='cascade')
    approval_type = fields.Selection([
        ('contact', 'Contact Approval'),
        ('charge', 'Charge Approval'),
        ('limit', 'Limit Approval')
    ], string='Approval Type', required=True)
    status = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending')
    ], string='Status', required=True)


class DepartmentBillingCharge(models.Model):
    _name = 'department.billing.charge'
    _description = 'Department Billing Charge'
    
    contact_id = fields.Many2one('records.department.billing.contact', string='Contact', required=True, ondelete='cascade')
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning'),
        ('consultation', 'Consultation')
    ], string='Service Type', required=True)
    invoice_id = fields.Many2one('account.move', string='Related Invoice')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid')
    ], string='Status', default='draft')
    
