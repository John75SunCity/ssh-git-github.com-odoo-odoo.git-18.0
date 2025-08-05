# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventory(models.Model):
    _name = "customer.inventory"
    _description = "Customer Inventory"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Standard message/activity fields
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", auto_join=True
    )
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities", auto_join=True
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", auto_join=True
    )
    action_confirm_report = fields.Char(string="Action Confirm Report")
    action_generate_pdf_report = fields.Char(string="Action Generate Pdf Report")
    action_send_to_customer = fields.Char(string="Action Send To Customer")
    action_view_boxes = fields.Char(string="Action View Boxes")
    action_view_documents = fields.Char(string="Action View Documents")
    action_view_locations = fields.Char(string="Action View Locations")
    active_locations = fields.Char(string="Active Locations")
    container_ids = fields.One2many(
        "records.container",
        string="Containers",
        compute="_compute_container_ids",
        help="Containers belonging to this customer",
    )
    boxes = fields.Char(string="Boxes")
    button_box = fields.Char(string="Button Box")
    card = fields.Char(string="Card")
    confirmed = fields.Boolean(string="Confirmed", default=False)
    context = fields.Char(string="Context")
    created_date = fields.Date(string="Created Date")
    customer_id = fields.Many2one(
        "res.partner", string="Customer Id", domain=[("is_company", "=", True)]
    )
    document_ids = fields.One2many(
        "records.document",
        string="Document Ids",
        compute="_compute_document_ids",
        help="Documents belonging to this customer",
    )
    document_type_id = fields.Many2one(
        "records.document.type", string="Document Type Id"
    )
    documents = fields.Char(string="Documents")
    draft = fields.Char(string="Draft")
    group_by_customer = fields.Char(string="Group By Customer")
    group_by_date = fields.Date(string="Group By Date")
    group_by_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Group By Status",
        default="draft",
    )
    group_by_volume = fields.Char(string="Group By Volume")
    help = fields.Char(string="Help")
    large_volume = fields.Char(string="Large Volume")
    last_quarter = fields.Char(string="Last Quarter")
    location_id = fields.Many2one("records.location", string="Location Id")
    medium_volume = fields.Char(string="Medium Volume")
    notes = fields.Char(string="Notes")
    report_date = fields.Date(string="Report Date")
    res_model = fields.Char(string="Res Model")
    search_view_id = fields.Many2one("ir.ui.view", string="Search View")
    sent = fields.Char(string="Sent")
    small_volume = fields.Char(string="Small Volume")
    status = fields.Selection(
        [("new", "New"), ("in_progress", "In Progress"), ("completed", "Completed")],
        string="Status",
        default="new",
    )
    stored_date = fields.Date(string="Stored Date")
    this_month = fields.Char(string="This Month")
    total_boxes = fields.Char(string="Total Boxes", compute="_compute_total_boxes")
    total_documents = fields.Char(
        string="Total Documents", compute="_compute_total_documents"
    )
    very_large_volume = fields.Char(string="Very Large Volume")
    view_mode = fields.Char(string="View Mode")
    volume_category = fields.Char(string="Volume Category")

    @api.depends("customer_id")
    def _compute_container_ids(self):
        """Compute containers belonging to this customer"""
        for record in self:
            if record.customer_id:
                containers = self.env["records.container"].search(
                    [("partner_id", "=", record.customer_id.id)]
                )
                record.container_ids = containers
            else:
                record.container_ids = False

    @api.depends("customer_id")
    def _compute_document_ids(self):
        """Compute documents belonging to this customer"""
        for record in self:
            if record.customer_id:
                documents = self.env["records.document"].search(
                    [("partner_id", "=", record.customer_id.id)]
                )
                record.document_ids = documents
            else:
                record.document_ids = False

    @api.depends("container_ids")
    def _compute_total_boxes(self):
        for record in self:
            record.total_boxes = str(len(record.container_ids))

    @api.depends("document_ids")
    def _compute_total_documents(self):
        for record in self:
            record.total_documents = str(len(record.document_ids))
