# -*- coding: utf-8 -*-
"""
Temporary Inventory Management Module

This module provides comprehensive temporary inventory management for the Records
Management System. It handles temporary storage tracking, location management,
document association, and workflow integration with complete audit trails.

Key Features:
- Temporary inventory lifecycle management
- Integration with records management system
- Location and capacity tracking
- Document association and counting
- Advanced workflow management with states
- Complete audit trails and compliance logging

Business Processes:
1. Inventory Creation: Initial setup with location and capacity definition
2. Document Association: Link documents for temporary tracking
3. Capacity Management: Monitor utilization and availability
4. Location Tracking: Real-time location monitoring with movements
5. Workflow Management: Complete state management with approvals
6. Audit Compliance: Complete tracking for records management compliance

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

class TempInventory(models.Model):
    _name = "temp.inventory"
    _description = "Temporary Inventory Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, date_created desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Inventory Reference",
        required=True,
        tracking=True,
        index=True,
        help="Unique temporary inventory reference",
    )
    description = fields.Text(
        string="Description", help="Detailed description of temporary inventory"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order sequence"
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of inventory record"
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
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this temporary inventory",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("in_use", "In Use"),
            ("full", "Full Capacity"),
            ("archived", "Archived"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current inventory status",
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
        help="Priority level for processing",
    )

    # ============================================================================
    # LOCATION AND STORAGE
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        help="Physical location where inventory is stored",
    )
    storage_type = fields.Selection(
        [
            ("boxes", "Document Boxes"),
            ("files", "File Folders"),
            ("media", "Electronic Media"),
            ("mixed", "Mixed Storage"),
        ],
        string="Storage Type",
        default="boxes",
        help="Type of items stored",
    )
    capacity_limit = fields.Integer(
        string="Capacity Limit",
        default=100,
        help="Maximum number of items that can be stored",
    )
    current_count = fields.Integer(
        string="Current Count",
        compute="_compute_current_count",
        store=True,
        help="Current number of items stored",
    )
    available_capacity = fields.Integer(
        string="Available Capacity",
        compute="_compute_available_capacity",
        store=True,
        help="Remaining storage capacity",
    )
    utilization_percent = fields.Float(
        string="Utilization %",
        compute="_compute_utilization_percent",
        store=True,
        help="Percentage of capacity utilized",
    )

    # ============================================================================
    # DOCUMENT RELATIONSHIPS
    # ============================================================================
    document_ids = fields.One2many(
        "records.document",
        "temp_inventory_id",
        string="Associated Documents",
        help="Documents stored in this temporary inventory",
    )
    container_ids = fields.One2many(
        "records.container",
        "temp_inventory_id",
        string="Associated Containers",
        help="Containers stored in this temporary inventory",
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
        store=True,
        help="Total number of associated documents",
    )
    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_count",
        store=True,
        help="Total number of associated containers",
    )

    # ============================================================================
    # TEMPORAL FIELDS
    # ============================================================================
    date_created = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        required=True,
        help="When inventory record was created",
    )
    date_modified = fields.Datetime(
        string="Last Modified", help="When inventory was last modified"
    )
    date_activated = fields.Datetime(
        string="Activation Date", help="When inventory was activated"
    )
    date_archived = fields.Datetime(
        string="Archive Date", help="When inventory was archived"
    )
    retention_period = fields.Integer(
        string="Retention Period (Days)",
        default=30,
        help="How long items can stay in temporary inventory",
    )
    expiry_date = fields.Date(
        string="Expiry Date",
        compute="_compute_expiry_date",
        store=True,
        help="When temporary storage expires",
    )

    # ============================================================================
    # WORKFLOW AND APPROVAL
    # ============================================================================
    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Whether approval is required for this inventory",
    )
    approved_by = fields.Many2one(
        "res.users", string="Approved By", help="User who approved this inventory"
    )
    approval_date = fields.Datetime(
        string="Approval Date", help="When inventory was approved"
    )
    rejection_reason = fields.Text(
        string="Rejection Reason", help="Reason for rejection if applicable"
    )

    # ============================================================================
    # INVENTORY MANAGEMENT
    # ============================================================================
    inventory_type = fields.Selection(
        [
            ("temporary", "Temporary Storage"),
            ("staging", "Staging Area"),
            ("quarantine", "Quarantine"),
            ("processing", "Processing Queue"),
        ],
        string="Inventory Type",
        default="temporary",
        help="Type of temporary inventory",
    )
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
        ],
        string="Access Level",
        default="restricted",
        help="Security access level",
    )
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled",
        default=False,
        help="Whether storage is temperature controlled",
    )
    humidity_controlled = fields.Boolean(
        string="Humidity Controlled",
        default=False,
        help="Whether storage is humidity controlled",
    )

    # ============================================================================
    # MOVEMENT AND TRACKING
    # ============================================================================
    movement_ids = fields.One2many(
        "temp.inventory.movement",
        "inventory_id",
        string="Inventory Movements",
        help="History of inventory movements",
    )
    last_movement_date = fields.Datetime(
        string="Last Movement",
        compute="_compute_last_movement_date",
        store=True,
        help="Date of last inventory movement",
    )
    movement_count = fields.Integer(
        string="Movement Count",
        compute="_compute_movement_count",
        store=True,
        help="Total number of movements",
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    compliance_required = fields.Boolean(
        string="Compliance Required",
        default=True,
        help="Whether compliance tracking is required",
    )
    audit_trail_ids = fields.One2many(
        "temp.inventory.audit",
        "inventory_id",
        string="Audit Trail",
        help="Complete audit trail for this inventory",
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required",
        default=False,
        help="Whether chain of custody tracking is required",
    )
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=False,
        help="Whether inventory meets NAID standards",
    )

    # ============================================================================
    # FINANCIAL FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    storage_cost = fields.Monetary(
        string="Storage Cost",
        currency_field="currency_id",
        default=0.0,
        help="Cost of temporary storage",
    )
    handling_cost = fields.Monetary(
        string="Handling Cost",
        currency_field="currency_id",
        default=0.0,
        help="Cost of handling and processing",
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
        help="Total cost including storage and handling",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for this inventory record",
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
    @api.depends("name", "inventory_type", "current_count")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.name:
                record.display_name = f"{record.name} ({record.current_count} items)"
            else:
                record.display_name = _("New Temporary Inventory")

    @api.depends("document_ids", "container_ids")
    def _compute_current_count(self):
        """Compute current count of items"""
        for record in self:
            record.current_count = len(record.document_ids) + len(record.container_ids)

    @api.depends("capacity_limit", "current_count")
    def _compute_available_capacity(self):
        """Compute available capacity"""
        for record in self:
            record.available_capacity = max(
                0, record.capacity_limit - record.current_count
            )

    @api.depends("current_count", "capacity_limit")
    def _compute_utilization_percent(self):
        """Compute utilization percentage"""
        for record in self:
            if record.capacity_limit > 0:
                record.utilization_percent = (
                    record.current_count / record.capacity_limit
                ) * 100
            else:
                record.utilization_percent = 0.0

    @api.depends("document_ids")
    def _compute_document_count(self):
        """Compute document count"""
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends("container_ids")
    def _compute_container_count(self):
        """Compute container count"""
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends("date_activated", "retention_period")
    def _compute_expiry_date(self):
        """Compute expiry date based on activation and retention period"""
        for record in self:
            if record.date_activated and record.retention_period:
                expiry_datetime = record.date_activated + timedelta(
                    days=record.retention_period
                )
                record.expiry_date = expiry_datetime.date()
            else:
                record.expiry_date = False

    @api.depends("movement_ids", "movement_ids.date")
    def _compute_last_movement_date(self):
        """Compute last movement date"""
        for record in self:
            if record.movement_ids:
                record.last_movement_date = max(record.movement_ids.mapped("date"))
            else:
                record.last_movement_date = False

    @api.depends("movement_ids")
    def _compute_movement_count(self):
        """Compute movement count"""
        for record in self:
            record.movement_count = len(record.movement_ids)

    @api.depends("storage_cost", "handling_cost")
    def _compute_total_cost(self):
        """Compute total cost"""
        for record in self:
            record.total_cost = record.storage_cost + record.handling_cost

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the temporary inventory"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft inventories can be activated"))

        self.write(
            {
                "state": "active",
                "date_activated": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Temporary inventory activated"))

    def action_deactivate(self):
        """Deactivate the temporary inventory"""
        self.ensure_one()
        if self.state not in ("active", "in_use"):
            raise UserError(_("Only active or in-use inventories can be deactivated"))

        self.write({"state": "archived"})
        self.message_post(body=_("Temporary inventory deactivated"))

    def action_archive(self):
        """Archive the temporary inventory"""
        self.ensure_one()
        if self.current_count > 0:
            raise UserError(
                _(
                    "Cannot archive inventory with items. "
                    "Please remove all items before archiving."
                )
            )

        self.write(
            {
                "state": "archived",
                "active": False,
                "date_archived": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Temporary inventory archived"))

    def action_approve(self):
        """Approve the temporary inventory"""
        self.ensure_one()
        if not self.approval_required:
            raise UserError(_("This inventory does not require approval"))

        self.write(
            {
                "approved_by": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Temporary inventory approved"))

    def action_reject(self):
        """Reject the temporary inventory"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Inventory"),
            "res_model": "temp.inventory.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_inventory_id": self.id},
        }

    def action_view_documents(self):
        """View associated documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Associated Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("temp_inventory_id", "=", self.id)],
            "context": {"default_temp_inventory_id": self.id},
        }

    def action_view_containers(self):
        """View associated containers"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Associated Containers"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("temp_inventory_id", "=", self.id)],
            "context": {"default_temp_inventory_id": self.id},
        }

    def action_view_movements(self):
        """View inventory movements"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Movements"),
            "res_model": "temp.inventory.movement",
            "view_mode": "tree,form",
            "domain": [("inventory_id", "=", self.id)],
            "context": {"default_inventory_id": self.id},
        }

    def action_create_movement(self):
        """Create new inventory movement"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Movement"),
            "res_model": "temp.inventory.movement",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_inventory_id": self.id,
                "default_movement_type": "in",
            },
        }

    def action_check_capacity(self):
        """Check capacity status"""
        self.ensure_one()

        if self.utilization_percent >= 100:
            self.write({"state": "full"})
            message = _("Inventory is at full capacity")
            message_type = "warning"
        elif self.utilization_percent >= 90:
            message = _("Inventory is at %s%% capacity - nearly full") % round(
                self.utilization_percent, 1
            )
            message_type = "warning"
        elif self.utilization_percent >= 75:
            message = _("Inventory is at %s%% capacity") % round(
                self.utilization_percent, 1
            )
            message_type = "info"
        else:
            message = _("Inventory has %s available slots") % self.available_capacity
            message_type = "success"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Capacity Status"),
                "message": message,
                "type": message_type,
                "sticky": False,
            },
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def check_expiry_status(self):
        """Check if inventory has expired"""
        self.ensure_one()
        if self.expiry_date and self.expiry_date <= fields.Date.today():
            return {
                "expired": True,
                "days_overdue": (fields.Date.today() - self.expiry_date).days,
            }
        return {
            "expired": False,
            "days_remaining": (
                (self.expiry_date - fields.Date.today()).days
                if self.expiry_date
                else None
            ),
        }

    def get_inventory_summary(self):
        """Get inventory summary for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "type": self.inventory_type,
            "state": self.state,
            "current_count": self.current_count,
            "capacity_limit": self.capacity_limit,
            "utilization_percent": self.utilization_percent,
            "location": self.location_id.name if self.location_id else None,
            "total_cost": self.total_cost,
            "expiry_status": self.check_expiry_status(),
        }

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains("capacity_limit")
    def _check_capacity_limit(self):
        """Validate capacity limit"""
        for record in self:
            if record.capacity_limit <= 0:
                raise ValidationError(_("Capacity limit must be greater than zero"))

    @api.constrains("retention_period")
    def _check_retention_period(self):
        """Validate retention period"""
        for record in self:
            if record.retention_period <= 0:
                raise ValidationError(_("Retention period must be greater than zero"))

    @api.constrains("storage_cost", "handling_cost")
    def _check_costs(self):
        """Validate costs are non-negative"""
        for record in self:
            if record.storage_cost < 0 or record.handling_cost < 0:
                raise ValidationError(_("Costs cannot be negative"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values and generate sequence"""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("temp.inventory") or "TI-NEW"
                )
            vals["date_created"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update modification date and handle state changes"""
        vals["date_modified"] = fields.Datetime.now()

        # Handle state changes
        if "state" in vals:
            for record in self:
                if vals["state"] != record.state:
                    record.message_post(
                        body=_("State changed from %s to %s")
                        % (
                            dict(record._fields["state"].selection)[record.state],
                            dict(record._fields["state"].selection)[vals["state"]],
                        )
                    )

        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion with items"""
        for record in self:
            if record.current_count > 0:
                raise UserError(
                    _(
                        "Cannot delete inventory '%s' because it contains %d items. "
                        "Please remove all items before deleting."
                    )
                    % (record.name, record.current_count)
                )
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_expired_inventories(self):
        """Get all expired temporary inventories"""
        return self.search(
            [
                ("expiry_date", "<=", fields.Date.today()),
                ("state", "in", ["active", "in_use"]),
            ]
        )

    @api.model
    def get_nearly_full_inventories(self, threshold=90):
        """Get inventories that are nearly full"""
        inventories = self.search([("state", "=", "active")])
        return inventories.filtered(lambda inv: inv.utilization_percent >= threshold)

    @api.model
    def cleanup_expired_inventories(self):
        """Cleanup expired inventories (automated method)"""
        expired_inventories = self.get_expired_inventories()
        for inventory in expired_inventories:
            if inventory.current_count == 0:
                inventory.action_archive()
            else:
                inventory.message_post(
                    body=_("Warning: Inventory has expired but still contains items")
                )


class TempInventoryMovement(models.Model):
    """Temporary Inventory Movement Tracking"""

    _name = "temp.inventory.movement"
    _description = "Temporary Inventory Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"
    _rec_name = "display_name"

    inventory_id = fields.Many2one(
        "temp.inventory",
        string="Inventory",
        required=True,
        ondelete="cascade",
        help="Associated temporary inventory",
    )
    movement_type = fields.Selection(
        [
            ("in", "Items In"),
            ("out", "Items Out"),
            ("transfer", "Transfer"),
            ("adjustment", "Adjustment"),
        ],
        string="Movement Type",
        required=True,
        default="in",
        help="Type of inventory movement",
    )
    date = fields.Datetime(
        string="Movement Date",
        required=True,
        default=fields.Datetime.now,
        help="When movement occurred",
    )
    quantity = fields.Integer(
        string="Quantity", required=True, default=1, help="Number of items moved"
    )
    user_id = fields.Many2one(
        "res.users",
        string="Performed By",
        required=True,
        default=lambda self: self.env.user,
        help="User who performed the movement",
    )
    notes = fields.Text(string="Notes", help="Additional notes about the movement")
    document_id = fields.Many2one(
        "records.document",
        string="Related Document",
        help="Document involved in this movement",
    )
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Container involved in this movement",
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for movement",
    )

    @api.depends("movement_type", "quantity", "date")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            movement_label = dict(record._fields["movement_type"].selection)[
                record.movement_type
            ]
            record.display_name = f"{movement_label}: {record.quantity} items"


class TempInventoryAudit(models.Model):
    """Temporary Inventory Audit Trail"""

    _name = "temp.inventory.audit"
    _description = "Temporary Inventory Audit"
    _order = "date desc"
    _rec_name = "display_name"

    inventory_id = fields.Many2one(
        "temp.inventory",
        string="Inventory",
        required=True,
        ondelete="cascade",
        help="Associated temporary inventory",
    )
    date = fields.Datetime(
        string="Audit Date",
        required=True,
        default=fields.Datetime.now,
        help="When audit event occurred",
    )
    event_type = fields.Selection(
        [
            ("created", "Created"),
            ("modified", "Modified"),
            ("accessed", "Accessed"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        string="Event Type",
        required=True,
        help="Type of audit event",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="User who triggered the event",
    )
    details = fields.Text(
        string="Details", help="Detailed information about the audit event"
    )
    ip_address = fields.Char(string="IP Address", help="IP address of the user")
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for audit record",
    )

    @api.depends("event_type", "user_id", "date")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            event_label = dict(record._fields["event_type"].selection)[
                record.event_type
            ]
            user_name = record.user_id.name if record.user_id else "Unknown"
            record.display_name = f"{event_label} by {user_name}"
