# -*- coding: utf-8 -*-
"""
Department Billing Contact
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDepartmentBillingContact(models.Model):
    """
    Department Billing Contact
    """

    _name = "records.department.billing.contact"
    _description = "Department Billing Contact"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # === ENHANCED DEPARTMENT BILLING CONTACT FIELDS ===

    # Contact Information
    contact_person = fields.Char(string="Contact Person", tracking=True)
    email = fields.Char(string="Email", tracking=True)
    phone = fields.Char(string="Phone", tracking=True)
    mobile = fields.Char(string="Mobile", tracking=True)
    department_name = fields.Char(
        string="Department Name", required=True, tracking=True
    )
    department_code = fields.Char(string="Department Code", tracking=True)

    # Billing Authority and Approval
    approval_authority = fields.Boolean(
        string="Has Approval Authority", default=False, tracking=True
    )
    approval_limit = fields.Monetary(
        string="Approval Limit", currency_field="currency_id", tracking=True
    )
    approval_date = fields.Date(string="Last Approval Date", tracking=True)
    approval_history_ids = fields.One2many(
        "approval.history", "contact_id", string="Approval History"
    )

    # Financial Information
    amount = fields.Monetary(
        string="Current Amount", currency_field="currency_id", tracking=True
    )
    budget_allocated = fields.Monetary(
        string="Budget Allocated", currency_field="currency_id", tracking=True
    )
    budget_remaining = fields.Monetary(
        string="Budget Remaining",
        compute="_compute_budget_remaining",
        store=True,
        currency_field="currency_id",
    )
    monthly_budget = fields.Monetary(
        string="Monthly Budget", currency_field="currency_id", tracking=True
    )
    annual_budget = fields.Monetary(
        string="Annual Budget", currency_field="currency_id", tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Payment Terms and Billing
    payment_terms = fields.Selection(
        [
            ("net_15", "Net 15"),
            ("net_30", "Net 30"),
            ("net_45", "Net 45"),
            ("net_60", "Net 60"),
            ("immediate", "Immediate"),
            ("custom", "Custom"),
        ],
        string="Payment Terms",
        default="net_30",
        tracking=True,
    )
    billing_frequency = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("on_demand", "On Demand"),
        ],
        string="Billing Frequency",
        default="monthly",
        tracking=True,
    )
    last_billed_date = fields.Date(string="Last Billed Date", tracking=True)
    next_billing_date = fields.Date(
        string="Next Billing Date",
        compute="_compute_next_billing_date",
        store=True,
        tracking=True,
    )

    # Cost Centers and Accounting
    cost_center_id = fields.Many2one(
        "account.analytic.account", string="Cost Center", tracking=True
    )
    gl_account_id = fields.Many2one(
        "account.account", string="GL Account", tracking=True
    )
    accounting_period = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("yearly", "Yearly")],
        string="Accounting Period",
        default="monthly",
        tracking=True,
    )

    # Service Configuration
    service_type = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("scanning", "Scanning Services"),
            ("pickup", "Pickup Services"),
            ("delivery", "Delivery Services"),
            ("all", "All Services"),
        ],
        string="Service Type",
        default="all",
        tracking=True,
    )
    service_level = fields.Selection(
        [
            ("basic", "Basic"),
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("enterprise", "Enterprise"),
        ],
        string="Service Level",
        default="standard",
        tracking=True,
    )

    # Notification and Communication Preferences
    notification_preferences = fields.Selection(
        [
            ("email", "Email Only"),
            ("phone", "Phone Only"),
            ("both", "Email and Phone"),
            ("none", "No Notifications"),
        ],
        string="Notification Preferences",
        default="email",
        tracking=True,
    )
    send_invoice_reminders = fields.Boolean(
        string="Send Invoice Reminders", default=True, tracking=True
    )
    send_budget_alerts = fields.Boolean(
        string="Send Budget Alerts", default=True, tracking=True
    )
    alert_threshold_percentage = fields.Float(
        string="Budget Alert Threshold (%)", default=80.0, tracking=True
    )

    # Billing Address
    billing_address_line1 = fields.Char(string="Billing Address Line 1", tracking=True)
    billing_address_line2 = fields.Char(string="Billing Address Line 2", tracking=True)
    billing_city = fields.Char(string="Billing City", tracking=True)
    billing_state = fields.Char(string="Billing State", tracking=True)
    billing_zip = fields.Char(string="Billing ZIP", tracking=True)
    billing_country_id = fields.Many2one(
        "res.country", string="Billing Country", tracking=True
    )

    # Performance Metrics
    average_response_time_hours = fields.Float(
        string="Average Response Time (Hours)",
        compute="_compute_performance_metrics",
        store=True,
    )
    approval_efficiency_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
        ],
        string="Approval Efficiency",
        compute="_compute_performance_metrics",
        store=True,
    )
    total_approvals_count = fields.Integer(
        string="Total Approvals", compute="_compute_approval_stats", store=True
    )
    monthly_approval_average = fields.Float(
        string="Monthly Approval Average", compute="_compute_approval_stats", store=True
    )

    # Enhanced State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Delegation and Backup Contacts
    backup_contact_id = fields.Many2one(
        "records.department.billing.contact", string="Backup Contact", tracking=True
    )
    delegation_start_date = fields.Date(string="Delegation Start Date", tracking=True)
    delegation_end_date = fields.Date(string="Delegation End Date", tracking=True)
    can_delegate_approval = fields.Boolean(
        string="Can Delegate Approval", default=False, tracking=True
    )

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    sequence = fields.Integer(string='Sequence', default=10)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')
    # Department Billing Contact Fields
    approval_notes = fields.Text('Approval Notes')
    approval_status = fields.Selection([('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    approved_by = fields.Many2one('res.users', 'Approved By')
    billing_role = fields.Selection([('primary', 'Primary Contact'), ('secondary', 'Secondary Contact'), ('backup', 'Backup Contact')], default='primary')
    budget_alert_threshold = fields.Monetary('Budget Alert Threshold', currency_field='currency_id')
    budget_approval_limit = fields.Monetary('Budget Approval Limit', currency_field='currency_id')
    contact_authorization_level = fields.Selection([('view', 'View Only'), ('approve', 'Approve'), ('admin', 'Admin')], default='view')
    contact_preferences = fields.Text('Contact Preferences')
    cost_center_access = fields.Many2many('account.analytic.account', 'billing_contact_cost_center_rel', 'contact_id', 'cost_center_id', 'Cost Center Access')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)
    department_budget_responsibility = fields.Boolean('Department Budget Responsibility', default=False)
    emergency_contact_backup = fields.Many2one('res.partner', 'Emergency Contact Backup')
    expense_approval_workflow = fields.Selection([('single', 'Single Approval'), ('dual', 'Dual Approval'), ('committee', 'Committee')], default='single')
    invoice_approval_authority = fields.Boolean('Invoice Approval Authority', default=False)
    invoice_delivery_preference = fields.Selection([('email', 'Email'), ('portal', 'Portal'), ('mail', 'Mail')], default='email')
    maximum_transaction_limit = fields.Monetary('Maximum Transaction Limit', currency_field='currency_id')
    notification_frequency = fields.Selection([('immediate', 'Immediate'), ('daily', 'Daily'), ('weekly', 'Weekly')], default='daily')
    payment_authorization_level = fields.Monetary('Payment Authorization Level', currency_field='currency_id')
    po_approval_required = fields.Boolean('PO Approval Required', default=False)
    procurement_authority = fields.Boolean('Procurement Authority', default=False)
    quarterly_review_required = fields.Boolean('Quarterly Review Required', default=True)
    reporting_frequency = fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], default='monthly')
    signature_authority = fields.Boolean('Signature Authority', default=False)
    spending_limit_override = fields.Boolean('Spending Limit Override', default=False)
    vendor_approval_authority = fields.Boolean('Vendor Approval Authority', default=False)


    @api.depends("budget_allocated", "amount")
    def _compute_budget_remaining(self):
        """Compute remaining budget."""
        for record in self:
            record.budget_remaining = (record.budget_allocated or 0) - (
                record.amount or 0
            )

    @api.depends("last_billed_date", "billing_frequency")
    def _compute_next_billing_date(self):
        """Compute next billing date based on frequency."""
        for record in self:
            if record.last_billed_date and record.billing_frequency:
                from datetime import timedelta

                if record.billing_frequency == "weekly":
                    record.next_billing_date = record.last_billed_date + timedelta(
                        weeks=1
                    )
                elif record.billing_frequency == "monthly":
                    record.next_billing_date = record.last_billed_date + timedelta(
                        days=30
                    )
                elif record.billing_frequency == "quarterly":
                    record.next_billing_date = record.last_billed_date + timedelta(
                        days=90
                    )
                elif record.billing_frequency == "annually":
                    record.next_billing_date = record.last_billed_date + timedelta(
                        days=365
                    )
                else:
                    record.next_billing_date = False
            else:
                record.next_billing_date = False

    @api.depends("approval_history_ids")
    def _compute_performance_metrics(self):
        """Compute performance metrics."""
        for record in self:
            if record.approval_history_ids:
                # Calculate average response time
                response_times = []
                for approval in record.approval_history_ids:
                    if approval.response_time_hours:
                        response_times.append(approval.response_time_hours)

                if response_times:
                    record.average_response_time_hours = sum(response_times) / len(
                        response_times
                    )
                    avg_time = record.average_response_time_hours
                    if avg_time <= 2:
                        record.approval_efficiency_rating = "excellent"
                    elif avg_time <= 8:
                        record.approval_efficiency_rating = "good"
                    elif avg_time <= 24:
                        record.approval_efficiency_rating = "fair"
                    else:
                        record.approval_efficiency_rating = "poor"
                else:
                    record.average_response_time_hours = 0
                    record.approval_efficiency_rating = "fair"
            else:
                record.average_response_time_hours = 0
                record.approval_efficiency_rating = "fair"

    @api.depends("approval_history_ids")
    def _compute_approval_stats(self):
        """Compute approval statistics."""
        for record in self:
            record.total_approvals_count = len(record.approval_history_ids)
            if record.approval_history_ids:
                # Calculate monthly average (assuming created in last 12 months)
                months_active = 12  # Simplified calculation
                record.monthly_approval_average = (
                    record.total_approvals_count / months_active
                )
            else:
                record.monthly_approval_average = 0

    def action_approve_charge(self):
        """Approve individual charge for department."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed contacts can approve charges."))

        # Create charge approval activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Charge approved by: %s") % self.name,
            note=_(
                "Individual charge has been approved by department billing contact."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Charge approved by department contact: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Charge Approved"),
                "message": _("Charge has been approved by %s") % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_approve_charges(self):
        """Approve multiple charges for department."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed contacts can approve charges."))

        # Create bulk approval activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Bulk charges approved by: %s") % self.name,
            note=_(
                "Multiple charges have been approved by department billing contact."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Bulk charges approved by: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Approve Charges"),
            "res_model": "department.charge",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("contact_id", "=", self.id), ("state", "=", "pending")],
            "context": {
                "default_contact_id": self.id,
                "search_default_contact_id": self.id,
                "search_default_pending": True,
            },
        }

    def action_budget_report(self):
        """Generate department budget report."""
        self.ensure_one()

        # Create budget report activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Budget report generated by: %s") % self.name,
            note=_("Department budget report has been generated and reviewed."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Budget report generated by: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.department_budget_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_send_bill_notification(self):
        """Send billing notification to department."""
        self.ensure_one()

        # Create notification activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Bill notification sent by: %s") % self.name,
            note=_("Billing notification has been sent to department members."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Bill notification sent by: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Send Notification"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "records.department.billing.contact",
                "default_res_id": self.id,
                "default_composition_mode": "comment",
                "default_subject": _("Billing Notification from %s") % self.name,
                "default_body": _(
                    "Please review the attached billing information for your department."
                ),
            },
        }

    def action_view_approvals(self):
        """View all approvals by this contact."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Approvals by: %s") % self.name,
            "res_model": "department.charge.approval",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("approved_by", "=", self.id)],
            "context": {
                "default_approved_by": self.id,
                "search_default_approved_by": self.id,
                "search_default_group_by_date": True,
            },
        }

    def action_view_department_charges(self):
        """View all charges for this department contact."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Department Charges: %s") % self.name,
            "res_model": "department.charge",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("contact_id", "=", self.id)],
            "context": {
                "default_contact_id": self.id,
                "search_default_contact_id": self.id,
                "search_default_group_by_status": True,
            },
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
