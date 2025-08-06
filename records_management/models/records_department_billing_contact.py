# -*- coding: utf-8 -*-
"""
Records Department Billing Contact Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDepartmentBillingContact(models.Model):
    """
    Department Billing Contact - Manages billing contacts and approval workflows
    """

    _name = "records.department.billing.contact"
    _description = "Records Department Billing Contact"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Contact Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact Partner",
        required=True,
        tracking=True,
        domain="[('is_company', '=', False)]",
    )
    department_id = fields.Many2one(
        "records.department", string="Department", required=True, tracking=True
    )
    email = fields.Char(string="Email", related="partner_id.email", store=True)
    phone = fields.Char(string="Phone", related="partner_id.phone", store=True)
    mobile = fields.Char(string="Mobile", related="partner_id.mobile", store=True)

    # ============================================================================
    # BILLING ROLE AND AUTHORIZATION
    # ============================================================================
    billing_role = fields.Selection(
        [
            ("primary", "Primary Contact"),
            ("secondary", "Secondary Contact"),
            ("approver", "Approver"),
            ("reviewer", "Reviewer"),
            ("backup", "Backup Contact"),
        ],
        string="Billing Role",
        required=True,
        tracking=True,
    )

    authorization_level = fields.Selection(
        [
            ("basic", "Basic Authorization"),
            ("intermediate", "Intermediate Authorization"),
            ("advanced", "Advanced Authorization"),
            ("full", "Full Authorization"),
        ],
        string="Authorization Level",
        default="basic",
        tracking=True,
    )

    approval_limit = fields.Monetary(
        string="Approval Limit",
        currency_field="currency_id",
        help="Maximum amount this contact can approve",
    )

    # ============================================================================
    # BILLING PREFERENCES
    # ============================================================================
    notification_preferences = fields.Selection(
        [
            ("email", "Email Only"),
            ("sms", "SMS Only"),
            ("both", "Email and SMS"),
            ("none", "No Notifications"),
        ],
        string="Notification Preferences",
        default="email",
    )

    billing_frequency = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
        ],
        string="Billing Frequency",
        default="monthly",
    )

    invoice_delivery_preference = fields.Selection(
        [
            ("email", "Email"),
            ("postal", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("both", "Email and Postal"),
        ],
        string="Invoice Delivery",
        default="email",
    )

    # ============================================================================
    # SERVICE AND WORKFLOW
    # ============================================================================
    service_type = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("shredding", "Shredding Services"),
            ("scanning", "Scanning Services"),
            ("retrieval", "Retrieval Services"),
            ("all", "All Services"),
        ],
        string="Service Type",
        default="all",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("inactive", "Inactive"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # DATES AND SCHEDULING
    # ============================================================================
    start_date = fields.Date(
        string="Start Date", default=fields.Date.today, tracking=True
    )
    end_date = fields.Date(string="End Date")
    last_contact_date = fields.Date(string="Last Contact Date")

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    approval_history_ids = fields.One2many(
        "approval.history", "contact_id", string="Approval History"
    )  # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    approval_count = fields.Integer(
        string="Approval Count", compute="_compute_approval_count"
    )

    # ============================================================================
    # DESCRIPTIVE FIELDS
    # ============================================================================
    notes = fields.Text(string="Internal Notes")
    special_instructions = fields.Text(string="Special Instructions")
    communication_preferences = fields.Text(string="Communication Preferences")

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    def _compute_approval_count(self):
        """Count approval history records"""
        for record in self:
            record.approval_count = len(record.approval_history_ids)

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the billing contact"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Only draft contacts can be activated")
        self.write({"state": "active"})
        self.message_post(body="Billing contact activated")

    def action_suspend(self):
        """Suspend the billing contact"""
        self.ensure_one()
        if self.state != "active":
            raise UserError("Only active contacts can be suspended")
        self.write({"state": "suspended"})
        self.message_post(body="Billing contact suspended")

    def action_deactivate(self):
        """Deactivate the billing contact"""
        self.ensure_one()
        self.write({"state": "inactive", "end_date": fields.Date.today()})
        self.message_post(body="Billing contact deactivated")

    def action_view_approvals(self):
        """View approval history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Approval History",
            "res_model": "approval.history",
            "view_mode": "tree,form",
            "domain": [("contact_id", "=", self.id)],
            "context": {"default_contact_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        """Validate date consistency"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError("Start date cannot be after end date")

    @api.constrains("approval_limit")
    def _check_approval_limit(self):
        """Validate approval limit"""
        for record in self:
            if record.approval_limit and record.approval_limit < 0:
                raise ValidationError("Approval limit must be positive")

    @api.constrains("email")
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.email and "@" not in record.email:
                raise ValidationError("Invalid email format")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic name generation"""
        for vals in vals_list:
            if "name" not in vals and "partner_id" in vals:
                partner = self.env["res.partner"].browse(vals["partner_id"])
                vals["name"] = f"Billing Contact - {partner.name}"
        return super().create(vals_list)

    def write(self, vals):
        """Override write for state change tracking"""
        if "state" in vals:
            for record in self:
                old_state = record.state
                new_state = vals["state"]
                if old_state != new_state:
                    record.message_post(
                        body=f"Status changed from {old_state} to {new_state}"
                    )
        return super().write(vals)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.partner_id.name}"
            if record.department_id:
                name += f" - {record.department_id.name}"
            if record.billing_role:
                name += f" ({record.billing_role})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by partner name, department, or role"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("partner_id.name", operator, name),
                ("department_id.name", operator, name),
                ("billing_role", operator, name),
                ("email", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    approval_authority = fields.Char(string='Approval Authority', tracking=True)
    budget_utilization = fields.Float(string='Budget Utilization (%)', tracking=True, help="Percentage of budget utilized")
    email_notifications = fields.Char(string='Email Notifications', tracking=True)
    monthly_budget = fields.Monetary(string='Monthly Budget', currency_field="currency_id", tracking=True, help="Monthly budget amount")
    approval_authority = fields.Char(string='Approval Authority', tracking=True)
    budget_utilization = fields.Char(string='Budget Utilization', tracking=True)
    email_notifications = fields.Char(string='Email Notifications', tracking=True)
    monthly_budget = fields.Char(string='Monthly Budget', tracking=True)
    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_budget_report(self):
        """Budget Report - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_budget_report_template",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }
    def action_send_bill_notification(self):
        """Send Bill Notification - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Send Bill Notification"),
            "res_model": "records.department.billing.contact",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }