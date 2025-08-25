# -*- coding: utf-8 -*-
"""
Customer Billing Profile Module

Manages customer-specific billing configurations, including cycles, payment terms,
prepaid options, and automated invoicing rules.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CustomerBillingProfile(models.Model):
    _name = 'customer.billing.profile'
    _description = 'Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE & WORKFLOW
    # ============================================================================
    name = fields.Char(string='Profile Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('annually', 'Annually')
    ], string='Default Billing Cycle', default='monthly', tracking=True)
    billing_day = fields.Integer(string='Billing Day of Month', default=1, help="Day of the month to generate invoices (1-28).")
    auto_invoice = fields.Boolean(string='Auto-Generate Invoices', default=True, tracking=True)
    auto_send_invoices = fields.Boolean(string='Auto-Send Invoices by Email', default=True, tracking=True)
    auto_send_statements = fields.Boolean(string='Auto-Send Statements', default=False, tracking=True)
    invoice_due_days = fields.Integer(string='Invoice Due Days', default=30)
    payment_terms_id = fields.Many2one('account.payment.term', string='Payment Terms')
    invoice_template_id = fields.Many2one('report.template', string='Invoice Template')

    # ============================================================================
    # SERVICE & STORAGE BILLING
    # ============================================================================
    auto_generate_service_invoices = fields.Boolean(string='Auto-Invoice Services', default=True)
    service_billing_cycle = fields.Selection(related='billing_cycle', string='Service Billing Cycle', readonly=True)
    auto_generate_storage_invoices = fields.Boolean(string='Auto-Invoice Storage', default=True)
    storage_billing_cycle = fields.Selection(related='billing_cycle', string='Storage Billing Cycle', readonly=True)
    storage_bill_in_advance = fields.Boolean(string='Bill Storage in Advance', default=True)
    storage_advance_months = fields.Integer(string='Storage Advance Months', default=1)
    next_storage_billing_date = fields.Date(string='Next Storage Billing Date', tracking=True)

    # ============================================================================
    # FINANCIAL & CREDIT
    # ============================================================================
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    credit_limit = fields.Monetary(string='Credit Limit', tracking=True)
    payment_reliability_score = fields.Float(string='Payment Reliability Score', compute='_compute_payment_reliability_score', store=True)

    # ============================================================================
    # PREPAID CONFIGURATION
    # ============================================================================
    prepaid_enabled = fields.Boolean(string='Enable Prepaid Billing', tracking=True)
    prepaid_balance = fields.Monetary(string='Prepaid Balance', compute='_compute_prepaid_balance', store=True)
    prepaid_months = fields.Integer(string='Prepaid Months', default=3)
    prepaid_discount_percent = fields.Float(string='Prepaid Discount (%)', default=0.0)
    minimum_prepaid_amount = fields.Monetary(string='Minimum Prepaid Amount')

    # ============================================================================
    # NOTIFICATIONS & CONTACTS
    # ============================================================================
    send_invoices_by_email = fields.Boolean(string='Send Invoices via Email', default=True)
    invoice_email = fields.Char(string='Invoice Email Address', help="Primary email for sending invoices.")
    late_payment_notification = fields.Boolean(string='Send Late Payment Notices', default=True)
    notification_days = fields.Integer(string='Days After Due Date to Notify', default=7)
    billing_contact_ids = fields.One2many('records.billing.contact', 'billing_profile_id', string='Billing Contacts')
    contact_count = fields.Integer(string='Contact Count', compute='_compute_contact_count', store=True)

    # ============================================================================
    # RELATED RECORDS
    # ============================================================================
    invoice_ids = fields.One2many('account.move', 'billing_profile_id', string='Invoices')
    prepaid_payment_ids = fields.One2many('account.payment', 'billing_profile_id', string='Prepaid Payments')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('billing_contact_ids')
    def _compute_contact_count(self):
        for record in self:
            record.contact_count = len(record.billing_contact_ids)

    @api.depends('prepaid_payment_ids.amount', 'invoice_ids.amount_total')
    def _compute_prepaid_balance(self):
        for record in self:
            total_payments = sum(record.prepaid_payment_ids.filtered(lambda p: p.state == 'posted').mapped("amount"))
            total_consumed = sum(record.invoice_ids.filtered(lambda i: i.state == 'posted' and i.payment_state in ('paid', 'in_payment')).mapped('amount_total'))
            record.prepaid_balance = total_payments - total_consumed

    @api.depends('partner_id.invoice_ids.payment_state')
    def _compute_payment_reliability_score(self):
        for record in self:
            if not record.partner_id:
                record.payment_reliability_score = 0.0
                continue
            invoices = self.env["account.move"].search([
                ("partner_id", "=", record.partner_id.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
            ])
            if not invoices:
                record.payment_reliability_score = 50.0  # Neutral score
                continue
            paid_on_time = invoices.filtered(lambda inv: inv.payment_state == 'paid' and (not inv.invoice_date_due or inv.invoice_date <= inv.invoice_date_due))
            score = (len(paid_on_time) / len(invoices)) * 100
            record.payment_reliability_score = min(100.0, max(0.0, score))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('billing_day')
    def _check_billing_day(self):
        for record in self:
            if not (1 <= record.billing_day <= 28):
                raise ValidationError(_("Billing day must be between 1 and 28."))

    @api.constrains('credit_limit')
    def _check_credit_limit(self):
        for record in self:
            if record.credit_limit < 0:
                raise ValidationError(_("Credit limit cannot be negative."))

    @api.constrains('prepaid_discount_percent')
    def _check_prepaid_discount(self):
        for record in self:
            if not (0 <= record.prepaid_discount_percent <= 100):
                raise ValidationError(_("Prepaid discount must be between 0% and 100%."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft profiles can be activated."))
        self.write({"state": "active"})
        self.message_post(body=_("Billing profile activated."))

    def action_suspend(self):
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active profiles can be suspended."))
        self.write({"state": "suspended"})
        self.message_post(body=_("Billing profile suspended."))

    def action_reactivate(self):
        self.ensure_one()
        if self.state != "suspended":
            raise UserError(_("Only suspended profiles can be reactivated."))
        self.write({"state": "active"})
        self.message_post(body=_("Billing profile reactivated."))

    def action_terminate(self):
        self.ensure_one()
        self.write({"state": "terminated", "active": False})
        self.message_post(body=_("Billing profile terminated."))

    def action_view_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("billing_profile_id", "=", self.id)],
            "context": {"default_billing_profile_id": self.id},
        }

