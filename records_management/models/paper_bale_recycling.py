# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperBaleRecycling(models.Model):
    _name = "paper.bale.recycling"
    _description = "Paper Bale Recycling"
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

    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - PAPER BALE RECYCLING ENHANCEMENT
    # ============================================================================

    # Framework Integration Fields (required by mail.thread)
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
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # Business Process Fields
    bale_number = fields.Char(
        string="Bale Number",
        required=True,
        index=True,
        tracking=True,
        help="Unique identifier for the paper bale",
    )

    contamination = fields.Float(
        string="Contamination Level (%)",
        digits=(5, 2),
        tracking=True,
        help="Percentage of contamination in the bale",
    )

    contamination_notes = fields.Text(
        string="Contamination Notes",
        help="Details about contamination found in the bale",
    )

    gps_coordinates = fields.Char(
        string="GPS Coordinates",
        help="GPS location where bale was collected or processed",
    )

    load_number = fields.Char(
        string="Load Number",
        tracking=True,
        help="Reference number for the load this bale belongs to",
    )

    # Production and Quality Management
    paper_grade = fields.Selection(
        [
            ("white", "White Paper"),
            ("mixed", "Mixed Paper"),
            ("cardboard", "Cardboard"),
        ],
        string="Paper Grade",
        required=True,
        default="mixed",
        tracking=True,
        help="Classification of paper type for recycling processing",
    )

    production_date = fields.Date(
        string="Production Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when the paper bale was created at our facility",
    )

    # Mobile and Service Integration
    mobile_entry = fields.Boolean(
        string="Mobile Entry",
        default=False,
        help="Indicates if this entry was created via mobile device",
    )

    # Weight and Measurement
    weight_net = fields.Float(
        string="Net Weight (lbs)",
        digits=(10, 2),
        help="Net weight of the paper bale",
    )

    # Additional Quality Fields
    quality_grade = fields.Selection(
        [
            ("premium", "Premium"),
            ("standard", "Standard"),
            ("economy", "Economy"),
            ("reject", "Reject"),
        ],
        string="Quality Grade",
        default="standard",
        tracking=True,
    )

    moisture_content = fields.Float(
        string="Moisture Content (%)",
        digits=(5, 2),
        help="Moisture percentage in the bale",
    )

    # Process Fields
    processing_facility = fields.Char(
        string="Processing Facility", help="Facility where the bale was processed"
    )

    batch_id = fields.Char(
        string="Batch ID", help="Batch identifier for quality tracking"
    )

    # Customer and Location
    collection_location = fields.Char(
        string="Collection Location", help="Location where materials were collected"
    )

    destination_facility = fields.Char(
        string="Destination Facility",
        help="Facility where bale will be sent for processing",
    )

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

    # Action Methods
    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    def action_assign_to_load(self):
        """Assign paper bale to a shipping load."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active paper bales can be assigned to loads."))

        # Update state and notes
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nAssigned to load on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create activity for load assignment
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Paper bale assigned to load: %s") % self.name,
            note=_(
                "Paper bale has been assigned to shipping load and is ready for transport."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Paper bale assigned to shipping load: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Assign to Load"),
            "res_model": "load",
            "view_mode": "tree,form",
            "target": "current",
            "context": {
                "default_name": _("Load for: %s") % self.name,
                "search_default_active": True,
            },
        }

    def action_mark_delivered(self):
        """Mark paper bale as delivered to recycling facility."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot mark archived paper bale as delivered."))

        # Update state and notes
        self.write(
            {
                "state": "inactive",  # Delivered state
                "notes": (self.notes or "")
                + _("\nDelivered to recycling facility on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create delivery confirmation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Paper bale delivered: %s") % self.name,
            note=_("Paper bale has been successfully delivered to recycling facility."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Paper bale delivered to recycling facility: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Delivery Confirmed"),
                "message": _(
                    "Paper bale %s has been successfully delivered to the recycling facility."
                )
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_paid(self):
        """Mark paper bale payment as received."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot mark payment for archived paper bale."))

        # Update notes with payment information
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nPayment received on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create payment confirmation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Payment received for paper bale: %s") % self.name,
            note=_(
                "Payment has been received and processed for this paper bale recycling."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Payment received for paper bale: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Payment Processing"),
            "res_model": "account.payment",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_payment_type": "inbound",
                "default_communication": _("Payment for paper bale: %s") % self.name,
                "default_ref": self.name,
            },
        }

    def action_ready_to_ship(self):
        """Mark paper bale as ready for shipping."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active paper bales can be marked ready to ship."))

        # Update notes with ready status
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nMarked ready to ship on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create shipping readiness activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Paper bale ready to ship: %s") % self.name,
            note=_(
                "Paper bale is processed and ready for shipping to recycling facility."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Paper bale marked ready to ship: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Ready to Ship"),
                "message": _(
                    "Paper bale %s is now ready for shipping to the recycling facility."
                )
                % self.name,
                "type": "info",
                "sticky": False,
            },
        }

    def action_ship_bale(self):
        """Process shipping of paper bale."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active paper bales can be shipped."))

        # Update notes with shipping information
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nShipped on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create shipping activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Paper bale shipped: %s") % self.name,
            note=_(
                "Paper bale has been shipped and is in transit to recycling facility."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Paper bale shipped to recycling facility: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shipping Documentation"),
            "res_model": "paper.bale.recycling",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "form_view_initial_mode": "edit",
            },
        }

    def action_store_bale(self):
        """Store paper bale in warehouse facility."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot store archived paper bale."))

        # Update state to stored (active) and notes
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nStored in warehouse on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create storage activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Paper bale stored: %s") % self.name,
            note=_("Paper bale has been properly stored in warehouse facility."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Paper bale stored in warehouse: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Warehouse Storage"),
            "res_model": "stock.location",
            "view_mode": "tree,form",
            "target": "current",
            "context": {
                "search_default_internal": True,
                "default_usage": "internal",
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
