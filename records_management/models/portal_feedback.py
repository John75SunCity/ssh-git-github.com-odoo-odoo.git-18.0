# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalFeedback(models.Model):
    _name = "portal.feedback"
    _description = "Portal Feedback"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # Essential Portal Feedback Fields
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    feedback_type = fields.Selection(
        [
            ("service_rating", "Service Rating"),
            ("complaint", "Complaint"),
            ("suggestion", "Suggestion"),
            ("compliment", "Compliment"),
            ("general", "General Feedback"),
            ("technical_issue", "Technical Issue"),
            ("billing_inquiry", "Billing Inquiry"),
        ],
        string="Feedback Type",
        required=True,
        tracking=True,
    )

    # Ratings and Scores
    overall_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Overall Rating",
        tracking=True,
    )

    service_quality_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Service Quality Rating",
    )

    communication_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Communication Rating",
    )

    timeliness_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Timeliness Rating",
    )

    # Customer Satisfaction Metrics
    nps_score = fields.Selection(
        [
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
        ],
        string="NPS Score (0-10)",
    )

    ces_score = fields.Selection(
        [
            ("1", "Very Difficult"),
            ("2", "Difficult"),
            ("3", "Neutral"),
            ("4", "Easy"),
            ("5", "Very Easy"),
        ],
        string="Customer Effort Score",
    )

    # Feedback Details
    feedback_subject = fields.Char(string="Subject", required=True)
    feedback_description = fields.Text(string="Detailed Feedback", required=True)

    # Service Related
    service_date = fields.Date(string="Service Date")
    service_type = fields.Selection(
        [
            ("document_storage", "Document Storage"),
            ("document_retrieval", "Document Retrieval"),
            ("shredding", "Shredding Service"),
            ("scanning", "Document Scanning"),
            ("pickup_delivery", "Pickup/Delivery"),
            ("portal_access", "Portal Access"),
            ("billing", "Billing"),
            ("other", "Other"),
        ],
        string="Service Type",
    )

    # Response Management
    response_required = fields.Boolean(string="Response Required", default=True)
    responded = fields.Boolean(string="Responded", default=False)
    response_date = fields.Datetime(string="Response Date")
    response_text = fields.Text(string="Response")
    assigned_to = fields.Many2one("res.users", string="Assigned To")

    # Priority and Escalation
    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="medium",
    )

    escalated = fields.Boolean(string="Escalated", default=False)
    escalation_reason = fields.Text(string="Escalation Reason")
    escalated_to = fields.Many2one("res.users", string="Escalated To")

    # Follow-up
    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")
    follow_up_notes = fields.Text(string="Follow-up Notes")

    # Analytics and Insights
    sentiment = fields.Selection(
        [
            ("very_negative", "Very Negative"),
            ("negative", "Negative"),
            ("neutral", "Neutral"),
            ("positive", "Positive"),
            ("very_positive", "Very Positive"),
        ],
        string="Sentiment",
        compute="_compute_sentiment",
    )

    competitive_mention = fields.Boolean(string="Competitive Mention", default=False)
    improvement_area = fields.Selection(
        [
            ("service_quality", "Service Quality"),
            ("communication", "Communication"),
            ("timeliness", "Timeliness"),
            ("pricing", "Pricing"),
            ("technology", "Technology"),
            ("staff", "Staff"),
            ("other", "Other"),
        ],
        string="Main Improvement Area",
    )

    # Contact Information
    contact_method = fields.Selection(
        [
            ("portal", "Portal"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("in_person", "In Person"),
            ("survey", "Survey"),
        ],
        string="Contact Method",
        default="portal",
    )

    # Resolution
    resolution_status = fields.Selection(
        [
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
            ("escalated", "Escalated"),
        ],
        string="Resolution Status",
        default="open",
        tracking=True,
    )

    resolution_notes = fields.Text(string="Resolution Notes")
    customer_satisfied_with_resolution = fields.Boolean(
        string="Customer Satisfied with Resolution"
    )

    # Related Records
    service_request_id = fields.Many2one(
        "portal.request", string="Related Service Request"
    )
    account_manager = fields.Many2one("res.users", string="Account Manager")

    # System Fields
    submission_date = fields.Datetime(
        string="Submission Date", default=fields.Datetime.now
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.depends("overall_rating", "nps_score", "feedback_type")
    def _compute_sentiment(self):
        """Compute sentiment based on ratings and feedback type"""
        for record in self:
            if record.feedback_type == "complaint":
                record.sentiment = "negative"
            elif record.feedback_type == "compliment":
                record.sentiment = "positive"
            elif record.overall_rating:
                rating = int(record.overall_rating)
                if rating <= 2:
                    record.sentiment = "negative"
                elif rating == 3:
                    record.sentiment = "neutral"
                else:
                    record.sentiment = "positive"
            elif record.nps_score:
                nps = int(record.nps_score)
                if nps <= 6:
                    record.sentiment = "negative"
                elif nps <= 8:
                    record.sentiment = "neutral"
                else:
                    record.sentiment = "positive"
            else:
                record.sentiment = "neutral"

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === COMPREHENSIVE MISSING FIELDS ===
    active = fields.Boolean(string='Flag', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    notes = fields.Text(string='Description', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Status', default='draft', tracking=True)
    created_date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string='Date', tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    rating = fields.Selection([('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')], string='Rating')
    feedback_text = fields.Text(string='Feedback')
    resolved = fields.Boolean(string='Resolved', default=False)
    # === COMPREHENSIVE MISSING FIELDS ===
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    workflow_state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Workflow State', default='draft')
    next_action_date = fields.Date(string='Next Action Date')
    deadline_date = fields.Date(string='Deadline')
    completion_date = fields.Datetime(string='Completion Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    assigned_team_id = fields.Many2one('hr.department', string='Assigned Team')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_score = fields.Float(string='Quality Score', digits=(3, 2))
    validation_required = fields.Boolean(string='Validation Required')
    validated_by_id = fields.Many2one('res.users', string='Validated By')
    validation_date = fields.Datetime(string='Validation Date')
    reference_number = fields.Char(string='Reference Number')
    external_reference = fields.Char(string='External Reference')
    documentation_complete = fields.Boolean(string='Documentation Complete')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments')
    performance_score = fields.Float(string='Performance Score', digits=(5, 2))
    efficiency_rating = fields.Selection([('poor', 'Poor'), ('fair', 'Fair'), ('good', 'Good'), ('excellent', 'Excellent')], string='Efficiency Rating')
    last_review_date = fields.Date(string='Last Review Date')
    next_review_date = fields.Date(string='Next Review Date')




    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =============================================================================
    # PORTAL FEEDBACK ACTION METHODS
    # =============================================================================

    def action_close(self):
        """Close the feedback ticket."""
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Feedback ticket closed."))
        return True

    def action_escalate(self):
        """Escalate feedback to management."""
        self.ensure_one()
        # Create escalation activity for manager
        manager_group = self.env.ref("records_management.group_records_manager")
        manager_users = manager_group.users

        if manager_users:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Escalated Feedback: %s") % self.name,
                note=_(
                    "This feedback has been escalated and requires management attention.\n\nFeedback Details:\n%s"
                )
                % self.description,
                user_id=manager_users[0].id,
            )

        self.message_post(body=_("Feedback escalated to management."))
        return True

    def action_mark_reviewed(self):
        """Mark feedback as reviewed."""
        self.ensure_one()
        self.write({"state": "active"})  # Using active as "reviewed" state
        self.message_post(body=_("Feedback marked as reviewed."))
        return True

    def action_reopen(self):
        """Reopen closed feedback."""
        self.ensure_one()
        if self.state != "inactive":
            raise UserError(_("Only closed feedback can be reopened."))

        self.write({"state": "draft"})
        self.message_post(body=_("Feedback reopened for further review."))
        return True

    def action_respond(self):
        """Respond to customer feedback."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Respond to Feedback"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "portal.feedback",
                "default_res_id": self.id,
                "default_use_template": False,
                "default_composition_mode": "comment",
                "default_subject": f"Response to: {self.name}",
            },
        }

    def action_view_customer_history(self):
        """View feedback history for this customer."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback History"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id), ("id", "!=", self.id)],
            "context": {
                "search_default_user_id": self.user_id.id,
                "group_by": "date_created",
            },
        }

    def action_view_improvement_actions(self):
        """View improvement actions related to this feedback."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Improvement Actions"),
            "res_model": "survey.improvement.action",
            "view_mode": "tree,form",
            "domain": [("feedback_id", "=", self.id)],
            "context": {
                "default_feedback_id": self.id,
                "default_name": f"Improvement for: {self.name}",
            },
        }

    def action_view_related_tickets(self):
        """View related feedback tickets."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Tickets"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [
                "|",
                ("user_id", "=", self.user_id.id),
                ("description", "ilike", self.name.split()[0] if self.name else ""),
            ],
            "context": {
                "search_default_user_id": self.user_id.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
