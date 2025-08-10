# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class BinUnlockService(models.Model):
    _name = "bin.unlock.service"
    _description = "Bin Unlock Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="Assigned User", default=lambda self: self.env.user)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"), ("active", "Active"),
        ("inactive", "Inactive"), ("archived", "Archived")
    ], string="Status", default="draft", tracking=True

    # ============================================================================
    # SERVICE REQUEST DETAILS
    # ============================================================================
    service_type = fields.Selection([
        ("emergency", "Emergency Unlock"), ("scheduled", "Scheduled Unlock"),
        ("bulk", "Bulk Unlock"), ("maintenance", "Maintenance Unlock")
    ], string="Service Type", required=True, default="scheduled"

    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now, tracking=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", tracking=True)
    completion_date = fields.Datetime(string="Completion Date", tracking=True)

    priority = fields.Selection([
        ("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")
    ], string="Priority", default="normal", tracking=True

    # ============================================================================
    # BIN & KEY INFORMATION
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    bin_id = fields.Many2one(
        "shred.bin", string="Shred Bin", required=True, tracking=True
    
    key_id = fields.Many2one("bin.key", string="Key", tracking=True)

    bin_location = fields.Char(string="Bin Location")
    key_serial_number = fields.Char(string="Key Serial Number")
    unlock_method = fields.Selection([
        ("physical_key", "Physical Key"), ("electronic", "Electronic"),
        ("master_key", "Master Key"), ("emergency_override", "Emergency Override")
    ], string="Unlock Method", default="physical_key"

    # ============================================================================
    # TECHNICIAN & SCHEDULING
    # ============================================================================
    assigned_technician_id = fields.Many2one("res.users", string="Assigned Technician", tracking=True)
    backup_technician_id = fields.Many2one("res.users", string="Backup Technician")
    estimated_duration = fields.Float(string="Estimated Duration (hours)", default=0.5)
    actual_duration = fields.Float(string="Actual Duration (hours)")

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    reason_for_unlock = fields.Text(string="Reason for Unlock", required=True)
    special_instructions = fields.Text(string="Special Instructions")
    security_notes = fields.Text(string="Security Notes")

    requires_escort = fields.Boolean(string="Requires Escort", default=False)
    witness_required = fields.Boolean(string="Witness Required", default=False)
    witness_name = fields.Char(string="Witness Name")

    # ============================================================================
    # COMPLIANCE & DOCUMENTATION
    # ============================================================================
    authorization_code = fields.Char(string="Authorization Code")
    service_report = fields.Text(string="Service Report")
    completion_notes = fields.Text(string="Completion Notes")

    photo_before = fields.Binary(string="Photo Before")
    photo_after = fields.Binary(string="Photo After")
    service_certificate = fields.Binary(string="Service Certificate")

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    currency_id = fields.Many2one("res.currency", string="Currency", 
                                 default=lambda self: self.env.company.currency_id
    service_cost = fields.Monetary(string="Service Cost", currency_field="currency_id")
    emergency_surcharge = fields.Monetary(string="Emergency Surcharge", currency_field="currency_id")
    total_cost = fields.Monetary(string="Total Cost", currency_field="currency_id", 
                                compute="_compute_total_cost", store=True

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    related_requests = fields.Many2many("portal.request", string="Related Portal Requests")

    # Mail framework fields    @api.depends("service_cost", "emergency_surcharge")
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.service_cost + record.emergency_surcharge

    @api.depends("name", "bin_id", "partner_id")
    def _compute_display_name(self):
        for record in self:
            if record.bin_id and record.partner_id:
                record.display_name = _("%s - %s - %s", "Unknown")
            else:
                pass
            pass
                record.display_name = record.name or "New"

    display_name = fields.Char(compute="_compute_display_name", string="Display Name", store=True)

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("bin.unlock.service") or "BUS/"
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_schedule(self):
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError(_("Please set a scheduled date first."))
        self.write({"state": "active"})

    def action_start_service(self):
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active services can be started."))
        self.write({"state": "active"})

    def action_complete(self):
        self.ensure_one()
        if not self.completion_notes:
            raise UserError(_("Please add completion notes before completing the service."))
        self.write({
            "state": "active",
            "completion_date": fields.Datetime.now()
        }

    def action_cancel(self):
        self.ensure_one()
        self.write({"state": "inactive"})

    def action_generate_certificate(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Generate Service Certificate",
            "res_model": "service.certificate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_service_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_service_summary(self):
        """Return formatted service summary"""
        self.ensure_one()
        return {
            "service_name": self.name,
            "customer": self.partner_id.name,
            "bin": self.bin_id.name if self.bin_id else "N/A",
            "status": self.state,
            "scheduled": self.scheduled_date.strftime("%Y-%m-%d %H:%M") if self.scheduled_date else "Not scheduled",
            "cost": self.total_cost,
        }

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (from comprehensive validation)
    # ============================================================================
    def action_create_invoice(self):
        """Create Invoice - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "bin.unlock.service",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_mark_completed(self):
        """Mark Completed - State management action"""
        self.ensure_one()
        # TODO: Implement action_mark_completed business logic
        self.message_post(body=_("Mark Completed action executed"))
        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("scheduled_date", "request_date")
    def _check_dates(self):
        for record in self:
            if record.scheduled_date and record.request_date and record.scheduled_date < record.request_date:
                raise ValidationError(_("Scheduled date cannot be before request date."))

    @api.constrains("estimated_duration", "actual_duration")
    def _check_duration(self):
        for record in self:
            if record.estimated_duration < 0 or record.actual_duration < 0:
                raise ValidationError(_("Duration cannot be negative."))

    @api.constrains("service_cost", "emergency_surcharge")
    def _check_costs(self):
        for record in self:
            if record.service_cost < 0 or record.emergency_surcharge < 0:
                raise ValidationError(_("Costs cannot be negative."))

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    customer_key_restricted = fields.Char(string='Customer Key Restricted', tracking=True)
    unlock_reason_code = fields.Char(string='Unlock Reason Code', tracking=True)
    service_start_time = fields.Datetime(string='Service Start Time')
    service_rate = fields.Float(string='Service Rate', default=25.0)
    invoice_id = fields.Many2one('account.move', string='Invoice')
