# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BinUnlockService(models.Model):
    _name = "bin.unlock.service"
    _description = "Bin Unlock Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

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
    created_date = fields.Date(string="Date", default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string="Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    service_date = fields.Date(string="Service Date")
    technician_id = fields.Many2one("hr.employee", string="Technician")
    billable = fields.Boolean(string="Billable", default=True)
    charge_amount = fields.Monetary(
        string="Charge Amount", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    completed = fields.Boolean(string="Completed", default=False)

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("estimated_cost", "actual_cost")
    def _compute_cost_variance(self):
        """Compute cost variance between estimated and actual cost"""
        for record in self:
            if record.estimated_cost and record.actual_cost:
                record.cost_variance = record.actual_cost - record.estimated_cost
            else:
                record.cost_variance = 0.0

    # === ONCHANGE METHODS ===
    @api.onchange("emergency_access_required")
    def _onchange_emergency_access_required(self):
        """Update priority when emergency access is required"""
        if self.emergency_access_required:
            self.priority_level = "emergency"
            self.witness_required = True
            self.incident_report_required = True

    @api.onchange("unlock_method_used")
    def _onchange_unlock_method_used(self):
        """Update fields based on unlock method"""
        if self.unlock_method_used == "drill_out":
            self.replacement_lock_required = True
            self.damage_assessment = "Lock destroyed during drill-out process"
        elif self.unlock_method_used == "locksmith":
            self.specialized_equipment_required = True

    @api.onchange("priority_level")
    def _onchange_priority_level(self):
        """Update service parameters based on priority level"""
        if self.priority_level == "emergency":
            self.witness_required = True
            self.regulatory_notification_sent = False  # Will be required
        elif self.priority_level == "high":
            self.follow_up_required = True

    # === VALIDATION METHODS ===
    @api.constrains("unlock_duration_minutes")
    def _check_unlock_duration(self):
        """Validate unlock duration is reasonable"""
        for record in self:
            if record.unlock_duration_minutes and (
                record.unlock_duration_minutes < 0
                or record.unlock_duration_minutes > 480
            ):  # 8 hours max
                raise ValidationError(
                    _("Unlock duration must be between 0 and 480 minutes (8 hours).")
                )

    @api.constrains("service_warranty_period")
    def _check_warranty_period(self):
        """Validate warranty period"""
        for record in self:
            if record.service_warranty_period and (
                record.service_warranty_period < 0
                or record.service_warranty_period > 365
            ):
                raise ValidationError(
                    _("Service warranty period must be between 0 and 365 days.")
                )

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

        # Auto-complete service when marked as completed
        if vals.get("completed") and not self.completed:
            vals["service_completion_notes"] = (
                vals.get("service_completion_notes", "")
                + f"\nService completed on {fields.Datetime.now()}"
            )
            if not vals.get("actual_cost"):
                vals["actual_cost"] = vals.get("charge_amount", self.charge_amount)

        return super().write(vals)

    # Bin Unlock Service Fields
    bin_location = fields.Char("Bin Location")
    customer_key_restricted = fields.Boolean("Customer Key Restricted", default=False)
    invoice_created = fields.Boolean("Invoice Created", default=False)
    items_retrieved = fields.Boolean("Items Retrieved", default=False)
    key_holder_id = fields.Many2one("res.partner", "Key Holder")
    access_authorization_verified = fields.Boolean(
        "Access Authorization Verified", default=False
    )
    backup_access_method = fields.Selection(
        [
            ("master_key", "Master Key"),
            ("code_override", "Code Override"),
            ("physical_break", "Physical Break"),
        ],
        default="master_key",
    )
    emergency_access_required = fields.Boolean(
        "Emergency Access Required", default=False
    )
    lock_mechanism_type = fields.Selection(
        [
            ("mechanical", "Mechanical"),
            ("electronic", "Electronic"),
            ("biometric", "Biometric"),
        ],
        default="mechanical",
    )
    security_log_generated = fields.Boolean("Security Log Generated", default=True)
    time_limit_exceeded = fields.Boolean("Time Limit Exceeded", default=False)
    unlock_authorization_code = fields.Char("Unlock Authorization Code")
    witness_required = fields.Boolean("Witness Required", default=False)

    # === MISSING CRITICAL BUSINESS FIELDS ===
    unlock_request_id = fields.Many2one(
        "bin.unlock.request",
        string="Unlock Request",
        help="Related unlock request record",
    )
    unlock_method_used = fields.Selection(
        [
            ("customer_key", "Customer Key"),
            ("master_key", "Master Key"),
            ("override_code", "Override Code"),
            ("drill_out", "Drill Out"),
            ("locksmith", "Professional Locksmith"),
        ],
        string="Unlock Method Used",
        help="Method actually used to unlock the bin",
    )

    unlock_duration_minutes = fields.Integer(
        string="Unlock Duration (Minutes)",
        help="Time taken to complete the unlock service",
    )
    witness_signature = fields.Binary(
        string="Witness Signature", help="Digital signature of required witness"
    )
    service_completion_notes = fields.Text(
        string="Service Completion Notes",
        help="Detailed notes about the service completion",
    )
    damage_assessment = fields.Text(
        string="Damage Assessment",
        help="Assessment of any damage during unlock process",
    )
    replacement_lock_required = fields.Boolean(
        string="Replacement Lock Required",
        default=False,
        help="Whether a replacement lock is needed",
    )
    additional_security_measures = fields.Text(
        string="Additional Security Measures",
        help="Any additional security measures taken during service",
    )

    # === ENHANCED WORKFLOW FIELDS ===
    priority_level = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("emergency", "Emergency"),
        ],
        string="Priority Level",
        default="normal",
        help="Priority level of the unlock service",
    )

    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost before service",
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost after service completion",
    )
    cost_variance = fields.Monetary(
        string="Cost Variance",
        compute="_compute_cost_variance",
        currency_field="currency_id",
        help="Difference between estimated and actual cost",
    )

    # === COMPLIANCE AND AUDIT FIELDS ===
    compliance_check_passed = fields.Boolean(
        string="Compliance Check Passed",
        default=False,
        help="Whether all compliance checks passed",
    )
    audit_trail = fields.Text(
        string="Audit Trail", help="Detailed audit trail of the unlock process"
    )
    regulatory_notification_sent = fields.Boolean(
        string="Regulatory Notification Sent",
        default=False,
        help="Whether regulatory authorities were notified if required",
    )
    incident_report_required = fields.Boolean(
        string="Incident Report Required",
        default=False,
        help="Whether an incident report is required",
    )

    # === CUSTOMER SERVICE FIELDS ===
    customer_satisfaction_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Customer Satisfaction Rating",
        help="Customer satisfaction rating for the service",
    )

    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        default=False,
        help="Whether follow-up service is required",
    )
    follow_up_date = fields.Date(
        string="Follow-up Date", help="Date for follow-up service"
    )
    service_warranty_period = fields.Integer(
        string="Service Warranty Period (Days)",
        default=30,
        help="Warranty period for the unlock service",
    )

    # === TECHNICAL DETAILS ===
    lock_serial_number = fields.Char(
        string="Lock Serial Number", help="Serial number of the lock that was opened"
    )
    lock_manufacturer = fields.Char(
        string="Lock Manufacturer", help="Manufacturer of the lock"
    )
    tools_used = fields.Text(
        string="Tools Used", help="List of tools used during the unlock process"
    )
    specialized_equipment_required = fields.Boolean(
        string="Specialized Equipment Required",
        default=False,
        help="Whether specialized equipment was needed",
    )

    # Bin Unlock Service Fields

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # === ENHANCED ACTION METHODS ===

    def action_start_service(self):
        """Start the unlock service"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Service must be in active state to start."))

        # Record service start
        self.message_post(
            body=_("Unlock service started by %s") % self.env.user.name,
            subject=_("Service Started"),
        )

        # Create audit trail entry
        audit_entry = (
            f"Service started on {fields.Datetime.now()} by {self.env.user.name}\n"
        )
        audit_entry += f"Method: {self.unlock_method_used or 'Not specified'}\n"
        audit_entry += f"Priority: {self.priority_level}"

        self.audit_trail = (self.audit_trail or "") + audit_entry + "\n"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Service Started"),
                "message": _("Unlock service has been started."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_complete_service(self):
        """Complete the unlock service"""
        self.ensure_one()

        # Validation checks before completion
        if not self.unlock_method_used:
            raise UserError(
                _(
                    "Please specify the unlock method used before completing the service."
                )
            )

        if self.witness_required and not self.witness_signature:
            raise UserError(
                _("Witness signature is required before completing this service.")
            )

        # Mark as completed
        self.write(
            {
                "completed": True,
                "state": "completed",
                "actual_cost": self.actual_cost or self.charge_amount,
            }
        )

        # Generate completion notification
        self.message_post(
            body=_(
                "Service completed successfully.\nMethod used: %s\nDuration: %s minutes"
            )
            % (self.unlock_method_used, self.unlock_duration_minutes or "Not recorded"),
            subject=_("Service Completed"),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Service Completed"),
                "message": _("Unlock service has been completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_schedule_followup(self):
        """Schedule follow-up service"""
        self.ensure_one()

        if not self.follow_up_required:
            self.follow_up_required = True

        if not self.follow_up_date:
            self.follow_up_date = fields.Date.add(fields.Date.today(), days=7)

        # Create follow-up activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Follow-up for Unlock Service: {self.name}",
            note=f"Follow-up required for unlock service.\nOriginal service date: {self.service_date}\nMethod used: {self.unlock_method_used}",
            date_deadline=self.follow_up_date,
            user_id=(
                self.technician_id.user_id.id
                if self.technician_id.user_id
                else self.env.user.id
            ),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Follow-up Scheduled"),
                "message": _("Follow-up service has been scheduled for %s.")
                % self.follow_up_date,
                "type": "info",
                "sticky": False,
            },
        }

    def action_generate_incident_report(self):
        """Generate incident report for emergency or problematic unlocks"""
        self.ensure_one()

        # Mark incident report as required
        self.incident_report_required = True

        # Create incident report content
        incident_details = f"""
        INCIDENT REPORT - BIN UNLOCK SERVICE
        ====================================
        Service ID: {self.name}
        Date: {self.service_date or fields.Date.today()}
        Customer: {self.customer_id.name if self.customer_id else 'Not specified'}
        Bin Location: {self.bin_location or 'Not specified'}
        
        SERVICE DETAILS:
        - Priority Level: {self.priority_level}
        - Unlock Method: {self.unlock_method_used or 'Not specified'}
        - Duration: {self.unlock_duration_minutes or 0} minutes
        - Emergency Access: {'Yes' if self.emergency_access_required else 'No'}
        - Witness Required: {'Yes' if self.witness_required else 'No'}
        
        DAMAGE ASSESSMENT:
        {self.damage_assessment or 'No damage reported'}
        
        ADDITIONAL NOTES:
        {self.service_completion_notes or 'No additional notes'}
        """

        # Create attachment with incident report
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"incident_report_{self.name}.txt",
                "datas": incident_details.encode(),
                "res_model": self._name,
                "res_id": self.id,
            }
        )

        self.message_post(
            body=_("Incident report generated and attached."),
            subject=_("Incident Report"),
            attachment_ids=[attachment.id],
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Incident Report Generated"),
                "message": _(
                    "Incident report has been generated and attached to this record."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
