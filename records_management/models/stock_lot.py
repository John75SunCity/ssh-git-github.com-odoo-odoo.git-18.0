# -*- coding: utf-8 -*-
"""
Stock Lot Attribute
"""

from odoo import models, fields, api, _

class StockLot(models.Model):
    """
    Stock Lot Extensions for Records Management
    """

    _inherit = "stock.lot"

    # Records management specific fields
    records_tracking = fields.Boolean(string="Records Tracking", default=False)
    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count"
    )
    destruction_eligible = fields.Boolean(
        string="Eligible for Destruction", default=False
    )
    quality_status = fields.Selection(
        [
            ("pending", "Pending Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Quality Status",
        default="pending",
    )

    @api.depends("name")
    def _compute_document_count(self):
        """Compute number of documents associated with this lot."""
        for record in self:
            record.document_count = self.env["records.document"].search_count(
                [("lot_id", "=", record.id)]
            )

    # =============================================================================
    # STOCK LOT ACTION METHODS
    # =============================================================================

    def action_print_label(self):
        """Print lot identification label."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.stock_lot_label_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_quality_check(self):
        """Perform quality check on lot."""
        self.ensure_one()
        # Create quality check activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Quality Check: {self.name}",
            note="Perform quality assessment including condition review and compliance verification.",
            user_id=self.env.user.id,
        )
        self.message_post(body="Quality check scheduled.")
        return True

    def action_track_history(self):
        """Track movement history of this lot."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lot Movement History",
            "res_model": "stock.move.line",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "search_default_lot_id": self.id,
                "group_by": "date",
            },
        }

    def action_view_location(self):
        """View current location of this lot."""
        self.ensure_one()
        quants = self.env["stock.quant"].search(
            [("lot_id", "=", self.id), ("quantity", ">", 0)]
        )
        if not quants:
            from odoo.exceptions import UserError

            raise UserError("No current location found for this lot.")

        return {
            "type": "ir.actions.act_window",
            "name": "Current Location",
            "res_model": "stock.location",
            "res_id": quants[0].location_id.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_move_details(self):
        """View detailed move information."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Move Details",
            "res_model": "stock.move",
            "view_mode": "tree,form",
            "domain": [("move_line_ids.lot_id", "=", self.id)],
            "context": {
                "search_default_lot_id": self.id,
            },
        }

    def action_view_movements(self):
        """View all movements for this lot."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lot Movements",
            "res_model": "stock.move.line",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "search_default_lot_id": self.id,
                "group_by": "picking_id",
            },
        }

    def action_view_quality_checks(self):
        """View quality checks for this lot."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Quality Checks",
            "res_model": "quality.check",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "default_lot_id": self.id,
                "search_default_lot_id": self.id,
            },
        }

    def action_view_quality_details(self):
        """View detailed quality information."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Quality Details",
            "res_model": "stock.lot",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "focus_field": "quality_status",
            },
        }

    def action_view_quants(self):
        """View stock quants for this lot."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Stock Quantities",
            "res_model": "stock.quant",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "search_default_lot_id": self.id,
                "group_by": "location_id",
            },
        }

class StockLotAttribute(models.Model):
    """
    Stock Lot Attribute
    """

    _name = "stock.lot.attribute"
    _description = "Stock Lot Attribute"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
