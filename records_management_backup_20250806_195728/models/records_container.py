# -*- coding: utf-8 -*-
"""
Records Container Management Module

This module provides comprehensive container management functionality for the Records Management System.
It handles the complete lifecycle of physical storage containers including creation, tracking, movement,
and destruction processes with full NAID AAA compliance.

Key Features:
- Complete container lifecycle management (draft → active → stored → destroyed)
- Document containment with capacity tracking and full/empty status
- Location-based storage with movement history and audit trails
- Retention policy automation with destruction scheduling
- Security classification and access control management
- Integration with barcode systems for container identification
- Billing rate management and service level configuration
- NAID compliance with audit trails and chain of custody

Business Processes:
1. Container Registration: Create containers with customer assignment and specifications
2. Document Loading: Associate documents with containers and track capacity
3. Storage Management: Move containers through locations with full audit trail
4. Retention Compliance: Automatic destruction scheduling based on retention policies
5. Retrieval Services: Track container access and document retrieval requests
6. Destruction Processing: NAID-compliant destruction with certificate generation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RecordsContainer(models.Model):
    """
    Records Container Management

    Note: Removed duplicate customer_id field to avoid confusion.
    The partner_id field is now used as the customer reference throughout this model.
    """

    _name = "records.container"
    _description = "Records Container Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Container Number", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Container Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================

    company_id = fields.Many2one(
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        string="Container Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

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
    # CUSTOMER & LOCATION RELATIONSHIPS
    # ============================================================================

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    department_id = fields.Many2one("records.department", string="Department")
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True
    )

    # Barcode Product Relationship (for barcoded containers)
    barcode_product_id = fields.Many2one(
        "barcode.product", string="Barcode Product", tracking=True
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS
    # ============================================================================

    container_type_id = fields.Many2one(
        "records.container.type", string="Container Type", required=True
    )
    barcode = fields.Char(string="Barcode", index=True, tracking=True)
    dimensions = fields.Char(string="Dimensions")
    weight = fields.Float(string="Weight (lbs)", digits="Stock Weight", default=0.0)
    cubic_feet = fields.Float(string="Cubic Feet", digits="Stock Weight", default=0.0)

    # ============================================================================
    # CONTENT MANAGEMENT
    # ============================================================================

    document_ids = fields.One2many(
        "records.document", "container_id", string="Documents"
    )
    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count", store=True
    )
    content_description = fields.Text(string="Content Description")
    is_full = fields.Boolean(string="Container Full", default=False)

    # ============================================================================
    # DATE TRACKING
    # ============================================================================

    received_date = fields.Date(
        string="Received Date", default=fields.Date.today, tracking=True
    )
    storage_start_date = fields.Date(string="Storage Start Date")
    stored_date = fields.Date(string="Stored Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date")
    destruction_date = fields.Date(string="Destruction Date")

    # ============================================================================
    # RETENTION MANAGEMENT
    # ============================================================================

    retention_policy_id = fields.Many2one(
        "records.retention.policy", string="Retention Policy"
    )
    retention_years = fields.Integer(string="Retention Years", default=7)
    destruction_due_date = fields.Date(
        string="Destruction Due Date",
        compute="_compute_destruction_due_date",
        store=True,
    )
    permanent_retention = fields.Boolean(string="Permanent Retention", default=False)

    # ============================================================================
    # BILLING & SERVICES
    # ============================================================================

    billing_rate = fields.Float(
        string="Monthly Billing Rate", digits="Product Price", default=0.0
    )
    service_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("climate_controlled", "Climate Controlled"),
            ("high_security", "High Security"),
        ],
        string="Service Level",
        default="standard",
    )

    # ============================================================================
    # SECURITY & ACCESS
    # ============================================================================

    security_level = fields.Selection(
        [
            ("public", "Public"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="confidential",
    )
    access_restriction = fields.Text(string="Access Restrictions")
    authorized_users = fields.Many2many("res.users", string="Authorized Users")

    # ============================================================================
    # CONDITION & MAINTENANCE
    # ============================================================================

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
    )
    maintenance_notes = fields.Text(string="Maintenance Notes")
    last_inspection_date = fields.Date(string="Last Inspection Date")

    # ============================================================================
    # MOVEMENT TRACKING
    # ============================================================================

    movement_ids = fields.One2many(
        "records.container.movement", "container_id", string="Movement History"
    )
    current_movement_id = fields.Many2one(
        "records.container.movement", string="Current Movement"
    )
    converter_id = fields.Many2one(
        "records.container.type.converter", string="Converter"
    )

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_activate(self):
        """Activate container for storage"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation"))
        if not self.location_id:
            raise UserError(_("Storage location must be assigned"))

        self.write(
            {
                "storage_start_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Container activated for storage"))

    def action_mark_full(self):
        """Mark container as full"""
        self.ensure_one()
        self.write({"is_full": True})
        self.message_post(body=_("Container marked as full"))

    def action_schedule_destruction(self):
        """Schedule container for destruction"""
        self.ensure_one()
        if self.permanent_retention:
            raise UserError(
                _("Cannot schedule permanent retention containers for destruction")
            )

        self.write({"state": "pending_destruction"})
        self.message_post(body=_("Container scheduled for destruction"))

    def action_destroy(self):
        """Mark container as destroyed"""
        self.ensure_one()
        if self.state != "pending_destruction":
            raise UserError(_("Only containers pending destruction can be destroyed"))

        self.write(
            {
                "destruction_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Container destroyed"))

    def action_view_documents(self):
        """View all documents in this container"""
        self.ensure_one()
        return {
            "name": _("Documents in Container %s") % self.name,
            "domain": [("container_id", "=", self.id)],
        }

    def action_generate_barcode(self):
        """Generate and print barcode for container"""
        self.ensure_one()
        if not self.barcode:
            # Generate barcode if not exists
            self.barcode = (
                self.env["ir.sequence"].next_by_code("records.container.barcode")
                or self.name
            )

        return {}

    def action_index_container(self):
        """Index container - change state from received to indexed"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft containers can be indexed"))
        self.write({"state": "active"})
        self.message_post(body=_("Container indexed and activated"))

    def action_store_container(self):
        """Store container - change state from indexed to stored"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active containers can be stored"))
        if not self.location_id:
            raise UserError(_("Storage location must be assigned before storing"))
        self.write({"state": "stored", "storage_start_date": fields.Date.today()})
        self.message_post(
            body=_("Container stored at location %s") % self.location_id.name
        )

    def action_retrieve_container(self):
        """Retrieve container from storage"""
        self.ensure_one()
        if self.state not in ["stored", "active"]:
            raise UserError(_("Only stored or active containers can be retrieved"))
        self.write({"state": "in_transit", "last_access_date": fields.Date.today()})
        self.message_post(body=_("Container retrieved from storage"))

    def action_destroy_container(self):
        """Prepare container for destruction"""
        self.ensure_one()
        if self.permanent_retention:
            raise UserError(_("Cannot destroy containers with permanent retention"))
        self.action_schedule_destruction()

    def action_bulk_convert_container_type(self):
        """Bulk convert container types"""
        return {
            "name": _("Bulk Convert Container Types"),
            "context": {"default_container_ids": [(6, 0, self.ids)]},
        }

    def create_movement_record(
        self, from_location_id, to_location_id, movement_type="transfer"
    ):
        """Create movement record for container"""
        self.ensure_one()
        movement_vals = {
            "movement_date": fields.Date.today(),
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "movement_type": movement_type,
            "container_id": self.id,
        }

        movement = self.env["records.container.movement"].create(movement_vals)
        self.current_movement_id = movement.id
        return movement

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    @api.depends("document_ids")
    def _compute_document_count(self):
        for container in self:
            container.document_count = len(container.document_ids)

    @api.depends("storage_start_date", "retention_years", "permanent_retention")
    def _compute_destruction_due_date(self):
        for container in self:
            if container.permanent_retention or not container.storage_start_date:
                container.destruction_due_date = False
            else:
                container.destruction_due_date = (
                    container.storage_start_date
                    + relativedelta(years=container.retention_years)
                )

    is_due_for_destruction = fields.Boolean(
        string="Due for Destruction",
        compute="_compute_is_due_for_destruction",
        search="_search_due_for_destruction",
    )

    @api.depends("destruction_due_date")
    def _compute_is_due_for_destruction(self):
        today = fields.Date.today()
        for container in self:
            container.is_due_for_destruction = (
                container.destruction_due_date
                and container.destruction_due_date <= today
                and not container.permanent_retention
            )

    def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
        if (operator == "=" and value) or (operator == "!=" and not value):
            return [
                ("destruction_due_date", "<=", today),
                ("permanent_retention", "=", False),
                ("state", "!=", "destroyed"),
            ]
        else:
            return [
                ("destruction_due_date", ">", today),
                ("permanent_retention", "=", True),
            ]

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("weight", "cubic_feet")
    def _check_positive_values(self):
        for record in self:
            if record.weight < 0 or record.cubic_feet < 0:
                raise ValidationError(
                    _("Weight and cubic feet must be positive values")
                )

    @api.constrains("retention_years")
    def _check_retention_years(self):
        for record in self:
            if record.retention_years < 0:
                raise ValidationError(_("Retention years cannot be negative"))

    @api.constrains("received_date", "storage_start_date")
    def _check_date_consistency(self):
        for record in self:
            if (
                record.received_date
                and record.storage_start_date
                and record.received_date > record.storage_start_date
            ):
                raise ValidationError(
                    _("Storage start date cannot be before received date")
                )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("records.container") or "NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        # Update last access date when certain fields change
        if any(key in vals for key in ["location_id", "state"]):
            vals["last_access_date"] = fields.Date.today()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state in ("active", "stored"):
                raise UserError(_("Cannot delete active containers"))
            if record.document_ids:
                raise UserError(_("Cannot delete containers with documents"))
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def get_next_inspection_date(self):
        """Calculate next inspection date based on service level"""
        self.ensure_one()
        if not self.last_inspection_date:
            return fields.Date.today() + relativedelta(months=6)
        inspection_intervals = {
            "standard": 12,
            "premium": 6,
            "climate_controlled": 4,
            "high_security": 3,
        }
        interval = inspection_intervals.get(self.service_level, 12)
        return self.last_inspection_date + relativedelta(months=interval)

    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================

    # ============================================================================
