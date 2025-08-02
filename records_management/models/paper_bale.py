# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PaperBale(models.Model):
    _name = "paper.bale"
    _description = "Paper Bale"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Bale Number", required=True)
    weight = fields.Float(string="Weight (kg)")
    creation_date = fields.Date(string="Creation Date", default=fields.Date.today)
    load_id = fields.Many2one("load", string="Load")
    recycling_facility = fields.Char(string="Recycling Facility")
    state = fields.Selection(
        [("created", "Created"), ("shipped", "Shipped"), ("recycled", "Recycled")],
        default="created",
    )

    # Additional fields for comprehensive bale management
    load_shipment_id = fields.Many2one("paper.load.shipment", string="Load Shipment")
    bale_type = fields.Selection(
        [
            ("mixed", "Mixed Paper"),
            ("cardboard", "Cardboard"),
            ("newspaper", "Newspaper"),
            ("office", "Office Paper"),
        ],
        string="Bale Type",
        default="mixed",
    )
    storage_location = fields.Char(string="Storage Location")
    trailer_id = fields.Many2one("records.vehicle", string="Trailer")
    quality_grade = fields.Selection(
        [("a", "Grade A"), ("b", "Grade B"), ("c", "Grade C")], string="Quality Grade"
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # =============================================================================
    # PAPER BALE ACTION METHODS
    # =============================================================================

    def action_load_trailer(self):
        """Load bale onto trailer."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Select Trailer",
            "res_model": "records.vehicle",
            "view_mode": "tree",
            "domain": [("vehicle_type", "=", "trailer"), ("state", "=", "available")],
            "context": {
                "default_bale_id": self.id,
                "search_default_available": 1,
            },
        }

    def action_move_to_storage(self):
        """Move bale to storage location."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Move to Storage",
            "res_model": "stock.picking",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_type_id": self.env.ref(
                    "stock.picking_type_internal"
                ).id,
                "default_origin": self.name,
                "default_note": f"Moving bale {self.name} to storage",
            },
        }

    def action_print_label(self):
        """Print bale identification label."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_bale_label_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_quality_inspection(self):
        """Perform quality inspection of bale."""
        self.ensure_one()
        # Create quality check activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Quality Inspection: {self.name}",
            note="Perform comprehensive quality inspection including contamination check, moisture content, and grade assessment.",
            user_id=self.user_id.id,
        )
        self.message_post(body="Quality inspection scheduled.")
        return True

    def action_view_inspection_details(self):
        """View quality inspection details."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Inspection Details",
            "res_model": "quality.check",
            "view_mode": "tree,form",
            "domain": [("product_id.name", "ilike", self.name)],
            "context": {
                "search_default_product_id": self.name,
            },
        }

    def action_view_source_documents(self):
        """View source documents that contributed to this bale."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Source Documents",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {
                "default_bale_id": self.id,
                "search_default_bale_id": self.id,
            },
        }

    def action_view_trailer_info(self):
        """View trailer information for this bale."""
        self.ensure_one()
        if not self.trailer_id:
            from odoo.exceptions import UserError

            raise UserError("No trailer assigned to this bale.")

        return {
            "type": "ir.actions.act_window",
            "name": "Trailer Information",
            "res_model": "records.vehicle",
            "res_id": self.trailer_id.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_weight_history(self):
        """View weight measurement history."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Weight History",
            "res_model": "stock.quant",
            "view_mode": "tree,form",
            "domain": [("product_id.name", "ilike", self.name)],
            "context": {
                "search_default_product_id": self.name,
                "group_by": "in_date",
            },
        }

    def action_weigh_bale(self):
        """Record bale weight measurement."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Weigh Bale",
            "res_model": "paper.bale",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_weight": self.weight,
                "focus_field": "weight",
            },
        }
