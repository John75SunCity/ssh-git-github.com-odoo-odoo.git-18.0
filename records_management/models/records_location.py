# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsLocation(models.Model):
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Location Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Location Code", required=True, index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Location Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # PHYSICAL LOCATION DETAILS
    # ============================================================================
    building = fields.Char(string="Building", tracking=True)
    floor = fields.Char(string="Floor", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    aisle = fields.Char(string="Aisle", tracking=True)
    rack = fields.Char(string="Rack", tracking=True)
    shelf = fields.Char(string="Shelf", tracking=True)
    position = fields.Char(string="Position", tracking=True)

    # Address Information
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state = fields.Char(string="State/Province")
    zip = fields.Char(string="ZIP Code")
    country_id = fields.Many2one("res.country", string="Country")

    # ============================================================================
    # CAPACITY & SPECIFICATIONS
    # ============================================================================
    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("vault", "Vault"),
            ("archive", "Archive"),
            ("temporary", "Temporary"),
            ("offsite", "Off-site"),
        ],
        string="Location Type",
        required=True,
        default="warehouse",
        tracking=True,
    )

    storage_capacity = fields.Integer(string="Storage Capacity (boxes)")
    current_utilization = fields.Integer(
        string="Current Utilization", compute="_compute_current_utilization"
    )
    available_spaces = fields.Integer(
        string="Available Spaces", compute="_compute_available_spaces"
    )
    utilization_percentage = fields.Float(
        string="Utilization %", compute="_compute_utilization_percentage"
    )

    # Physical constraints
    max_weight_capacity = fields.Float(string="Max Weight Capacity (lbs)")
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled", default=False
    )
    humidity_controlled = fields.Boolean(string="Humidity Controlled", default=False)
    fire_suppression = fields.Boolean(string="Fire Suppression", default=False)
    security_level = fields.Selection(
        [("standard", "Standard"), ("high", "High"), ("maximum", "Maximum")],
        string="Security Level",
        default="standard",
        tracking=True,
    )

    # ============================================================================
    # ACCESS & SECURITY
    # ============================================================================
    access_restrictions = fields.Text(string="Access Restrictions")
    authorized_users = fields.Many2many("res.users", string="Authorized Users")
    requires_escort = fields.Boolean(string="Requires Escort", default=False)
    security_camera = fields.Boolean(string="Security Camera", default=False)
    access_card_required = fields.Boolean(string="Access Card Required", default=False)

    # ============================================================================
    # OPERATIONAL STATUS
    # ============================================================================
    operational_status = fields.Selection(
        [
            ("active", "Active"),
            ("maintenance", "Under Maintenance"),
            ("inactive", "Inactive"),
            ("full", "At Capacity"),
        ],
        string="Operational Status",
        default="active",
        tracking=True,
    )

    availability_schedule = fields.Text(string="Availability Schedule")
    last_inspection_date = fields.Date(string="Last Inspection Date")
    next_inspection_date = fields.Date(string="Next Inspection Date")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Records and containers at this location
    container_ids = fields.One2many(
        "records.container", "location_id", string="Records Containers"
    )
    parent_location_id = fields.Many2one("records.location", string="Parent Location")
    child_location_ids = fields.One2many(
        "records.location", "parent_location_id", string="Child Locations"
    )

    # Mail framework fields
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("model", "=", "records.location")],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", "records.location")],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", "records.location")],
    )

    # ============================================================================
    # COMPUTED FIELDS

    # ============================================================================
    @api.depends("container_ids")
    def _compute_current_utilization(self):
        for record in self:
            record.current_utilization = len(record.container_ids)

    @api.depends("storage_capacity", "current_utilization")
    def _compute_available_spaces(self):
        for record in self:
            if record.storage_capacity > 0:
                record.available_spaces = max(
                    0, record.storage_capacity - record.current_utilization
                )
            else:
                record.available_spaces = 0

    @api.depends("current_utilization", "storage_capacity")
    def _compute_utilization_percentage(self):
        for record in self:
            if record.storage_capacity > 0:
                record.utilization_percentage = (
                    record.current_utilization / record.storage_capacity
                ) * 100
            else:
                record.utilization_percentage = 0.0

    @api.depends("child_location_ids")
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.child_location_ids)

    @api.depends("operational_status", "storage_capacity", "current_utilization")
    def _compute_is_available(self):
        for record in self:
            record.is_available = (
                record.operational_status == "active"
                and record.current_utilization < record.storage_capacity
            )

    child_count = fields.Integer(compute="_compute_child_count", string="Child Count")
    is_available = fields.Boolean(
        compute="_compute_is_available", string="Available for Storage"
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("records.location") or "LOC/"
                )
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Records Containers",
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("location_id", "=", self.id)],
            "context": {"default_location_id": self.id},
        }

    def action_location_report(self):
        """Generate location utilization and capacity report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_utilization_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_maintenance_mode(self):
        self.ensure_one()
        self.write({"operational_status": "maintenance"})

    def action_reserve_space(self):
        """Open a form to schedule an inspection if the location is available for reservation."""
        self.ensure_one()
        if not self.is_available:
            raise UserError(_("Location is not available for reservations."))
        # Reservation logic to be implemented as needed
        return {
            "type": "ir.actions.act_window",
            "name": "Schedule Inspection",
            "res_model": "records.location.inspection",
            "view_mode": "form",
            "target": "new",
            "context": {"default_location_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_full_location_path(self):
        """Return full hierarchical path of location"""
        self.ensure_one()
        path = [self.name]
        current = self.parent_location_id
        while current:
            path.insert(0, current.name)
            current = current.parent_location_id
        return " > ".join(path)

    def get_available_capacity(self):
        """Return available storage capacity"""
        self.ensure_one()
        return max(0, self.storage_capacity - self.current_utilization)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("storage_capacity")
    def _check_storage_capacity(self):
        for record in self:
            if record.storage_capacity < 0:
                raise ValidationError(_("Storage capacity cannot be negative."))

    @api.constrains("parent_location_id")
    def _check_parent_location(self):
        for record in self:
            if record.parent_location_id:
                if record.parent_location_id == record:
                    raise ValidationError(_("Location cannot be its own parent."))

    @api.constrains("code")
    def _check_code_uniqueness(self):
        for record in self:
            if record.code:
                existing = self.search(
                    [("code", "=", record.code), ("id", "!=", record.id)],
                    limit=1
                )
                if existing:
                    raise ValidationError(_("Location code must be unique."))
