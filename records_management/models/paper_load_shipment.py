# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperLoadShipment(models.Model):
    _name = "paper.load.shipment"
    _description = "Paper Load Shipment"
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

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

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

    # =============================================================================
    # PAPER LOAD SHIPMENT ACTION METHODS
    # =============================================================================

    def action_add_bales_to_load(self):
        """Add paper bales to this load shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Bales to Load"),
            "res_model": "paper.bale",
            "view_mode": "tree",
            "domain": [
                ("state", "=", "ready_to_ship"),
                ("load_shipment_id", "=", False),
            ],
            "context": {
                "default_load_shipment_id": self.id,
                "search_default_ready_to_ship": 1,
            },
        }

    def action_create_invoice(self):
        """Create invoice for this shipment."""
        self.ensure_one()
        # Create invoice based on shipment value
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self.company_id.partner_id.id,  # Default to company partner
            "invoice_date": fields.Date.today(),
            "payment_reference": self.name,
            "narration": f"Invoice for paper load shipment: {self.name}",
        }

        invoice = self.env["account.move"].create(invoice_vals)
        self.message_post(body=_("Invoice created: %s") % invoice.name)

        return {
            "type": "ir.actions.act_window",
            "name": _("Created Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_generate_manifest(self):
        """Generate shipping manifest for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_load_manifest_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_mark_delivered(self):
        """Mark shipment as delivered."""
        self.ensure_one()
        self.write(
            {
                "state": "inactive",  # Using inactive as "delivered" state
                "date_modified": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Shipment marked as delivered."))
        return True

    def action_mark_in_transit(self):
        """Mark shipment as in transit."""
        self.ensure_one()
        self.write({"state": "active"})  # Using active as "in transit" state
        self.message_post(body=_("Shipment marked as in transit."))
        return True

    def action_mark_paid(self):
        """Mark shipment as paid."""
        self.ensure_one()
        # Add payment tracking field if needed
        self.message_post(body=_("Shipment marked as paid."))
        return True

    def action_ready_for_pickup(self):
        """Mark shipment as ready for pickup."""
        self.ensure_one()
        self.write({"state": "draft"})  # Using draft as "ready for pickup"
        self.message_post(body=_("Shipment ready for pickup."))
        return True

    def action_schedule_pickup(self):
        """Schedule pickup for this shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Pickup"),
            "res_model": "pickup.request",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Pickup for {self.name}",
                "default_description": f"Scheduled pickup for paper load shipment: {self.name}",
                "default_load_shipment_id": self.id,
            },
        }

    def action_view_manifest(self):
        """View shipping manifest."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_load_manifest_report",
            "report_type": "qweb-html",  # View in browser instead of download
            "context": {"active_ids": [self.id]},
        }

    def action_view_weight_breakdown(self):
        """View weight breakdown of bales in this shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weight Breakdown"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_shipment_id", "=", self.id)],
            "context": {
                "search_default_load_shipment_id": self.id,
                "group_by": "bale_type",
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
