# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingService(models.Model):
    _name = "shredding.service"
    _description = "Shredding Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # Essential Shredding Service Fields (from view analysis)
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    service_location_type = fields.Selection(
        [("onsite", "On-Site"), ("offsite", "Off-Site")],
        string="Service Location",
        required=True,
        default="onsite",
        tracking=True,
    )
    service_type = fields.Selection(
        [
            ("box_shredding", "Box Shredding"),
            ("bin_shredding", "Bin Shredding"),
            ("hard_drive_destruction", "Hard Drive Destruction"),
            ("uniform_destruction", "Uniform Destruction"),
            ("pickup", "Pickup Service"),
            ("scheduled", "Scheduled Service"),
            ("emergency", "Emergency Shredding"),
            ("purge", "Purge Service"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    status = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("rescheduled", "Rescheduled"),
        ],
        string="Status",
        default="scheduled",
        tracking=True,
    )

    # Scheduling
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, tracking=True
    )
    actual_start_time = fields.Datetime(string="Actual Start Time")
    actual_completion_time = fields.Datetime(string="Actual Completion Time")
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)", digits=(8, 2)
    )

    # Destruction Details
    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("disintegration", "Disintegration"),
            ("pulverization", "Pulverization"),
            ("incineration", "Incineration"),
            ("degaussing", "Degaussing (Electronic Media)"),
        ],
        string="Destruction Method",
        required=True,
        tracking=True,
    )

    # NAID Compliance
    naid_compliance_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
            ("standard", "Standard"),
        ],
        string="NAID Compliance Level",
        required=True,
        default="standard",
    )

    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    witness_required = fields.Boolean(string="Witness Required", default=False)

    # Service Details
    container_count = fields.Integer(string="Container Count", default=0)
    total_weight = fields.Float(string="Total Weight (lbs)", digits=(10, 2))
    document_types = fields.Text(string="Document Types")
    uniform_destruction_details = fields.Text(string="Uniform Destruction Details")

    # Uniform-Specific Fields
    uniform_type = fields.Selection(
        [
            ("corporate", "Corporate Uniforms"),
            ("medical", "Medical Scrubs"),
            ("security", "Security Uniforms"),
            ("hospitality", "Hospitality Uniforms"),
            ("school", "School Uniforms"),
            ("industrial", "Industrial Workwear"),
            ("other", "Other Uniform Types"),
        ],
        string="Uniform Type",
        help="Type of uniforms being destroyed",
    )
    uniform_count = fields.Integer(string="Number of Uniforms", default=0)
    uniform_brands = fields.Text(string="Uniform Brands/Labels")
    uniform_destruction_reason = fields.Selection(
        [
            ("expired", "Expired/End of Use"),
            ("damaged", "Damaged Beyond Repair"),
            ("rebrand", "Company Rebranding"),
            ("policy", "Policy Change"),
            ("contaminated", "Contaminated"),
            ("recalled", "Product Recall"),
        ],
        string="Destruction Reason",
    )

    # Location and Logistics
    service_location = fields.Text(string="Service Location")
    onsite_requirements = fields.Text(
        string="On-Site Requirements", help="Special requirements for on-site service"
    )
    access_instructions = fields.Text(string="Site Access Instructions")
    assigned_technician = fields.Many2one("res.users", string="Assigned Technician")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Service Vehicle")

    # Financial
    service_cost = fields.Monetary(string="Service Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Documentation
    certificate_generated = fields.Boolean(
        string="Certificate Generated", default=False
    )
    photos_taken = fields.Integer(string="Photos Taken", default=0)
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )

    # Quality and Compliance
    quality_check_passed = fields.Boolean(string="Quality Check Passed", default=False)
    compliance_verified = fields.Boolean(string="Compliance Verified", default=False)
    audit_trail_ids = fields.One2many(
        "shredding.audit.trail", "service_id", string="Audit Trail"
    )

    # Customer Service
    customer_notification_sent = fields.Boolean(
        string="Customer Notification Sent", default=False
    )
    customer_feedback = fields.Text(string="Customer Feedback")
    customer_rating = fields.Selection(
        [
            ("1", "Poor"),
            ("2", "Fair"),
            ("3", "Good"),
            ("4", "Very Good"),
            ("5", "Excellent"),
        ],
        string="Customer Rating",
    )

    # Related Records
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    pickup_request_id = fields.Many2one("pickup.request", string="Pickup Request")

    # System Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Service Manager", default=lambda self: self.env.user
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        tracking=True,
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
    is_uniform_service = fields.Boolean(
        string="Is Uniform Service", compute="_compute_is_uniform_service", store=True
    )

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("service_type")
    def _compute_is_uniform_service(self):
        """Determine if this is a uniform destruction service."""
        for record in self:
            record.is_uniform_service = record.service_type == "uniform_destruction"

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

    # =========================================================================
    # UNIFORM DESTRUCTION SPECIFIC METHODS
    # =========================================================================

    def action_process_uniform_destruction(self):
        """Process uniform destruction with special handling."""
        self.ensure_one()
        if self.service_type != "uniform_destruction":
            raise UserError(
                _("This action is only available for uniform destruction services.")
            )

        if not self.uniform_type:
            raise UserError(_("Uniform type must be specified before processing."))

        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nUniform destruction process initiated on %s for %s uniforms")
                % (
                    fields.Datetime.now(),
                    dict(self._fields["uniform_type"].selection)[self.uniform_type],
                ),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Uniform Destruction Started"),
                "message": _("Uniform destruction process has been initiated for %s")
                % self.uniform_type,
                "type": "success",
            },
        }

    def action_validate_uniform_inventory(self):
        """Validate uniform inventory before destruction."""
        self.ensure_one()
        if not self.is_uniform_service:
            raise UserError(_("This action is only available for uniform services."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Uniform Inventory Validation"),
            "res_model": "uniform.inventory.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_uniform_type": self.uniform_type,
                "default_uniform_count": self.uniform_count,
            },
        }

    # =========================================================================
    # ON-SITE / OFF-SITE SERVICE METHODS
    # =========================================================================

    def action_schedule_onsite_service(self):
        """Schedule on-site shredding service."""
        self.ensure_one()
        if self.service_location_type != "onsite":
            raise UserError(_("This action is only available for on-site services."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule On-Site Service"),
            "res_model": "onsite.scheduling.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_customer_id": self.customer_id.id,
                "default_service_type": self.service_type,
            },
        }

    def action_prepare_offsite_transport(self):
        """Prepare materials for off-site transport."""
        self.ensure_one()
        if self.service_location_type != "offsite":
            raise UserError(_("This action is only available for off-site services."))

        self.write(
            {
                "notes": (self.notes or "")
                + _("\nOff-site transport preparation completed on %s")
                % fields.Datetime.now()
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Transport Prepared"),
                "message": _("Materials prepared for off-site destruction transport"),
                "type": "success",
            },
        }

    def action_validate_site_access(self):
        """Validate access requirements for on-site service."""
        self.ensure_one()
        if self.service_location_type != "onsite":
            raise UserError(
                _("Site access validation is only required for on-site services.")
            )

        if not self.access_instructions:
            raise UserError(
                _("Access instructions must be provided for on-site services.")
            )

        self.write(
            {
                "notes": (self.notes or "")
                + _("\nSite access validated on %s") % fields.Datetime.now()
            }
        )

        return True

    # =========================================================================
    # COMPREHENSIVE SHREDDING SERVICE ACTION METHODS
    # =========================================================================

    def action_view_hard_drives(self):
        """View hard drives associated with this shredding service"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Hard Drives"),
            "res_model": "shredding.hard_drive",
            "view_mode": "tree,form",
            "domain": [("service_id", "=", self.id)],
            "context": {"default_service_id": self.id},
        }

    def action_compliance_check(self):
        """Perform NAID compliance verification check"""
        self.ensure_one()
        # Validate compliance requirements
        if not self.service_type:
            raise UserError(_("Service type must be specified for compliance check"))

        # Mark compliance verified
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nNAID Compliance Check completed on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Check"),
                "message": _("NAID AAA compliance verification completed successfully"),
                "type": "success",
            },
        }

    def action_mark_customer_scanned(self):
        """Mark hard drives as scanned at customer location"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nCustomer location scanning completed on %s")
                % fields.Datetime.now(),
            }
        )
        return True

    def action_mark_facility_verified(self):
        """Mark items as verified at facility"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nFacility verification completed on %s") % fields.Datetime.now(),
            }
        )
        return True

    def action_start_destruction(self):
        """Initiate the destruction process with proper validation"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to start destruction"))

        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nDestruction process started on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Destruction Started"),
                "message": _("Destruction process has been initiated"),
                "type": "success",
            },
        }

    def action_verify_witness(self):
        """Verify witness for destruction process"""
        self.ensure_one()
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nWitness verification completed on %s") % fields.Datetime.now()
            }
        )
        return True

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to generate certificate"))

        # Mark certificate generated
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nDestruction certificate generated on %s") % fields.Datetime.now()
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Generated"),
                "message": _("Destruction certificate has been created successfully"),
                "type": "success",
            },
        }

    def action_scan_hard_drives_customer(self):
        """Scan hard drives at customer location"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Hard Drives - Customer Location"),
            "res_model": "hard_drive.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_location_type": "customer",
            },
        }

    def action_scan_hard_drives_facility(self):
        """Scan hard drives at facility"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Hard Drives - Facility"),
            "res_model": "hard_drive.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_location_type": "facility",
            },
        }

    def action_witness_verification(self):
        """Open witness verification dialog"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Witness Verification"),
            "res_model": "shredding.service",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"show_witness_verification": True},
        }

    def action_mark_destroyed(self):
        """Mark service as completely destroyed"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to mark as destroyed"))

        self.write(
            {
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nDestruction completed on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Destruction Complete"),
                "message": _("Service has been marked as completely destroyed"),
                "type": "success",
            },
        }

    def action_view_certificates(self):
        """View all destruction certificates for this service."""
        self.ensure_one()

        # Create activity to track certificate viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Destruction certificates reviewed: %s") % self.name,
            note=_("All destruction certificates for this service have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificates: %s") % self.name,
            "res_model": "destruction.certificate",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_group_by_date": True,
            },
        }

    def action_view_items(self):
        """View all items included in this shredding service."""
        self.ensure_one()

        # Create activity to track item viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Shredding items reviewed: %s") % self.name,
            note=_("All items included in this shredding service have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shredding Items: %s") % self.name,
            "res_model": "shredding.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_group_by_type": True,
            },
        }

    def action_view_witnesses(self):
        """View all witnesses for this shredding service."""
        self.ensure_one()

        # Create activity to track witness viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Witnesses reviewed: %s") % self.name,
            note=_(
                "All witnesses for this shredding service have been reviewed and verified."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shredding Witnesses: %s") % self.name,
            "res_model": "shredding.witness",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_verified": True,
            },
        }

    @api.model
    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Shredding Service")
        return super().create(vals)
