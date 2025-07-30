# -*- coding: utf-8 -*-
"""
Document Retrieval Work Order Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DocumentRetrievalWorkOrder(models.Model):
    """
    Document Retrieval Work Order
    Manages work orders for document retrieval requests
    """

    _name = "document.retrieval.work.order"
    _description = "Document Retrieval Work Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, scheduled_date, create_date desc"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(
        string="Work Order Reference",
        required=True,
        tracking=True,
        default=lambda self: _("New"),
        copy=False,
    )
    description = fields.Text(string="Work Order Description", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Work Order Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    customer_contact_id = fields.Many2one(
        "res.partner", string="Customer Contact", tracking=True
    )
    department_id = fields.Many2one(
        "records.department", string="Department", tracking=True
    )

    # ==========================================
    # WORK ORDER DETAILS
    # ==========================================
    work_order_type = fields.Selection(
        [
            ("standard", "Standard Retrieval"),
            ("expedited", "Expedited Retrieval"),
            ("emergency", "Emergency Retrieval"),
            ("bulk", "Bulk Retrieval"),
            ("research", "Research Request"),
        ],
        string="Work Order Type",
        default="standard",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        string="Priority",
        default="1",
        tracking=True,
    )

    # ==========================================
    # SCHEDULING
    # ==========================================
    request_date = fields.Datetime(
        string="Request Date", default=fields.Datetime.now, required=True, tracking=True
    )
    scheduled_date = fields.Datetime(string="Scheduled Date", tracking=True)
    due_date = fields.Datetime(string="Due Date", tracking=True)

    estimated_start_time = fields.Datetime(string="Estimated Start Time")
    estimated_completion_time = fields.Datetime(string="Estimated Completion Time")
    actual_start_time = fields.Datetime(string="Actual Start Time")
    actual_completion_time = fields.Datetime(string="Actual Completion Time")

    # ==========================================
    # PERSONNEL ASSIGNMENT
    # ==========================================
    assigned_team_id = fields.Many2one(
        "hr.department", string="Assigned Department", tracking=True
    )
    primary_technician_id = fields.Many2one(
        "res.users", string="Primary Technician", tracking=True
    )
    secondary_technician_id = fields.Many2one(
        "res.users", string="Secondary Technician", tracking=True
    )
    supervisor_id = fields.Many2one("res.users", string="Supervisor", tracking=True)

    # ==========================================
    # WORK ORDER STATUS
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("delivered", "Delivered"),
            ("invoiced", "Invoiced"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    # ==========================================
    # RETRIEVAL SPECIFICATIONS
    # ==========================================
    retrieval_item_ids = fields.One2many(
        "document.retrieval.item", "work_order_id", string="Retrieval Items"
    )
    total_documents = fields.Integer(
        string="Total Documents", compute="_compute_totals", store=True
    )
    total_pages = fields.Integer(
        string="Total Pages", compute="_compute_totals", store=True
    )
    total_containers = fields.Integer(
        string="Total Containers", compute="_compute_totals", store=True
    )

    delivery_method = fields.Selection(
        [
            ("pickup", "Customer Pickup"),
            ("courier", "Courier Delivery"),
            ("mail", "Mail Delivery"),
            ("digital", "Digital Delivery"),
            ("secure_transport", "Secure Transport"),
        ],
        string="Delivery Method",
        required=True,
        tracking=True,
    )

    delivery_address = fields.Text(string="Delivery Address")
    delivery_instructions = fields.Text(string="Delivery Instructions")

    # ==========================================
    # PRICING AND BILLING
    # ==========================================
    rate_id = fields.Many2one(
        "customer.retrieval.rates", string="Applied Rate", tracking=True
    )
    estimated_cost = fields.Float(
        string="Estimated Cost", compute="_compute_costs", store=True
    )
    actual_cost = fields.Float(string="Actual Cost", tracking=True)

    billable = fields.Boolean(string="Billable", default=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    invoiced = fields.Boolean(
        string="Invoiced", compute="_compute_invoiced", store=True
    )

    # ==========================================
    # QUALITY AND COMPLIANCE
    # ==========================================
    quality_check_required = fields.Boolean(
        string="Quality Check Required", default=True
    )
    quality_check_completed = fields.Boolean(string="Quality Check Completed")
    quality_notes = fields.Text(string="Quality Notes")

    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    custody_log_ids = fields.One2many(
        "records.chain.of.custody.log",
        "work_order_id",
        string="Chain of Custody Records",
    )

    # ==========================================
    # DOCUMENTATION
    # ==========================================
    completion_notes = fields.Text(string="Completion Notes")
    customer_signature = fields.Binary(string="Customer Signature")
    technician_signature = fields.Binary(string="Technician Signature")
    delivery_receipt = fields.Binary(string="Delivery Receipt")
    action_add_items = fields.Char(string='Action Add Items')
    action_assign_technician = fields.Char(string='Action Assign Technician')
    action_complete = fields.Char(string='Action Complete')
    action_confirm = fields.Char(string='Action Confirm')
    action_deliver = fields.Char(string='Action Deliver')
    action_ready_for_delivery = fields.Char(string='Action Ready For Delivery')
    action_start_retrieval = fields.Char(string='Action Start Retrieval')
    action_view_pricing_breakdown = fields.Char(string='Action View Pricing Breakdown')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    assignment = fields.Char(string='Assignment')
    barcode = fields.Char(string='Barcode')
    base_delivery_cost = fields.Char(string='Base Delivery Cost')
    base_retrieval_cost = fields.Char(string='Base Retrieval Cost')
    box_id = fields.Many2one('box', string='Box Id')
    button_box = fields.Char(string='Button Box')
    color = fields.Char(string='Color')
    confirmed = fields.Boolean(string='Confirmed', default=False)
    context = fields.Char(string='Context')
    current_location = fields.Char(string='Current Location')
    custom_rates = fields.Char(string='Custom Rates')
    customer_info = fields.Char(string='Customer Info')
    customer_rates_id = fields.Many2one('customer.rates', string='Customer Rates Id')
    customer_signature_date = fields.Date(string='Customer Signature Date')
    delivered_by = fields.Char(string='Delivered By')
    delivery = fields.Char(string='Delivery')
    delivery_contact = fields.Char(string='Delivery Contact')
    delivery_date = fields.Date(string='Delivery Date')
    delivery_notes = fields.Char(string='Delivery Notes')
    delivery_phone = fields.Char(string='Delivery Phone')
    delivery_time = fields.Float(string='Delivery Time', digits=(12, 2))
    document_id = fields.Many2one('document', string='Document Id')
    draft = fields.Char(string='Draft')
    driver_id = fields.Many2one('driver', string='Driver Id')
    emergency = fields.Char(string='Emergency')
    group_customer = fields.Char(string='Group Customer')
    group_priority = fields.Selection([], string='Group Priority')  # TODO: Define selection options
    group_request_date = fields.Date(string='Group Request Date')
    group_state = fields.Selection([], string='Group State')  # TODO: Define selection options
    group_technician = fields.Char(string='Group Technician')
    has_custom_rates = fields.Char(string='Has Custom Rates')
    help = fields.Char(string='Help')
    in_progress = fields.Char(string='In Progress')
    item_type = fields.Selection([], string='Item Type')  # TODO: Define selection options
    items = fields.Char(string='Items')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    my_orders = fields.Char(string='My Orders')
    notes = fields.Char(string='Notes')
    pricing = fields.Char(string='Pricing')
    pricing_breakdown = fields.Char(string='Pricing Breakdown')
    priority_item_cost = fields.Char(string='Priority Item Cost')
    priority_order_cost = fields.Char(string='Priority Order Cost')
    request_info = fields.Char(string='Request Info')
    requested_by = fields.Char(string='Requested By')
    res_model = fields.Char(string='Res Model')
    retrieval_notes = fields.Char(string='Retrieval Notes')
    rush = fields.Char(string='Rush')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    technician_id = fields.Many2one('technician', string='Technician Id')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    total_cost = fields.Char(string='Total Cost')
    view_id = fields.Many2one('view', string='View Id')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum(record.line_ids.mapped('amount'))

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends(
        "retrieval_item_ids",
        "retrieval_item_ids.document_count",
        "retrieval_item_ids.page_count",
        "retrieval_item_ids.container_count",
    )
    def _compute_totals(self):
        """Compute total documents, pages, and containers"""
        for order in self:
            order.total_documents = sum(
                order.retrieval_item_ids.mapped("document_count")
            )
            order.total_pages = sum(order.retrieval_item_ids.mapped("page_count"))
            order.total_containers = sum(
                order.retrieval_item_ids.mapped("container_count")
            )

    @api.depends(
        "rate_id",
        "total_documents",
        "total_pages",
        "total_containers",
        "work_order_type",
    )
    def _compute_costs(self):
        """Compute estimated cost based on rate and quantities"""
        for order in self:
            if order.rate_id and order.total_documents:
                urgency = "standard"
                if order.work_order_type == "expedited":
                    urgency = "expedited"
                elif order.work_order_type == "emergency":
                    urgency = "emergency"

                order.estimated_cost = order.rate_id.calculate_retrieval_cost(
                    document_count=order.total_documents,
                    page_count=order.total_pages,
                    container_count=order.total_containers,
                    urgency=urgency,
                )
            else:
                order.estimated_cost = 0.0

    @api.depends("invoice_id")
    def _compute_invoiced(self):
        """Check if work order is invoiced"""
        for order in self:
            order.invoiced = bool(order.invoice_id)

    # ==========================================
    # CRUD METHODS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "document.retrieval.work.order"
                ) or _("New")
        return super().create(vals_list)

    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_confirm(self):
        """Confirm work order"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft work orders can be confirmed"))

        if not self.retrieval_item_ids:
            raise UserError(_("Please add at least one retrieval item"))

        self.write({"state": "confirmed"})
        self.message_post(body=_("Work order confirmed"))

    def action_assign(self):
        """Assign work order to technician"""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed work orders can be assigned"))

        if not self.primary_technician_id:
            raise UserError(_("Please assign a primary technician"))

        self.write({"state": "assigned"})
        self.message_post(
            body=_("Work order assigned to %s") % self.primary_technician_id.name
        )

    def action_start(self):
        """Start work order execution"""
        self.ensure_one()
        if self.state != "assigned":
            raise UserError(_("Only assigned work orders can be started"))

        self.write({"state": "in_progress", "actual_start_time": fields.Datetime.now()})

        # Create custody log for work start
        if self.chain_of_custody_required:
            self.env["records.chain.of.custody.log"].create_work_order_custody_log(
                work_order_id=self.id,
                custody_event="retrieval_start",
                from_party=None,  # Documents come from storage
                to_party=self.primary_technician_id.partner_id,
                notes=f"Document retrieval started by {self.primary_technician_id.name}",
            )

        self.message_post(body=_("Work order started"))

    def action_complete(self):
        """Complete work order"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only work orders in progress can be completed"))

        if self.quality_check_required and not self.quality_check_completed:
            raise UserError(_("Quality check must be completed before finishing"))

        self.write(
            {"state": "completed", "actual_completion_time": fields.Datetime.now()}
        )

        # Create custody log for work completion
        if self.chain_of_custody_required:
            self.env["records.chain.of.custody.log"].create_work_order_custody_log(
                work_order_id=self.id,
                custody_event="retrieval_complete",
                from_party=self.primary_technician_id.partner_id,
                to_party=None,  # Documents ready for delivery
                notes=f"Document retrieval completed by {self.primary_technician_id.name}",
            )

        self.message_post(body=_("Work order completed"))

    def action_deliver(self):
        """Mark as delivered"""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Only completed work orders can be delivered"))

        self.write({"state": "delivered"})

        # Create custody log for delivery
        if self.chain_of_custody_required:
            self.env["records.chain.of.custody.log"].create_work_order_custody_log(
                work_order_id=self.id,
                custody_event="delivery",
                from_party=None,  # From records center
                to_party=self.customer_contact_id or self.customer_id,
                notes=f"Documents delivered to customer via {self.delivery_method}",
            )

        self.message_post(body=_("Work order delivered"))

    def action_create_invoice(self):
        """Create invoice for work order"""
        self.ensure_one()
        if self.state not in ["completed", "delivered"]:
            raise UserError(
                _("Only completed or delivered work orders can be invoiced")
            )

        if not self.billable:
            raise UserError(_("This work order is not billable"))

        if self.invoiced:
            raise UserError(_("Work order already invoiced"))

        # Create invoice
        invoice_vals = {
            "partner_id": self.customer_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": f"Document Retrieval - {self.name}",
                        "quantity": 1,
                        "price_unit": self.actual_cost or self.estimated_cost,
                        "account_id": self.env["account.account"]
                        .search([("account_type", "=", "income")], limit=1)
                        .id,
                    },
                )
            ],
        }

        invoice = self.env["account.move"].create(invoice_vals)

        self.write({"state": "invoiced", "invoice_id": invoice.id})

        self.message_post(body=_("Invoice created: %s") % invoice.name)

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_cancel(self):
        """Cancel work order"""
        self.ensure_one()
        if self.state in ["completed", "delivered", "invoiced"]:
            raise UserError(
                _("Cannot cancel completed, delivered, or invoiced work orders")
            )

        self.write({"state": "cancelled"})
        self.message_post(body=_("Work order cancelled"))

    # ==========================================
    # HELPER METHODS
    # ==========================================
    def get_estimated_turnaround(self):
        """Get estimated turnaround time"""
        self.ensure_one()
        if self.rate_id:
            urgency = "standard"
            if self.work_order_type == "expedited":
                urgency = "expedited"
            elif self.work_order_type == "emergency":
                urgency = "emergency"
            return self.rate_id.get_turnaround_time(urgency)
        return 24  # Default 24 hours

    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains("scheduled_date", "due_date")
    def _check_dates(self):
        """Validate dates"""
        for order in self:
            if order.scheduled_date and order.due_date:
                if order.scheduled_date > order.due_date:
                    raise ValidationError(_("Scheduled date cannot be after due date"))

    @api.constrains("actual_start_time", "actual_completion_time")
    def _check_actual_times(self):
        """Validate actual times"""
        for order in self:
            if order.actual_start_time and order.actual_completion_time:
                if order.actual_completion_time <= order.actual_start_time:
                    raise ValidationError(_("Completion time must be after start time"))


# ==========================================
# DOCUMENT RETRIEVAL ITEM MODEL
# ==========================================
class DocumentRetrievalItem(models.Model):
    """
    Individual items in a document retrieval work order
    """

    _name = "document.retrieval.item"
    _description = "Document Retrieval Item"
    _order = "sequence, id"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    sequence = fields.Integer(string="Sequence", default=10)
    work_order_id = fields.Many2one(
        "document.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Item Description", required=True)

    # ==========================================
    # ITEM SPECIFICATIONS
    # ==========================================
    item_type = fields.Selection(
        [
            ("document", "Single Document"),
            ("folder", "Document Folder"),
            ("container", "Records Container"),
            ("file", "File Cabinet"),
            ("custom", "Custom Item"),
        ],
        string="Item Type",
        required=True,
        default="document",
    )

    container_id = fields.Many2one("records.container", string="Records Container")
    folder_name = fields.Char(string="Folder Name")
    document_reference = fields.Char(string="Document Reference")

    # ==========================================
    # QUANTITIES
    # ==========================================
    document_count = fields.Integer(string="Document Count", default=1)
    page_count = fields.Integer(string="Page Count", default=1)
    container_count = fields.Integer(string="Container Count", default=0)

    # ==========================================
    # LOCATION INFORMATION
    # ==========================================
    storage_location = fields.Char(string="Storage Location")
    shelf_number = fields.Char(string="Shelf Number")
    section = fields.Char(string="Section")
    notes = fields.Text(string="Retrieval Notes")

    # ==========================================
    # STATUS
    # ==========================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("located", "Located"),
            ("retrieved", "Retrieved"),
            ("not_found", "Not Found"),
            ("damaged", "Damaged"),
        ],
        string="Status",
        default="pending",
    )

    retrieved_by = fields.Many2one("res.users", string="Retrieved By")
    retrieved_date = fields.Datetime(string="Retrieved Date")

    # ==========================================
    # ACTIONS
    # ==========================================
    def action_mark_located(self):
        """Mark item as located"""
        self.write({"status": "located"})

    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.write(
            {
                "status": "retrieved",
                "retrieved_by": self.env.user.id,
                "retrieved_date": fields.Datetime.now(),
            }
        )

    def action_mark_not_found(self):
        """Mark item as not found"""
        self.write({"status": "not_found"})
