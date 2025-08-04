# -*- coding: utf-8 -*-
"""
Customer Inventory Report
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventoryReport(models.Model):
    """
    Customer Inventory Report
    """

    _name = "customer.inventory.report"
    _description = "Customer Inventory Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

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
    # === COMPREHENSIVE MISSING FIELDS ===
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    created_date = fields.Date(string="Date", default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string="Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    document_count = fields.Integer(string="Document Count", default=0)
    total_amount = fields.Monetary(string="Total Amount", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # === MISSING CRITICAL BUSINESS FIELDS ===
    report_generation_date = fields.Datetime(
        string="Report Generation Date",
        default=fields.Datetime.now,
        help="Date and time when the report was generated",
    )
    report_period_start = fields.Date(
        string="Report Period Start",
        help="Start date of the inventory period covered by this report",
    )
    report_period_end = fields.Date(
        string="Report Period End",
        help="End date of the inventory period covered by this report",
    )
    inventory_snapshot_id = fields.Many2one(
        "inventory.snapshot",
        string="Inventory Snapshot",
        help="Related inventory snapshot record",
    )
    report_status_details = fields.Text(
        string="Report Status Details",
        help="Detailed status information about the report generation process",
    )
    customer_notification_sent = fields.Boolean(
        string="Customer Notification Sent",
        default=False,
        help="Whether customer has been notified about this report",
    )
    report_distribution_method = fields.Selection(
        [
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("physical", "Physical Mail"),
            ("pickup", "Customer Pickup"),
        ],
        string="Report Distribution Method",
        default="email",
        help="Method for distributing the report to customer",
    )

    # === ENHANCED INVENTORY DETAILS ===
    total_containers = fields.Integer(
        string="Total Containers",
        compute="_compute_inventory_totals",
        store=True,
        help="Total number of containers in inventory",
    )
    total_documents = fields.Integer(
        string="Total Documents",
        compute="_compute_inventory_totals",
        store=True,
        help="Total number of documents in inventory",
    )
    total_storage_cubic_feet = fields.Float(
        string="Total Storage (Cubic Feet)",
        digits=(10, 2),
        compute="_compute_inventory_totals",
        store=True,
        help="Total storage space used in cubic feet",
    )
    average_document_age_days = fields.Integer(
        string="Average Document Age (Days)",
        compute="_compute_document_metrics",
        store=True,
        help="Average age of documents in days",
    )

    # === COST AND BILLING INTEGRATION ===
    monthly_storage_cost = fields.Monetary(
        string="Monthly Storage Cost",
        currency_field="currency_id",
        help="Monthly storage cost for items in this report",
    )
    retrieval_activity_cost = fields.Monetary(
        string="Retrieval Activity Cost",
        currency_field="currency_id",
        help="Cost of retrieval activities during report period",
    )
    destruction_activity_cost = fields.Monetary(
        string="Destruction Activity Cost",
        currency_field="currency_id",
        help="Cost of destruction activities during report period",
    )
    total_period_cost = fields.Monetary(
        string="Total Period Cost",
        compute="_compute_total_costs",
        currency_field="currency_id",
        store=True,
        help="Total cost for the reporting period",
    )

    # === COMPLIANCE AND AUDIT ===
    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("minor_issues", "Minor Issues"),
            ("major_issues", "Major Issues"),
            ("non_compliant", "Non-Compliant"),
        ],
        string="Compliance Status",
        default="compliant",
        help="Overall compliance status for items in this report",
    )
    retention_policy_violations = fields.Integer(
        string="Retention Policy Violations",
        default=0,
        help="Number of retention policy violations found",
    )
    security_incidents = fields.Integer(
        string="Security Incidents",
        default=0,
        help="Number of security incidents during report period",
    )
    audit_findings = fields.Text(
        string="Audit Findings", help="Detailed audit findings and recommendations"
    )

    # === CUSTOMER SERVICE AND COMMUNICATION ===
    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        help="Primary customer contact for this report",
    )
    report_delivery_preference = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Report Delivery Preference",
        default="monthly",
        help="Customer preference for report delivery frequency",
    )
    customer_feedback_received = fields.Boolean(
        string="Customer Feedback Received",
        default=False,
        help="Whether customer has provided feedback on this report",
    )
    customer_satisfaction_score = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Customer Satisfaction Score",
        help="Customer satisfaction rating for this report",
    )

    # === ANALYTICS AND TRENDS ===
    inventory_growth_percentage = fields.Float(
        string="Inventory Growth %",
        digits=(5, 2),
        compute="_compute_growth_metrics",
        store=True,
        help="Percentage growth in inventory since last report",
    )
    document_activity_level = fields.Selection(
        [
            ("low", "Low Activity"),
            ("moderate", "Moderate Activity"),
            ("high", "High Activity"),
            ("very_high", "Very High Activity"),
        ],
        string="Document Activity Level",
        compute="_compute_activity_level",
        store=True,
        help="Level of document access activity",
    )
    predicted_next_period_cost = fields.Monetary(
        string="Predicted Next Period Cost",
        currency_field="currency_id",
        help="Predicted cost for next reporting period",
    )

    # === OPERATIONAL DETAILS ===
    report_generation_duration = fields.Float(
        string="Report Generation Duration (Hours)",
        digits=(5, 2),
        help="Time taken to generate this report",
    )
    data_sources_count = fields.Integer(
        string="Data Sources Count",
        default=1,
        help="Number of data sources used for this report",
    )
    report_complexity_score = fields.Float(
        string="Report Complexity Score",
        digits=(3, 1),
        compute="_compute_complexity_score",
        store=True,
        help="Complexity score based on data volume and processing requirements",
    )
    automated_generation = fields.Boolean(
        string="Automated Generation",
        default=False,
        help="Whether this report was generated automatically",
    )

    # Customer Inventory Report Fields
    active_locations = fields.Integer("Active Locations", default=0)
    container_ids = fields.Many2many("records.container", string="Containers")
    document_ids = fields.Many2many("records.document", string="Documents")
    document_type_id = fields.Many2one("records.document.type", "Document Type")
    location_id = fields.Many2one("records.location", "Location")
    archived_document_count = fields.Integer("Archived Document Count", default=0)
    compliance_status_summary = fields.Text("Compliance Status Summary")
    destruction_eligible_count = fields.Integer("Destruction Eligible Count", default=0)
    last_inventory_audit_date = fields.Date("Last Inventory Audit Date")
    pending_retrieval_count = fields.Integer("Pending Retrieval Count", default=0)
    retention_policy_violations = fields.Integer(
        "Retention Policy Violations", default=0
    )
    total_storage_cost = fields.Monetary(
        "Total Storage Cost", currency_field="currency_id"
    )
    # Customer Inventory Report Fields

    # === COMPUTE METHODS ===

    @api.depends("customer_id", "report_period_start", "report_period_end")
    def _compute_inventory_totals(self):
        """Compute total containers, documents, and storage space"""
        for report in self:
            if report.customer_id:
                # Get all containers for customer
                containers = self.env["records.container"].search(
                    [("customer_id", "=", report.customer_id.id)]
                )
                report.total_containers = len(containers)

                # Get all documents for customer
                documents = self.env["records.document"].search(
                    [("customer_id", "=", report.customer_id.id)]
                )
                report.total_documents = len(documents)

                # Calculate total storage space
                total_cubic_feet = sum(containers.mapped("cubic_feet_capacity") or [0])
                report.total_storage_cubic_feet = total_cubic_feet
            else:
                report.total_containers = 0
                report.total_documents = 0
                report.total_storage_cubic_feet = 0.0

    @api.depends("customer_id", "report_period_start")
    def _compute_document_metrics(self):
        """Compute document-related metrics"""
        for report in self:
            if report.customer_id and report.report_period_start:
                documents = self.env["records.document"].search(
                    [("customer_id", "=", report.customer_id.id)]
                )
                if documents:
                    # Calculate average document age
                    today = fields.Date.today()
                    total_age = 0
                    valid_docs = 0
                    for doc in documents:
                        if hasattr(doc, "creation_date") and doc.creation_date:
                            age = (today - doc.creation_date).days
                            total_age += age
                            valid_docs += 1

                    if valid_docs > 0:
                        report.average_document_age_days = total_age // valid_docs
                    else:
                        report.average_document_age_days = 0
                else:
                    report.average_document_age_days = 0
            else:
                report.average_document_age_days = 0

    @api.depends(
        "monthly_storage_cost", "retrieval_activity_cost", "destruction_activity_cost"
    )
    def _compute_total_costs(self):
        """Compute total costs for the reporting period"""
        for report in self:
            report.total_period_cost = (
                (report.monthly_storage_cost or 0)
                + (report.retrieval_activity_cost or 0)
                + (report.destruction_activity_cost or 0)
            )

    @api.depends("total_documents", "total_containers")
    def _compute_growth_metrics(self):
        """Compute inventory growth percentage"""
        for report in self:
            if report.customer_id:
                # Find previous report for same customer
                previous_report = self.search(
                    [
                        ("customer_id", "=", report.customer_id.id),
                        ("report_generation_date", "<", report.report_generation_date),
                        ("id", "!=", report.id),
                    ],
                    order="report_generation_date desc",
                    limit=1,
                )

                if previous_report and previous_report.total_documents > 0:
                    growth = (
                        (report.total_documents - previous_report.total_documents)
                        / previous_report.total_documents
                    ) * 100
                    report.inventory_growth_percentage = growth
                else:
                    report.inventory_growth_percentage = 0.0
            else:
                report.inventory_growth_percentage = 0.0

    @api.depends("retrieval_activity_cost", "total_documents")
    def _compute_activity_level(self):
        """Compute document activity level based on retrieval costs"""
        for report in self:
            if report.total_documents and report.retrieval_activity_cost:
                cost_per_doc = report.retrieval_activity_cost / report.total_documents
                if cost_per_doc <= 1.0:
                    report.document_activity_level = "low"
                elif cost_per_doc <= 5.0:
                    report.document_activity_level = "moderate"
                elif cost_per_doc <= 15.0:
                    report.document_activity_level = "high"
                else:
                    report.document_activity_level = "very_high"
            else:
                report.document_activity_level = "low"

    @api.depends("total_documents", "total_containers", "data_sources_count")
    def _compute_complexity_score(self):
        """Compute report complexity score"""
        for report in self:
            base_score = 1.0

            # Factor in document count
            if report.total_documents:
                if report.total_documents > 10000:
                    base_score += 3.0
                elif report.total_documents > 1000:
                    base_score += 2.0
                elif report.total_documents > 100:
                    base_score += 1.0

            # Factor in container count
            if report.total_containers:
                if report.total_containers > 1000:
                    base_score += 2.0
                elif report.total_containers > 100:
                    base_score += 1.0
                elif report.total_containers > 10:
                    base_score += 0.5

            # Factor in data sources
            if report.data_sources_count > 1:
                base_score += (report.data_sources_count - 1) * 0.5

            report.report_complexity_score = min(base_score, 10.0)  # Cap at 10.0

    # === ONCHANGE METHODS ===

    @api.onchange("report_period_start", "report_period_end")
    def _onchange_report_period(self):
        """Update report name when period changes"""
        if self.report_period_start and self.report_period_end and self.customer_id:
            period_str = f"{self.report_period_start} to {self.report_period_end}"
            self.name = f"Inventory Report - {self.customer_id.name} - {period_str}"

    @api.onchange("customer_id")
    def _onchange_customer_id(self):
        """Update fields when customer changes"""
        if self.customer_id:
            # Set customer contact
            contacts = self.customer_id.child_ids.filtered(
                lambda c: c.is_company == False
            )
            if contacts:
                self.customer_contact_id = contacts[0]
            else:
                self.customer_contact_id = self.customer_id

    @api.onchange("compliance_status")
    def _onchange_compliance_status(self):
        """Update related fields based on compliance status"""
        if self.compliance_status in ["major_issues", "non_compliant"]:
            self.customer_notification_sent = (
                False  # Require explicit notification for issues
            )

    # === VALIDATION METHODS ===

    @api.constrains("report_period_start", "report_period_end")
    def _check_report_period(self):
        """Validate report period dates"""
        for report in self:
            if report.report_period_start and report.report_period_end:
                if report.report_period_start > report.report_period_end:
                    raise ValidationError(
                        _("Report period start date cannot be after end date.")
                    )

                # Check for reasonable period length (not more than 1 year)
                period_days = (
                    report.report_period_end - report.report_period_start
                ).days
                if period_days > 365:
                    raise ValidationError(_("Report period cannot exceed 365 days."))

    @api.constrains("customer_satisfaction_score", "customer_feedback_received")
    def _check_satisfaction_score(self):
        """Ensure satisfaction score is only set when feedback is received"""
        for report in self:
            if (
                report.customer_satisfaction_score
                and not report.customer_feedback_received
            ):
                raise ValidationError(
                    _(
                        "Customer satisfaction score can only be set when feedback has been received."
                    )
                )

    def action_confirm_report(self):
        """Confirm inventory report for processing."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft reports can be confirmed."))

        # Update state and notes
        self.write(
            {
                "state": "confirmed",
                "notes": (self.notes or "")
                + _("\nReport confirmed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create confirmation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory report confirmed: %s") % self.name,
            note=_(
                "Customer inventory report has been confirmed and is ready for processing."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Inventory report confirmed: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Report Confirmed"),
                "message": _(
                    "Inventory report %s has been confirmed and is ready for processing."
                )
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_generate_pdf_report(self):
        """Generate PDF version of inventory report."""
        self.ensure_one()

        # Create PDF generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("PDF report generated: %s") % self.name,
            note=_(
                "PDF version of inventory report has been generated and is ready for distribution."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("PDF report generated: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.customer_inventory_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_send_to_customer(self):
        """Send inventory report to customer."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed reports can be sent to customers."))

        # Update state and notes
        self.write(
            {
                "state": "done",
                "notes": (self.notes or "")
                + _("\nSent to customer on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create send activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Report sent to customer: %s") % self.name,
            note=_("Inventory report has been successfully sent to the customer."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Inventory report sent to customer: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Send Report"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "customer.inventory.report",
                "default_res_id": self.id,
                "default_composition_mode": "comment",
                "default_subject": _("Inventory Report: %s") % self.name,
                "default_body": _("Please find attached your inventory report."),
            },
        }

    def action_view_boxes(self):
        """View all boxes included in this inventory report."""
        self.ensure_one()

        # Create activity to track box viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory boxes reviewed: %s") % self.name,
            note=_("All boxes included in this inventory report have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Boxes: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_location": True,
            },
        }

    def action_view_documents(self):
        """View all documents included in this inventory report."""
        self.ensure_one()

        # Create activity to track document viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory documents reviewed: %s") % self.name,
            note=_(
                "All documents included in this inventory report have been reviewed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Documents: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_type": True,
            },
        }

    def action_view_locations(self):
        """View all locations included in this inventory report."""
        self.ensure_one()

        # Create activity to track location viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Inventory locations reviewed: %s") % self.name,
            note=_(
                "All locations included in this inventory report have been reviewed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Locations: %s") % self.name,
            "res_model": "records.location",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_zone": True,
            },
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})

    # === ENHANCED ACTION METHODS ===

    def action_generate_analytics_summary(self):
        """Generate comprehensive analytics summary"""
        self.ensure_one()

        analytics_summary = f"""
        INVENTORY ANALYTICS SUMMARY
        ===========================
        Report: {self.name}
        Customer: {self.customer_id.name if self.customer_id else 'Not specified'}
        Period: {self.report_period_start} to {self.report_period_end}
        
        INVENTORY METRICS:
        - Total Containers: {self.total_containers:,}
        - Total Documents: {self.total_documents:,}
        - Storage Space: {self.total_storage_cubic_feet:.2f} cubic feet
        - Average Document Age: {self.average_document_age_days} days
        
        COST ANALYSIS:
        - Monthly Storage: ${self.monthly_storage_cost:.2f}
        - Retrieval Activities: ${self.retrieval_activity_cost:.2f}
        - Destruction Activities: ${self.destruction_activity_cost:.2f}
        - Total Period Cost: ${self.total_period_cost:.2f}
        
        TRENDS & ACTIVITY:
        - Inventory Growth: {self.inventory_growth_percentage:.1f}%
        - Activity Level: {self.document_activity_level.title()}
        - Complexity Score: {self.report_complexity_score:.1f}/10.0
        
        COMPLIANCE STATUS:
        - Overall Status: {self.compliance_status.title()}
        - Retention Violations: {self.retention_policy_violations}
        - Security Incidents: {self.security_incidents}
        """

        # Create attachment with analytics summary
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"analytics_summary_{self.name}.txt",
                "datas": analytics_summary.encode(),
                "res_model": self._name,
                "res_id": self.id,
            }
        )

        self.message_post(
            body=_("Analytics summary generated and attached."),
            subject=_("Analytics Summary"),
            attachment_ids=[attachment.id],
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Analytics Generated"),
                "message": _("Comprehensive analytics summary has been generated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_send_compliance_alert(self):
        """Send compliance alert if issues are found"""
        self.ensure_one()

        if self.compliance_status in ["minor_issues", "major_issues", "non_compliant"]:
            # Mark notification as sent
            self.customer_notification_sent = True

            # Create compliance alert message
            alert_message = f"""
            COMPLIANCE ALERT - {self.compliance_status.upper()}
            
            Report: {self.name}
            Customer: {self.customer_id.name}
            Status: {self.compliance_status.title()}
            
            Issues Found:
            - Retention Policy Violations: {self.retention_policy_violations}
            - Security Incidents: {self.security_incidents}
            
            Audit Findings:
            {self.audit_findings or 'No detailed findings recorded'}
            
            Please review and take appropriate action.
            """

            self.message_post(
                body=alert_message,
                subject=f"COMPLIANCE ALERT: {self.name}",
                message_type="email",
                partner_ids=(
                    [self.customer_contact_id.id] if self.customer_contact_id else []
                ),
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Compliance Alert Sent"),
                    "message": _("Compliance alert has been sent to customer."),
                    "type": "warning",
                    "sticky": True,
                },
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Issues Found"),
                    "message": _("Report is compliant - no alert needed."),
                    "type": "info",
                    "sticky": False,
                },
            }

    def action_schedule_next_report(self):
        """Schedule the next inventory report based on delivery preference"""
        self.ensure_one()

        # Calculate next report date based on preference
        next_date_mapping = {
            "immediate": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90,
        }

        days_to_add = next_date_mapping.get(self.report_delivery_preference, 30)
        next_report_date = fields.Date.add(fields.Date.today(), days=days_to_add)

        # Create next report record
        next_report = self.copy(
            {
                "name": f"Scheduled Report - {self.customer_id.name} - {next_report_date}",
                "state": "draft",
                "report_generation_date": False,
                "report_period_start": self.report_period_end or fields.Date.today(),
                "report_period_end": next_report_date,
                "customer_notification_sent": False,
                "customer_feedback_received": False,
            }
        )

        # Create activity for next report
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Generate Next Inventory Report: {next_report.name}",
            note=f"Scheduled inventory report for {self.customer_id.name}.\nDelivery preference: {self.report_delivery_preference}",
            date_deadline=next_report_date,
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Next Scheduled Report"),
            "res_model": "customer.inventory.report",
            "res_id": next_report.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_request_customer_feedback(self):
        """Request feedback from customer on this report"""
        self.ensure_one()

        if not self.customer_contact_id:
            raise UserError(
                _("Please set a customer contact before requesting feedback.")
            )

        # Create feedback request message
        feedback_message = f"""
        Dear {self.customer_contact_id.name},
        
        Your inventory report "{self.name}" has been completed and is ready for your review.
        
        Report Summary:
        - Total Documents: {self.total_documents:,}
        - Total Containers: {self.total_containers:,}
        - Period Cost: ${self.total_period_cost:.2f}
        
        We would appreciate your feedback on this report to help us improve our services.
        
        Please log into your customer portal to review the full report and provide feedback.
        
        Thank you for your business!
        """

        # Send message to customer
        self.message_post(
            body=feedback_message,
            subject=f"Inventory Report Ready for Review: {self.name}",
            message_type="email",
            partner_ids=[self.customer_contact_id.id],
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Feedback Requested"),
                "message": _("Feedback request has been sent to customer."),
                "type": "success",
                "sticky": False,
            },
        }
