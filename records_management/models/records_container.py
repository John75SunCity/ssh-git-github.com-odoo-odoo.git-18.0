# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class RecordsContainer(models.Model):
    _name = "records.container"
    _description = "Records Container Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Container Number", required=True, tracking=True, index=True)
    code = fields.Char(string="Container Code", index=True, tracking=True)
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
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("in_transit", "In Transit"),
            ("stored", "Stored"),
            ("pending_destruction", "Pending Destruction"),
            ("destroyed", "Destroyed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CONTAINER CLASSIFICATION
    # ============================================================================

    # Container Type Configuration
    container_type = fields.Selection(
        [
            ("standard_box", "Standard Storage Box"),
            ("legal_box", "Legal Size Box"),
            ("file_folder", "File Folder"),
            ("binder", "Binder"),
            ("archive_box", "Archive Box"),
            ("media_container", "Media Container"),
            ("custom", "Custom Container"),
        ],
        string="Container Type",
        required=True,
        tracking=True,
    )

    container_category = fields.Selection(
        [
            ("permanent", "Permanent Storage"),
            ("temporary", "Temporary Storage"),
            ("transit", "In Transit"),
            ("destruction", "Pending Destruction"),
        ],
        string="Container Category",
        default="permanent",
        tracking=True,
    )

    container_material = fields.Selection(
        [
            ("cardboard", "Cardboard"),
            ("plastic", "Plastic"),
            ("metal", "Metal"),
            ("fabric", "Fabric"),
            ("mixed", "Mixed Materials"),
        ],
        string="Material",
        default="cardboard",
    )

    size_category = fields.Selection(
        [
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
            ("extra_large", "Extra Large"),
        ],
        string="Size Category",
        default="medium",
    )

    # ============================================================================
    # LOCATION & TRACKING
    # ============================================================================

    # Location Management
    location_id = fields.Many2one(
        "records.location", string="Current Location", tracking=True
    )
    from_location_id = fields.Many2one(
        "records.location", string="From Location", tracking=True
    )
    to_location_id = fields.Many2one(
        "records.location", string="To Location", tracking=True
    )

    # Customer and Department
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    department_id = fields.Many2one(
        "records.department", string="Department", tracking=True
    )

    # Barcode and Identification
    barcode = fields.Char(string="Barcode", index=True, tracking=True)
    qr_code = fields.Char(string="QR Code", tracking=True)
    rfid_tag = fields.Char(string="RFID Tag", tracking=True)

    # ============================================================================
    # PHYSICAL PROPERTIES
    # ============================================================================

    # Dimensions
    length = fields.Float(string="Length (cm)", digits=(8, 2))
    width = fields.Float(string="Width (cm)", digits=(8, 2))
    height = fields.Float(string="Height (cm)", digits=(8, 2))
    
    # Weight and Capacity
    weight = fields.Float(string="Weight (kg)", digits=(8, 2), tracking=True)
    max_weight = fields.Float(string="Max Weight (kg)", digits=(8, 2))
    volume = fields.Float(string="Volume (m³)", digits=(8, 3))
    capacity = fields.Float(string="Capacity", digits=(8, 2))

    # Status Indicators
    fill_level = fields.Float(
        string="Fill Level %", digits=(5, 2), default=0.0, tracking=True
    )
    condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Condition",
        default="good",
        tracking=True,
    )

    # ============================================================================  
    # FINANCIAL INFORMATION
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Valuation
    container_value = fields.Monetary(
        string="Container Value", currency_field="currency_id", tracking=True
    )
    content_value = fields.Monetary(
        string="Content Value", currency_field="currency_id", tracking=True
    )
    replacement_cost = fields.Monetary(
        string="Replacement Cost", currency_field="currency_id"
    )

    # Insurance
    insured_value = fields.Monetary(
        string="Insured Value", currency_field="currency_id"
    )
    insurance_policy = fields.Char(string="Insurance Policy Number")

    # ============================================================================
    # SECURITY & COMPLIANCE
    # ============================================================================

    # Security Classification
    security_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="internal",
        tracking=True,
    )

    # Access Control
    requires_authorization = fields.Boolean(
        string="Requires Authorization", default=False
    )
    authorized_users = fields.Many2many(
        "res.users", string="Authorized Users"
    )

    # Compliance
    naid_compliant = fields.Boolean(string="NAID Compliant", default=False)
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=False
    )

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================

    # Important Dates
    creation_date = fields.Date(string="Creation Date", default=fields.Date.today)
    received_date = fields.Date(string="Received Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date", tracking=True)
    destruction_date = fields.Date(string="Scheduled Destruction Date", tracking=True)

    # Retention Management
    retention_period = fields.Integer(string="Retention Period (Years)", default=7)
    retention_start_date = fields.Date(string="Retention Start Date")
    retention_end_date = fields.Date(
        string="Retention End Date", 
        compute="_compute_retention_end_date", 
        store=True
    )

    # ============================================================================
    # OPERATIONAL FIELDS
    # ============================================================================

    # Status Tracking
    is_full = fields.Boolean(string="Is Full", compute="_compute_is_full", store=True)
    is_overdue = fields.Boolean(
        string="Is Overdue", compute="_compute_is_overdue", store=True
    )
    is_accessible = fields.Boolean(string="Is Accessible", default=True)

    # Workflow Management
    needs_review = fields.Boolean(string="Needs Review", default=False)
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
    )

    # Counts and Statistics
    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count", store=True
    )
    access_count = fields.Integer(string="Access Count", default=0)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Core Relationships
    document_ids = fields.One2many(
        "records.document", "container_id", string="Documents"
    )
    movement_ids = fields.One2many(
        "records.container.movement", "container_id", string="Movement History"
    )
    
    # Container Contents
    content_ids = fields.One2many(
        "container.contents", "container_id", string="Container Contents"
    )

    # Related Records
    pickup_request_ids = fields.One2many(
        "pickup.request", "container_id", string="Pickup Requests"
    )
    audit_log_ids = fields.One2many(
        "records.audit.log", "container_id", string="Audit Logs"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("retention_start_date", "retention_period")
    def _compute_retention_end_date(self):
        """Compute retention end date"""
        for record in self:
            if record.retention_start_date and record.retention_period:
                record.retention_end_date = record.retention_start_date + relativedelta(
                    years=record.retention_period
                )
            else:
                record.retention_end_date = False

    @api.depends("fill_level")
    def _compute_is_full(self):
        """Compute if container is full"""
        for record in self:
            record.is_full = record.fill_level >= 95.0

    @api.depends("retention_end_date")
    def _compute_is_overdue(self):
        """Compute if container is overdue for action"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.retention_end_date and record.retention_end_date < today
            )

    @api.depends("document_ids")
    def _compute_document_count(self):
        """Compute number of documents in container"""
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Compute display name with code"""
        for record in self:
            if record.code:
                record.display_name = f"[{record.code}] {record.name}"
            else:
                record.display_name = record.name or _("New")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_mark_full(self):
        """Mark container as full"""
        self.ensure_one()
        self.write({
            'fill_level': 100.0,
            'state': 'stored',
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Container Marked Full"),
                "message": _("Container has been marked as full."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_schedule_pickup(self):
        """Schedule container pickup"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Pickup"),
            "res_model": "pickup.request",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_container_id": self.id,
                "default_customer_id": self.customer_id.id,
                "default_location_id": self.location_id.id,
            },
        }

    def action_view_documents(self):
        """View container documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Container Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("container_id", "=", self.id)],
        }

    def action_view_movement_history(self):
        """View container movement history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Movement History"),
            "res_model": "records.container.movement",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("container_id", "=", self.id)],
        }

    def action_create_chain_of_custody(self):
        """Create chain of custody record"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "records.chain.of.custody",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_container_id": self.id,
                "default_customer_id": self.customer_id.id,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("fill_level")
    def _check_fill_level(self):
        """Validate fill level percentage"""
        for record in self:
            if record.fill_level and (record.fill_level < 0 or record.fill_level > 100):
                raise ValidationError(_("Fill level must be between 0 and 100."))

    @api.constrains("weight", "max_weight")
    def _check_weight(self):
        """Validate weight constraints"""
        for record in self:
            if record.weight and record.weight < 0:
                raise ValidationError(_("Weight cannot be negative."))
            if record.max_weight and record.max_weight < 0:
                raise ValidationError(_("Maximum weight cannot be negative."))
            if (
                record.weight 
                and record.max_weight 
                and record.weight > record.max_weight
            ):
                raise ValidationError(_("Weight cannot exceed maximum weight."))

    @api.constrains("retention_period")
    def _check_retention_period(self):
        """Validate retention period"""
        for record in self:
            if record.retention_period and record.retention_period < 0:
                raise ValidationError(_("Retention period cannot be negative."))

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate container dimensions"""
        for record in self:
            if record.length and record.length <= 0:
                raise ValidationError(_("Length must be positive."))
            if record.width and record.width <= 0:
                raise ValidationError(_("Width must be positive."))
            if record.height and record.height <= 0:
                raise ValidationError(_("Height must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("records.container") or _("New")
        if not vals.get("creation_date"):
            vals["creation_date"] = fields.Date.today()
        return super().create(vals)

    def write(self, vals):
        """Override write to track location changes"""
        if 'location_id' in vals:
            for record in self:
                if record.location_id.id != vals['location_id']:
                    record.message_post(
                        body=_("Container moved from %s to %s") % (
                            record.location_id.name or _("Unknown"),
                            self.env['records.location'].browse(vals['location_id']).name or _("Unknown")
                        )
                    )
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of containers with documents"""
        if any(record.document_count > 0 for record in self):
            raise UserError(_("Cannot delete containers that contain documents."))
        return super().unlink()
