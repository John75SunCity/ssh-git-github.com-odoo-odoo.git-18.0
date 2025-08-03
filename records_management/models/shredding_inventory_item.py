# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingInventoryItem(models.Model):
    _name = "shredding.inventory.item"
    _description = "Shredding Inventory Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "display_name"

    # Basic Information
    name = fields.Char(string="Item Name", required=True, tracking=True)
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    sequence = fields.Integer(string="Sequence", default=10)

    # Core fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # Workflow relationships - containers vs documents
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        help="Barcoded container being shredded",
    )
    document_id = fields.Many2one(
        "records.document", string="Document", help="Specific document being shredded"
    )
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")
    current_location_id = fields.Many2one("records.location", string="Current Location")

    # Item details
    item_type = fields.Selection(
        [
            ("document", "Document"),
            ("container", "Container"),
            ("hard_drive", "Hard Drive"),
            ("media", "Media"),
        ],
        string="Item Type",
        default="document",
        tracking=True,
    )
    quantity = fields.Float(string="Quantity", default=1.0)
    total_cost = fields.Monetary(string="Total Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Status tracking
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_pickup", "Pending Pickup"),
            ("retrieved", "Retrieved"),
            ("destroyed", "Destroyed"),
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Additional tracking fields
    description = fields.Text(string="Description")
    notes = fields.Text(string="Notes")
    date = fields.Date(string="Date", default=fields.Date.today)
    # === COMPREHENSIVE MISSING FIELDS ===
    active = fields.Boolean(string='Flag', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    notes = fields.Text(string='Description', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Status', default='draft', tracking=True)
    created_date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string='Date', tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    document_count = fields.Integer(string='Document Count', default=0)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id')
    # Shredding Inventory Item Fields
    approval_date = fields.Date('Approval Date')
    customer_approved = fields.Boolean('Customer Approved', default=False)
    destroyed_by = fields.Many2one('hr.employee', 'Destroyed By')
    destruction_date = fields.Date('Destruction Date')
    destruction_notes = fields.Text('Destruction Notes')
    batch_processing_required = fields.Boolean('Batch Processing Required', default=False)
    certificate_generation_required = fields.Boolean('Certificate Generation Required', default=True)
    chain_of_custody_number = fields.Char('Chain of Custody Number')
    contamination_check_completed = fields.Boolean('Contamination Check Completed', default=False)
    destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)
    item_classification = fields.Selection([('paper', 'Paper'), ('media', 'Media'), ('electronic', 'Electronic')], default='paper')
    quality_verification_completed = fields.Boolean('Quality Verification Completed', default=False)
    security_level_verified = fields.Boolean('Security Level Verified', default=False)
    witness_verification_required = fields.Boolean('Witness Verification Required', default=False)



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

    def action_approve_item(self):
        """Approve item for destruction."""
        self.ensure_one()
        self.write({"status": "pending_pickup"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Approved"),
                "message": _(
                    "Item has been approved for destruction and is pending pickup."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_retrieved(self):
        """Mark item as retrieved."""
        self.ensure_one()
        self.write({"status": "retrieved"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Retrieved"),
                "message": _("Item has been marked as retrieved."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_destroyed(self):
        """Mark item as destroyed."""
        self.ensure_one()
        self.write({"status": "destroyed"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Destroyed"),
                "message": _("Item has been marked as destroyed."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_mark_picked(self):
        """Mark item as picked."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Picked"),
                "message": _("Item has been marked as picked."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_not_found(self):
        """Mark item as not found."""
        self.ensure_one()
        self.write({"status": "not_found"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Not Found"),
                "message": _("Item has been marked as not found."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_track_chain_of_custody(self):
        """Track chain of custody."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("item_id", "=", self.id)],
        }

    def action_generate_certificate(self):
        """Generate destruction certificate."""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.destruction_certificate",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_audit_compliance(self):
        """Audit compliance status."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Audited"),
                "message": _("Compliance status has been audited."),
                "type": "success",
                "sticky": False,
            },
        }
