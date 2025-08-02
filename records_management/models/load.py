# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Load(models.Model):
    _name = "load"
    _description = "Load"
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
    # LOAD ACTION METHODS
    # =============================================================================

    def action_cancel(self):
        """Cancel the load."""
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Load cancelled."))
        return True

    def action_mark_sold(self):
        """Mark load as sold."""
        self.ensure_one()
        self.write({"state": "archived"})  # Using archived as "sold" state
        self.message_post(body=_("Load marked as sold."))
        return True

    def action_prepare_load(self):
        """Prepare load for shipping."""
        self.ensure_one()
        self.write({"state": "draft"})  # Using draft as "preparing" state
        self.message_post(body=_("Load preparation started."))

        # Create preparation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Prepare Load: {self.name}",
            note="Prepare load for shipping including bale verification, weight confirmation, and documentation.",
            user_id=self.user_id.id,
        )
        return True

    def action_ship_load(self):
        """Ship the load."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active loads can be shipped."))

        self.write({"state": "inactive"})  # Using inactive as "shipped" state
        self.message_post(body=_("Load shipped successfully."))
        return True

    def action_start_loading(self):
        """Start loading process."""
        self.ensure_one()
        self.write({"state": "active"})
        self.message_post(body=_("Loading process started."))
        return True

    def action_view_bales(self):
        """View bales in this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Load Bales"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {
                "default_load_id": self.id,
                "search_default_load_id": self.id,
            },
        }

    def action_view_revenue_report(self):
        """View revenue report for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.load_revenue_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_view_weight_tickets(self):
        """View weight tickets for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weight Tickets"),
            "res_model": "stock.picking",
            "view_mode": "tree,form",
            "domain": [("origin", "ilike", self.name)],
            "context": {
                "search_default_origin": self.name,
                "group_by": "date",
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
