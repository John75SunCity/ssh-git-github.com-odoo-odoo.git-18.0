# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ServiceItem(models.Model):
    _name = "service.item"
    _description = "Service Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Service Item Name", required=True, tracking=True, index=True
    ),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    ),
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ]),
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    )
    service_type = fields.Selection(
        [
            ("pickup", "Pickup Service"),
            ("shredding", "Shredding Service"),
            ("destruction", "Destruction Service"),
            ("storage", "Storage Service"),
            ("retrieval", "Document Retrieval"),
            ("transport", "Transport Service"),
            ("scanning", "Scanning Service"),
            ("consultation", "Consultation Service"),
        ]),
        string="Service Type",
        required=True,
    )

    category = fields.Selection(
        [
            ("equipment", "Equipment"),
            ("vehicle", "Vehicle"),
            ("container", "Container"),
            ("tool", "Tool"),
            ("software", "Software"),
            ("personnel", "Personnel"),
        ]),
        string="Category",
        required=True,
    )

    # ============================================================================
    # ITEM SPECIFICATIONS
    # ============================================================================
    )
    model_number = fields.Char(string="Model Number"),
    serial_number = fields.Char(string="Serial Number", index=True)
    manufacturer = fields.Char(string="Manufacturer"),
    purchase_date = fields.Date(string="Purchase Date")
    warranty_expiry = fields.Date(string="Warranty Expiry")

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    purchase_cost = fields.Float(string="Purchase Cost", digits="Product Price"),
    current_value = fields.Float(string="Current Value", digits="Product Price")
    maintenance_cost = fields.Float(string="Maintenance Cost", digits="Product Price"),
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # OPERATIONAL STATUS
    # ============================================================================
    )
    location_id = fields.Many2one("records.location", string="Current Location"),
    assigned_user_id = fields.Many2one("res.users", string="Assigned To")
    department_id = fields.Many2one("records.department", string="Department"),
    last_maintenance = fields.Date(string="Last Maintenance")
    next_maintenance = fields.Date(string="Next Maintenance"),
    maintenance_interval = fields.Integer(
        string="Maintenance Interval (days)", default=90
    )

    # ============================================================================
    # CAPACITY & PERFORMANCE
    # ============================================================================
    )
    capacity = fields.Float(string="Capacity"),
    capacity_unit = fields.Selection(
        [
            ("kg", "Kilograms"),
            ("pieces", "Pieces"),
            ("hours", "Hours"),
            ("boxes", "Boxes"),
            ("pages", "Pages"),
        ]),
        string="Capacity Unit",
        default="pieces",
    )

    )

    utilization_rate = fields.Float(string="Utilization Rate (%)", default=0.0)
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ]),
        string="Efficiency Rating",
        default="good",
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    )
    service_request_ids = fields.One2many(
        "portal.request", "service_item_id", string="Service Requests"
    # REMOVED: maintenance_log_ids - replaced by standard maintenance.request system

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    ),
    description = fields.Text(string="Description")
    specifications = fields.Text(string="Technical Specifications"),
    operating_instructions = fields.Text(string="Operating Instructions")
    safety_notes = fields.Text(string="Safety Notes")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Note: Removed pos_wizard_id field - Model to TransientModel relationships are forbidden

    # # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )    @api.depends("purchase_date", "warranty_expiry")
    def _compute_warranty_status(self):
        today = fields.Date.today()
        for item in self:
            if item.warranty_expiry:
                if item.warranty_expiry >= today:
                    item.warranty_status = "active"
                else:
                    item.warranty_status = "expired"
            else:
                item.warranty_status = "unknown"

    warranty_status = fields.Selection(
        [("active", "Active"), ("expired", "Expired"), ("unknown", "Unknown")],
        string="Warranty Status",
        compute="_compute_warranty_status",
        store=True,
    )

    @api.depends("last_maintenance", "maintenance_interval")
    def _compute_maintenance_due(self):
        )
        today = fields.Date.today()
        for item in self:
            if item.last_maintenance and item.maintenance_interval:
                next_due = item.last_maintenance + fields.Date.to_date(
                    f"{item.maintenance_interval} days"
                )
                item.maintenance_due = next_due <= today
            else:
                item.maintenance_due = False

    maintenance_due = fields.Boolean(
        string="Maintenance Due", compute="_compute_maintenance_due", store=True
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_in_use(self):
        """Mark service item as in use"""
        self.write({"state": "in_use"})

    def action_schedule_maintenance(self):
        """Schedule maintenance for service item"""
        self.write({"state": "maintenance"})
        return {
            "type": "ir.actions.act_window",
            "name": "Schedule Maintenance",
            "res_model": "maintenance.request",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Maintenance - {self.name}",
                "default_request_type": "preventive",
            },
        }

    def action_retire_item(self):
        """Retire service item"""
        self.write({"state": "retired", "active": False})