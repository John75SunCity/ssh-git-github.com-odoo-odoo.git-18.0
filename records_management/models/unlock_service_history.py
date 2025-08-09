# -*- coding: utf-8 -*-
"""
Unlock Service History Management Module

This module provides comprehensive unlock service history management for the Records
Management System. It tracks unlock services, emergency procedures, key resets,
and maintenance operations with complete audit trails and billing integration.

Key Features:
- Complete unlock service lifecycle management
- Emergency unlock tracking with priority handling
- Key reset and maintenance service documentation
- Technician assignment and tracking
- Billing integration with cost tracking
- Location-based service management
- State workflow with approval processes

Business Processes:
1. Service Scheduling: Initial service request and scheduling
2. Service Execution: Real-time service tracking and documentation
3. Billing Management: Cost calculation and billing integration
4. Audit Compliance: Complete service history and audit trails
5. Customer Communication: Service notifications and updates
6. Performance Analytics: Service metrics and reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UnlockServiceHistory(models.Model):
    _name = "unlock.service.history"
    _description = "Unlock Service History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Service Reference",
        required=True,
        default="New",
        tracking=True,
        index=True,
        help="Unique service reference number",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of service record"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    technician_id = fields.Many2one(
        "res.users",
        string="Technician",
        default=lambda self: self.env.user,
        tracking=True,
        help="Technician performing the service",
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        tracking=True,
        help="Customer receiving the service",
    )

    # ============================================================================
    # SERVICE IDENTIFICATION
    # ============================================================================
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key",
        string="Partner Bin Key",
        required=True,
        tracking=True,
        help="Related partner bin key",
    )
    service_type = fields.Selection(
        [
            ("unlock", "Standard Unlock"),
            ("emergency_unlock", "Emergency Unlock"),
            ("key_reset", "Key Reset"),
            ("maintenance", "Maintenance Service"),
            ("repair", "Repair Service"),
            ("replacement", "Key Replacement"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
        help="Type of unlock service performed",
    )

    # ============================================================================
    # SERVICE TIMING AND LOCATION
    # ============================================================================
    date = fields.Datetime(
        string="Service Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time service was performed",
    )
    scheduled_date = fields.Datetime(
        string="Scheduled Date", help="Originally scheduled service date"
    )
    start_time = fields.Datetime(string="Start Time", help="Service start time")
    end_time = fields.Datetime(string="End Time", help="Service completion time")
    duration = fields.Float(
        string="Duration (minutes)",
        compute="_compute_duration",
        store=True,
        help="Service duration in minutes",
    )
    location_id = fields.Many2one(
        "records.location",
        string="Service Location",
        help="Physical location where service was performed",
    )

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    reason = fields.Text(
        string="Reason for Service", help="Detailed reason why service was required"
    )
    resolution = fields.Text(string="Resolution", help="How the service was resolved")
    notes = fields.Text(
        string="Service Notes", help="Additional notes about the service"
    )
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        tracking=True,
        help="Service priority level",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("failed", "Failed"),
        ],
        string="Service State",
        default="scheduled",
        tracking=True,
        help="Current service state",
    )

    # ============================================================================
    # BILLING AND COST MANAGEMENT
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    cost = fields.Monetary(
        string="Service Cost", currency_field="currency_id", help="Total service cost"
    )
    billable = fields.Boolean(
        string="Billable", default=True, help="Whether service is billable to customer"
    )
    invoice_id = fields.Many2one(
        "account.move", string="Invoice", help="Related invoice if billed"
    )
    billing_status = fields.Selection(
        [
            ("not_billed", "Not Billed"),
            ("billed", "Billed"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Billing Status",
        default="not_billed",
        tracking=True,
        help="Current billing status",
    )

    # ============================================================================
    # EQUIPMENT AND TOOLS
    # ============================================================================
    equipment_used_ids = fields.Many2many(
        "maintenance.equipment",
        string="Equipment Used",
        help="Equipment and tools used during service",
    )
    parts_used_ids = fields.One2many(
        "unlock.service.part",
        "service_history_id",
        string="Parts Used",
        help="Parts and materials used",
    )

    # ============================================================================
    # QUALITY AND VERIFICATION
    # ============================================================================
    quality_check = fields.Boolean(
        string="Quality Check Performed",
        default=False,
        help="Whether quality check was performed",
    )
    quality_rating = fields.Selection(
        [
            ("1", "Poor"),
            ("2", "Fair"),
            ("3", "Good"),
            ("4", "Very Good"),
            ("5", "Excellent"),
        ],
        string="Quality Rating",
        help="Service quality rating",
    )
    customer_signature = fields.Binary(
        string="Customer Signature", help="Customer signature for service completion"
    )
    verification_code = fields.Char(
        string="Verification Code", help="Service verification code"
    )

    # ============================================================================
    # FOLLOW-UP AND MAINTENANCE
    # ============================================================================
    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        default=False,
        help="Whether follow-up service is required",
    )
    follow_up_date = fields.Date(
        string="Follow-up Date", help="Scheduled follow-up date"
    )
    warranty_expiry = fields.Date(
        string="Warranty Expiry", help="Service warranty expiration date"
    )
    repeat_service = fields.Boolean(
        string="Repeat Service", default=False, help="Whether this is a repeat service"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Service display name",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "service_type", "customer_id")
    def _compute_display_name(self):
        """Compute display name for service"""
        for record in self:
            if record.name and record.service_type:
                service_type = dict(record._fields["service_type"].selection)[
                    record.service_type
                ]
                customer = record.customer_id.name if record.customer_id else "Unknown"
                record.display_name = f"{record.name} - {service_type} ({customer})"
            else:
                record.display_name = record.name or _("New Service")

    @api.depends("start_time", "end_time")
    def _compute_duration(self):
        """Compute service duration in minutes"""
        for record in self:
            if record.start_time and record.end_time:
                duration_seconds = (record.end_time - record.start_time).total_seconds()
                record.duration = duration_seconds / 60.0
            else:
                record.duration = 0.0

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence numbers"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("unlock.service.history")
                    or "USH-NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle state changes"""
        result = super().write(vals)

        # Handle state change notifications
        if "state" in vals:
            for record in self:
                if vals["state"] == "completed":
                    record._handle_service_completion()
                elif vals["state"] == "cancelled":
                    record._handle_service_cancellation()

        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_service(self):
        """Start the unlock service"""
        self.ensure_one()
        if self.state != "scheduled":
            raise UserError(_("Only scheduled services can be started"))

        self.write(
            {
                "state": "in_progress",
                "start_time": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Service started"))

    def action_complete_service(self):
        """Complete the unlock service"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress services can be completed"))

        self.write(
            {
                "state": "completed",
                "end_time": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Service completed successfully"))

        # Handle completion tasks
        self._handle_service_completion()

    def action_cancel_service(self):
        """Cancel the unlock service"""
        self.ensure_one()
        if self.state in ["completed", "cancelled"]:
            raise UserError(_("Completed or cancelled services cannot be cancelled"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Service cancelled"))

        # Handle cancellation tasks
        self._handle_service_cancellation()

    def action_reschedule_service(self):
        """Reschedule the service"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Service"),
            "res_model": "unlock.service.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_service_id": self.id},
        }

    def action_create_invoice(self):
        """Create invoice for billable service"""
        self.ensure_one()
        if not self.billable:
            raise UserError(_("Service is not billable"))

        if not self.customer_id:
            raise UserError(_("Customer is required for billing"))

        if self.invoice_id:
            raise UserError(_("Invoice already exists for this service"))

        # Create invoice
        invoice_vals = self._prepare_invoice_values()
        invoice = self.env["account.move"].create(invoice_vals)

        self.write(
            {
                "invoice_id": invoice.id,
                "billing_status": "billed",
            }
        )

        self.message_post(body=_("Invoice created: %s") % invoice.name)

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
        }

    def action_send_completion_notification(self):
        """Send service completion notification to customer"""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Only completed services can send notifications"))

        template = self.env.ref(
            "records_management.unlock_service_completion_email_template"
        )
        if template:
            template.send_mail(self.id, force_send=True)
            self.message_post(body=_("Completion notification sent to customer"))

    def action_schedule_follow_up(self):
        """Schedule follow-up service"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Follow-up"),
            "res_model": "unlock.service.history",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_bin_key_id": self.partner_bin_key_id.id,
                "default_customer_id": self.customer_id.id,
                "default_location_id": self.location_id.id,
                "default_service_type": "maintenance",
                "default_reason": f"Follow-up service for {self.name}",
            },
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _handle_service_completion(self):
        """Handle tasks when service is completed"""
        self.ensure_one()

        # Update partner bin key status
        if self.partner_bin_key_id:
            self.partner_bin_key_id.write(
                {
                    "last_service_date": self.date,
                    "service_count": self.partner_bin_key_id.service_count + 1,
                }
            )

        # Create follow-up activity if required
        if self.follow_up_required and self.follow_up_date:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=self.follow_up_date,
                summary=f"Follow-up service for {self.name}",
                note="Scheduled follow-up service based on completion requirements.",
                user_id=self.technician_id.id,
            )

        # Auto-create invoice for billable services
        if self.billable and not self.invoice_id and self.customer_id:
            try:
                self.action_create_invoice()
            except Exception as e:
                self.message_post(body=_("Auto-billing failed: %s") % str(e))

    def _handle_service_cancellation(self):
        """Handle tasks when service is cancelled"""
        self.ensure_one()

        # Cancel related activities
        activities = self.activity_ids.filtered(lambda a: a.res_model == self._name)
        activities.action_done()

        # Update billing status
        if self.billing_status == "billed" and not self.invoice_id:
            self.write({"billing_status": "cancelled"})

    def _prepare_invoice_values(self):
        """Prepare values for invoice creation"""
        self.ensure_one()

        product = self.env["product.product"].search(
            [("default_code", "=", "UNLOCK_SERVICE")], limit=1
        )

        if not product:
            # Create default service product
            product = self.env["product.product"].create(
                {
                    "name": "Unlock Service",
                    "default_code": "UNLOCK_SERVICE",
                    "type": "service",
                    "list_price": 50.0,
                    "invoice_policy": "order",
                }
            )

        invoice_line_vals = {
            "product_id": product.id,
            "name": f"Unlock Service - {self.name}",
            "quantity": 1,
            "price_unit": self.cost or product.list_price,
        }

        return {
            "partner_id": self.customer_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [(0, 0, invoice_line_vals)],
        }

    def get_service_summary(self):
        """Get service summary for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "service_type": self.service_type,
            "customer": self.customer_id.name if self.customer_id else None,
            "technician": self.technician_id.name,
            "date": self.date,
            "duration": self.duration,
            "cost": self.cost,
            "state": self.state,
            "billing_status": self.billing_status,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_time", "end_time")
    def _check_service_times(self):
        """Validate service times"""
        for record in self:
            if record.start_time and record.end_time:
                if record.end_time <= record.start_time:
                    raise ValidationError(_("End time must be after start time"))

    @api.constrains("cost")
    def _check_cost(self):
        """Validate service cost"""
        for record in self:
            if record.cost < 0:
                raise ValidationError(_("Service cost cannot be negative"))

    @api.constrains("follow_up_date")
    def _check_follow_up_date(self):
        """Validate follow-up date"""
        for record in self:
            if record.follow_up_required and record.follow_up_date:
                if record.follow_up_date <= fields.Date.today():
                    raise ValidationError(_("Follow-up date must be in the future"))


