# -*- coding: utf-8 -*-
"""
File Retrieval Work Order Module

This module manages work orders for retrieving specific physical files from within containers.
It handles the complete lifecycle from file identification to customer delivery,
including file location tracking, quality control, and customer notifications.

Key Features:
- Specific file identification and retrieval from containers
- File condition assessment and quality control
- Integration with container management system
- Customer delivery coordination and tracking
- File handling equipment and team management
- Detailed pricing and cost tracking for file-level services

Business Processes:
1. Work Order Creation: Generate from customer requests for specific files
2. File Location: Identify specific files within containers using detailed records
3. Container Access: Coordinate access to containers containing requested files
4. File Retrieval: Carefully extract specific files with quality checks
5. Delivery Preparation: Package and prepare files for customer delivery
6. Customer Delivery: Handle delivery logistics and customer confirmation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FileRetrievalWorkOrder(models.Model):
    _name = "file.retrieval.work.order"
    _description = "File Retrieval Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.integration.mixin']
    _order = "priority desc, scheduled_date asc, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Work Order Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
        help="Unique file retrieval work order number"
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name for the work order"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary user responsible for this work order"
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # WORK ORDER STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locating', 'Locating Files'),
        ('accessing', 'Accessing Container'),
        ('retrieving', 'Retrieving Files'),
        ('quality_check', 'Quality Check'),
        ('packaging', 'Packaging'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True,
       help="Current status of the file retrieval work order")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True,
       help="Work order priority level for processing")

    # ============================================================================
    # CUSTOMER AND REQUEST INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
        help="Customer requesting file retrieval"
    )
    portal_request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Originating portal request if applicable"
    )
    request_description = fields.Text(
        string="Request Description",
        required=True,
        help="Detailed description of files to be retrieved"
    )

    # ============================================================================
    # FILE RETRIEVAL ITEMS
    # ============================================================================
    retrieval_item_ids = fields.One2many(
        "file.retrieval.item",
        "work_order_id",
        string="Retrieval Items",
        help="Specific files to be retrieved"
    )
    item_count = fields.Integer(
        string="Item Count",
        compute="_compute_item_metrics",
        store=True,
        help="Number of files to retrieve"
    )
    estimated_pages = fields.Integer(
        string="Estimated Total Pages",
        compute="_compute_item_metrics",
        store=True,
        help="Estimated total pages across all files"
    )

    # ============================================================================
    # CONTAINER AND LOCATION TRACKING
    # ============================================================================
    container_ids = fields.Many2many(
        "records.container",
        "file_retrieval_container_rel",
        "work_order_id",
        "container_id",
        string="Source Containers",
        help="Containers that need to be accessed for file retrieval"
    )
    location_ids = fields.Many2many(
        "records.location",
        "file_retrieval_location_rel", 
        "work_order_id",
        "location_id",
        string="Access Locations",
        help="Locations where containers are stored"
    )
    access_coordination_needed = fields.Boolean(
        string="Access Coordination Needed",
        default=True,
        help="Whether special coordination is needed to access containers"
    )

    # ============================================================================
    # SCHEDULING AND TIMING
    # ============================================================================
    scheduled_date = fields.Datetime(
        string="Scheduled Start Date",
        required=True,
        tracking=True,
        help="Planned date to start file retrieval process"
    )
    estimated_completion_date = fields.Datetime(
        string="Estimated Completion",
        compute="_compute_estimated_completion",
        store=True,
        help="Estimated completion date based on workload"
    )
    actual_start_date = fields.Datetime(
        string="Actual Start Date",
        tracking=True,
        help="Actual date when file retrieval started"
    )
    actual_completion_date = fields.Datetime(
        string="Actual Completion Date",
        tracking=True,
        help="Actual date when all files were retrieved and packaged"
    )

    # ============================================================================
    # DELIVERY AND PACKAGING
    # ============================================================================
    delivery_method = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Delivery'),
        ('mail', 'Mail/Postal'),
        ('secure_transport', 'Secure Transport'),
        ('hand_delivery', 'Hand Delivery'),
    ], string='Delivery Method', default='pickup', required=True,
       help="Method for delivering files to customer")
    
    packaging_type = fields.Selection([
        ('folder', 'File Folder'),
        ('box', 'Document Box'),
        ('envelope', 'Envelope'),
        ('tube', 'Mailing Tube'),
        ('secure_case', 'Secure Case'),
    ], string='Packaging Type', default='folder',
       help="Type of packaging for retrieved files")
    
    delivery_address_id = fields.Many2one(
        "res.partner",
        string="Delivery Address",
        help="Specific delivery address if different from customer address"
    )
    delivery_instructions = fields.Text(
        string="Delivery Instructions",
        help="Special delivery instructions from customer"
    )

    # ============================================================================
    # PROGRESS TRACKING AND METRICS
    # ============================================================================
    progress_percentage = fields.Float(
        string="Progress %",
        compute="_compute_progress",
        help="Overall progress percentage of the work order"
    )
    files_located_count = fields.Integer(
        string="Files Located",
        help="Number of files successfully located"
    )
    files_retrieved_count = fields.Integer(
        string="Files Retrieved", 
        help="Number of files successfully retrieved"
    )
    files_quality_approved_count = fields.Integer(
        string="Files Quality Approved",
        help="Number of files that passed quality check"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # MODEL CREATE WITH SEQUENCE
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'file.retrieval.work.order') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id', 'item_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.item_count:
                record.display_name = _("%s - %s (%s files)", 
                    record.name, record.partner_id.name, record.item_count)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New File Retrieval")

    @api.depends('retrieval_item_ids')
    def _compute_item_metrics(self):
        for record in self:
            items = record.retrieval_item_ids
            record.item_count = len(items)
            record.estimated_pages = sum(items.mapped('estimated_pages')) if items else 0

    @api.depends('scheduled_date', 'item_count')
    def _compute_estimated_completion(self):
        for record in self:
            if record.scheduled_date and record.item_count:
                # Estimate 2 hours per file plus 4 hours base time
                estimated_hours = 4 + (record.item_count * 2)
                record.estimated_completion_date = record.scheduled_date + timedelta(hours=estimated_hours)
            else:
                record.estimated_completion_date = False

    @api.depends('files_retrieved_count', 'item_count')
    def _compute_progress(self):
        for record in self:
            if record.item_count > 0:
                record.progress_percentage = (record.files_retrieved_count / record.item_count) * 100
            else:
                record.progress_percentage = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed"))
        
        self.write({'state': 'confirmed'})
        self.message_post(
            body=_("File retrieval work order confirmed for %s", self.partner_id.name),
            message_type='notification'
        )
        return True

    def action_start_locating(self):
        """Start file location process"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can start file location"))
        
        self.write({
            'state': 'locating',
            'actual_start_date': fields.Datetime.now()
        })
        self.message_post(
            body=_("Started file location process"),
            message_type='notification'
        )
        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed"))
        
        self.write({
            'state': 'completed',
            'actual_completion_date': fields.Datetime.now()
        })
        self.message_post(
            body=_("File retrieval work order completed successfully"),
            message_type='notification'
        )
        return True


