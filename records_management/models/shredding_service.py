# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ShreddingService(models.Model):
    _name = "shredding.service"
    _description = "Shredding Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, service_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Service Order #", required=True, tracking=True, index=True)
    reference = fields.Char(string="Reference", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Service Technician",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("invoiced", "Invoiced"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & SERVICE DETAILS
    # ============================================================================

    # Customer Information
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    customer_name = fields.Char(string="Customer Name", related="partner_id.name", store=True)
    contact_person = fields.Many2one("res.partner", string="Contact Person")
    site_address = fields.Text(string="Service Site Address")

    # Service Classification
    service_type = fields.Selection(
        [
            ("onsite", "On-Site Shredding"),
            ("offsite", "Off-Site Shredding"),
            ("hard_drive", "Hard Drive Destruction"),
            ("mobile", "Mobile Shredding"),
            ("bulk", "Bulk Destruction"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="medium",
        tracking=True,
    )

    # Security & Compliance
    security_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("confidential", "Confidential"),
            ("secret", "Secret"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="standard",
        tracking=True,
    )

    naid_compliance_required = fields.Boolean(string="NAID Compliance Required", default=True)
    chain_of_custody_required = fields.Boolean(string="Chain of Custody Required", default=True)

    # ============================================================================
    # SCHEDULING & TIMING
    # ============================================================================

    # Service Scheduling
    service_date = fields.Datetime(string="Service Date", required=True, tracking=True)
    estimated_start_time = fields.Datetime(string="Estimated Start Time")
    actual_start_time = fields.Datetime(string="Actual Start Time")
    estimated_completion_time = fields.Datetime(string="Estimated Completion Time")
    actual_completion_time = fields.Datetime(string="Actual Completion Time")

    # Duration Tracking
    estimated_duration = fields.Float(string="Estimated Duration (Hours)", digits=(5, 2))
    actual_duration = fields.Float(
        string="Actual Duration (Hours)",
        digits=(5, 2),
        compute="_compute_actual_duration",
        store=True,
    )

    # ============================================================================
    # MATERIAL & INVENTORY
    # ============================================================================

    # Material Information
    total_weight = fields.Float(string="Total Weight (lbs)", digits=(10, 2), tracking=True)
    total_volume = fields.Float(string="Total Volume (cubic ft)", digits=(8, 2))
    container_count = fields.Integer(string="Container Count", default=0)
    
    # Material Types
    material_types = fields.Selection(
        [
            ("paper", "Paper Documents"),
            ("hard_drives", "Hard Drives"),
            ("optical_media", "Optical Media"),
            ("mixed", "Mixed Materials"),
            ("confidential", "Confidential Documents"),
        ],
        string="Material Types",
        default="paper",
    )

    # Inventory Items
    shredding_items_ids = fields.One2many(
        "shredding.inventory.item",
        "service_id",
        string="Items to Shred",
    )

    item_count = fields.Integer(
        string="Item Count",
        compute="_compute_item_metrics",
        store=True,
    )

    # ============================================================================
    # CERTIFICATES & DOCUMENTATION
    # ============================================================================

    # Certificates
    destruction_certificate_id = fields.Many2one(
        "destruction.certificate",
        string="Destruction Certificate",
    )
    certificate_number = fields.Char(string="Certificate Number", tracking=True)
    certificate_issued = fields.Boolean(string="Certificate Issued", default=False)
    certificate_date = fields.Date(string="Certificate Date")

    # Documentation
    pre_service_photos = fields.Boolean(string="Pre-Service Photos Taken", default=False)
    post_service_photos = fields.Boolean(string="Post-Service Photos Taken", default=False)
    witness_required = fields.Boolean(string="Customer Witness Required", default=False)
    witness_present = fields.Boolean(string="Customer Witness Present", default=False)
    witness_name = fields.Char(string="Witness Name")

    # Service Notes
    service_notes = fields.Text(string="Service Notes")
    technician_notes = fields.Text(string="Technician Notes")
    quality_notes = fields.Text(string="Quality Control Notes")
    customer_feedback = fields.Text(string="Customer Feedback")

    # ============================================================================
    # EQUIPMENT & RESOURCES
    # ============================================================================

    # Equipment
    shredder_type = fields.Selection(
        [
            ("strip_cut", "Strip Cut"),
            ("cross_cut", "Cross Cut"),
            ("micro_cut", "Micro Cut"),
            ("industrial", "Industrial Shredder"),
        ],
        string="Shredder Type",
        default="cross_cut",
    )

    equipment_serial = fields.Char(string="Equipment Serial Number")
    vehicle_id = fields.Many2one("records.vehicle", string="Service Vehicle")
    
    # Team Assignment
    technician_team_ids = fields.Many2many(
        "res.users",
        "shredding_service_team_rel",
        "service_id",
        "user_id",
        string="Service Team",
    )

    supervisor_id = fields.Many2one("res.users", string="Service Supervisor")

    # ============================================================================
    # COSTS & BILLING
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Pricing
    unit_price = fields.Monetary(string="Unit Price", currency_field="currency_id")
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    
    # Additional Costs
    travel_cost = fields.Monetary(string="Travel Cost", currency_field="currency_id")
    equipment_cost = fields.Monetary(string="Equipment Cost", currency_field="currency_id")
    disposal_cost = fields.Monetary(string="Disposal Cost", currency_field="currency_id")

    # Billing Status
    invoiced = fields.Boolean(string="Invoiced", default=False)
    invoice_id = fields.Many2one("account.move", string="Invoice")
    
    # Missing fields from gap analysis
    serial_number = fields.Char(string="Service Serial Number", tracking=True)

    # ============================================================================
    # COMPLIANCE & AUDIT
    # ============================================================================

    # Chain of Custody
    custody_log_ids = fields.One2many(
        "records.chain.of.custody",
        "service_id",
        string="Chain of Custody Log",
    )

    # Audit Trail
    audit_trail_ids = fields.One2many(
        "naid.audit.log",
        "service_id",
        string="Audit Trail",
    )

    # Compliance Verification
    naid_verification_completed = fields.Boolean(string="NAID Verification Completed")
    compliance_officer = fields.Many2one("res.users", string="Compliance Officer")
    verification_date = fields.Date(string="Verification Date")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    portal_request_id = fields.Many2one("portal.request", string="Portal Request")
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")
    pickup_request_id = fields.Many2one("pickup.request", string="Pickup Request")

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("actual_start_time", "actual_completion_time")
    def _compute_actual_duration(self):
        """Compute actual service duration"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                delta = record.actual_completion_time - record.actual_start_time
                record.actual_duration = delta.total_seconds() / 3600
            else:
                record.actual_duration = 0.0

    @api.depends("shredding_items_ids")
    def _compute_item_metrics(self):
        """Compute item count and metrics"""
        for record in self:
            record.item_count = len(record.shredding_items_ids)

    @api.depends("unit_price", "total_weight", "travel_cost", "equipment_cost", "disposal_cost")
    def _compute_total_amount(self):
        """Compute total service amount"""
        for record in self:
            base_amount = (record.unit_price or 0.0) * (record.total_weight or 0.0)
            additional_costs = (
                (record.travel_cost or 0.0) +
                (record.equipment_cost or 0.0) +
                (record.disposal_cost or 0.0)
            )
            record.total_amount = base_amount + additional_costs

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_schedule_service(self):
        """Schedule the shredding service"""
        self.ensure_one()
        if not self.service_date:
            raise UserError(_("Please set a service date before scheduling."))
        
        self.write({"state": "scheduled"})
        
        # Create calendar event
        self._create_service_calendar_event()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Service Scheduled"),
                "message": _("Shredding service has been scheduled successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_start_service(self):
        """Start the shredding service"""
        self.ensure_one()
        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now(),
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Service Started"),
                "message": _("Shredding service has been started."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_complete_service(self):
        """Complete the shredding service"""
        self.ensure_one()
        if not self.service_notes:
            raise UserError(_("Please enter service notes before completing."))
        
        self.write({
            "state": "completed",
            "actual_completion_time": fields.Datetime.now(),
        })
        
        # Generate destruction certificate
        self._generate_destruction_certificate()
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Service Completed"),
                "message": _("Shredding service has been completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Certificate"),
            "res_model": "destruction.certificate",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_service_date": self.service_date,
                "default_total_weight": self.total_weight,
            },
        }

    def action_create_invoice(self):
        """Create invoice for shredding service"""
        self.ensure_one()
        if self.invoiced:
            raise UserError(_("Service has already been invoiced."))
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_move_type": "out_invoice",
                "default_ref": self.name,
                "default_amount_total": self.total_amount,
            },
        }

    def action_view_items(self):
        """View shredding items"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Shredding Items"),
            "res_model": "shredding.inventory.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("service_id", "=", self.id)],
        }

    def action_view_chain_of_custody(self):
        """View chain of custody logs"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "records.chain.of.custody",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("service_id", "=", self.id)],
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    def _create_service_calendar_event(self):
        """Create calendar event for scheduled service"""
        for record in self:
            if record.service_date and record.user_id:
                duration = record.estimated_duration or 4  # Default 4 hours
                self.env["calendar.event"].create({
                    "name": f"Shredding Service: {record.name}",
                    "description": f"Shredding service for {record.partner_id.name}",
                    "start": record.service_date,
                    "stop": record.service_date + timedelta(hours=duration),
                    "user_id": record.user_id.id,
                    "partner_ids": [(6, 0, [record.partner_id.id])],
                })

    def _generate_destruction_certificate(self):
        """Generate destruction certificate automatically"""
        for record in self:
            if not record.destruction_certificate_id:
                certificate = self.env["destruction.certificate"].create({
                    "name": f"Certificate - {record.name}",
                    "service_id": record.id,
                    "partner_id": record.partner_id.id,
                    "destruction_date": record.service_date,
                    "total_weight": record.total_weight,
                    "destruction_method": f"{record.service_type} - {record.shredder_type}",
                })
                record.destruction_certificate_id = certificate.id
                record.certificate_issued = True
                record.certificate_date = fields.Date.today()

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("service_date", "estimated_start_time", "estimated_completion_time")
    def _check_time_sequence(self):
        """Ensure times are in logical sequence"""
        for record in self:
            if record.estimated_start_time and record.estimated_completion_time:
                if record.estimated_completion_time <= record.estimated_start_time:
                    raise ValidationError(_("Completion time must be after start time."))

    @api.constrains("total_weight", "total_volume")
    def _check_positive_values(self):
        """Ensure weights and volumes are positive"""
        for record in self:
            if record.total_weight and record.total_weight < 0:
                raise ValidationError(_("Total weight must be positive."))
            if record.total_volume and record.total_volume < 0:
                raise ValidationError(_("Total volume must be positive."))

    @api.constrains("unit_price", "total_amount")
    def _check_pricing_positive(self):
        """Ensure pricing values are positive"""
        for record in self:
            if record.unit_price and record.unit_price < 0:
                raise ValidationError(_("Unit price must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals):
        """Override create to set defaults and generate sequence"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("shredding.service") or _("New")
        
        if not vals.get("serial_number"):
            vals["serial_number"] = self.env["ir.sequence"].next_by_code("shredding.service.serial") or _("SRV-001")
        
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Service status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)