class UnlockServicePart(models.Model):
    """Parts and materials used in unlock services"""

    _name = "unlock.service.part"
    _description = "Unlock Service Part"
    _rec_name = "product_id"

    service_history_id = fields.Many2one(
        "unlock.service.history",
        string="Service",
        required=True,
        ondelete="cascade",
        help="Related service history",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        help="Product used in service",
    )
    quantity = fields.Float(
        string="Quantity", default=1.0, required=True, help="Quantity used"
    )
    unit_price = fields.Float(string="Unit Price", help="Unit price of the part")
    total_price = fields.Float(
        string="Total Price",
        compute="_compute_total_price",
        store=True,
        help="Total price (quantity * unit price)",
    )
    notes = fields.Text(string="Notes", help="Additional notes about part usage")

    @api.depends("quantity", "unit_price")
    def _compute_total_price(self):
        """Compute total price"""
        for record in self:
            record.total_price = record.quantity * record.unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Set unit price when product changes"""
        if self.product_id:
            self.unit_price = self.product_id.list_price


class UnlockServiceRescheduleWizard(models.TransientModel):
    """Wizard for rescheduling unlock services"""

    _name = "unlock.service.reschedule.wizard"
    _description = "Unlock Service Reschedule Wizard"

    service_id = fields.Many2one(
        "unlock.service.history",
        string="Service",
        required=True,
        help="Service to reschedule",
    )
    new_date = fields.Datetime(
        string="New Service Date",
        required=True,
        default=fields.Datetime.now,
        help="New scheduled date and time",
    )
    reason = fields.Text(
        string="Reschedule Reason", required=True, help="Reason for rescheduling"
    )
    notify_customer = fields.Boolean(
        string="Notify Customer", default=True, help="Send notification to customer"
    )

    def action_reschedule(self):
        """Execute the reschedule"""
        self.ensure_one()

        # Update service record
        self.service_id.write(
            {
                "scheduled_date": self.new_date,
                "date": self.new_date,
            }
        )

        # Post message with reason
        self.service_id.message_post(
            body=_("Service rescheduled to %s. Reason: %s")
            % (self.new_date.strftime("%Y-%m-%d %H:%M"), self.reason)
        )

        # Send customer notification if requested
        if self.notify_customer and self.service_id.customer_id:
            template = self.env.ref(
                "records_management.unlock_service_reschedule_email_template"
            )
            if template:
                template.send_mail(self.service_id.id, force_send=True)

        return {"type": "ir.actions.act_window_close"}

    @api.constrains("new_date")
    def _check_new_date(self):
        """Validate new service date"""
        for record in self:
            if record.new_date <= fields.Datetime.now():
                raise ValidationError(_("New service date must be in the future"))