class FileRetrievalItem(models.Model):
    """Individual file items to be retrieved"""
    _name = "file.retrieval.item"
    _description = "File Retrieval Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "work_order_id, sequence"
    _rec_name = "description"

    # Core fields
    name = fields.Char(string="Item Reference", required=True, tracking=True, index=True)
    description = fields.Text(string="File Description", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    
    # Work order relationship
    work_order_id = fields.Many2one(
        "file.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete='cascade'
    )
    
    # File details
    file_name = fields.Char(string="File Name")
    estimated_pages = fields.Integer(string="Estimated Pages", default=1)
    file_type = fields.Selection([
        ('document', 'Document'),
        ('photo', 'Photograph'),
        ('blueprint', 'Blueprint'),
        ('legal', 'Legal Document'),
        ('medical', 'Medical Record'),
        ('other', 'Other'),
    ], string='File Type', default='document')
    
    # Location information
    container_id = fields.Many2one("records.container", string="Source Container")
    location_notes = fields.Text(string="Location Notes")
    
    # Status tracking
    status = fields.Selection([
        ('pending', 'Pending'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('quality_checked', 'Quality Checked'),
        ('packaged', 'Packaged'),
        ('not_found', 'Not Found'),
    ], string='Status', default='pending', tracking=True)
    
    # Quality and condition
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ], string='Condition')
    
    quality_notes = fields.Text(string="Quality Notes")
    actual_pages = fields.Integer(string="Actual Pages")
    
    # Mail thread fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    def action_mark_located(self):
        """Mark item as located"""
        self.ensure_one()
        self.status = 'located'
        # Update work order progress
        located_count = len(self.work_order_id.retrieval_item_ids.filtered(lambda r: r.status == 'located'))
        self.work_order_id.files_located_count = located_count

    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.ensure_one()
        self.status = 'retrieved'
        # Update work order progress
        retrieved_count = len(self.work_order_id.retrieval_item_ids.filtered(lambda r: r.status == 'retrieved'))
        self.work_order_id.files_retrieved_count = retrieved_count
