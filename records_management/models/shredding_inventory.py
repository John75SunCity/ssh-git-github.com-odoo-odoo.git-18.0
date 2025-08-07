# -*- coding: utf-8 -*-
"""
Shredding Inventory Item
"""

from odoo import models, fields, api, _

class ShreddingInventoryBatch(models.Model):
    """
    Shredding Inventory Batch - For batch processing of multiple items
    """

    _name = "shredding.inventory.batch"
    _description = "Shredding Inventory Batch"
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

class ShreddingPicklistItem(models.Model):
    """
    Shredding Picklist Item - Items picked from inventory for shredding
    """

    _name = "shredding.picklist.item"
    _description = "Shredding Picklist Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "display_name"

    # Core fields
    name = fields.Char(string="Item Name", required=True, tracking=True)
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    sequence = fields.Integer(string="Sequence", default=10)

    # Workflow relationships
    container_id = fields.Many2one("records.container", string="Container")
    document_id = fields.Many2one("records.document", string="Document")
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")
    location_id = fields.Many2one("records.location", string="Location")

    # Picking details
    picked_by = fields.Many2one("res.users", string="Picked By")
    picked_date = fields.Datetime(string="Picked Date")

    # Status tracking
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_pickup", "Pending Pickup"),
            ("picked", "Picked"),
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Common fields

    @api.depends("name", "container_id", "document_id")
    def _compute_display_name(self):
        for record in self:
            if record.container_id:
                record.display_name = (
                    f"{record.name} (Container: {record.container_id.name})"
                )
            elif record.document_id:
                record.display_name = (
                    f"{record.name} (Document: {record.document_id.name})"
                )
            else:
                record.display_name = record.name or _("New Item")

    def action_mark_picked(self):
        """Mark item as picked"""
        self.write(
            {
                "status": "picked",
                "picked_by": self.env.user.id,
                "picked_date": fields.Datetime.now(),
            }
        )

    def action_mark_not_found(self):
        """Mark item as not found"""
        self.write({"status": "not_found"})

    def action_confirm(self):
        """Confirm the record"""
        self.write({"status": "pending_pickup"})

    def action_done(self):
        """Mark as done"""
        self.write({"status": "picked"})
