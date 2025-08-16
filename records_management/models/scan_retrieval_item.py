# -*- coding: utf-8 -*-
"""
Scan Retrieval Item Module

This module manages individual items/pages to be scanned as part of scan retrieval work orders.
Each item represents specific documents, pages, or sections that need to be digitally scanned.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ScanRetrievalItem(models.Model):
    """Individual items/pages to be scanned"""
    _name = "scan.retrieval.item"
    _description = "Scan Retrieval Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "work_order_id, sequence"
    _rec_name = "description"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Reference", 
        required=True, 
        tracking=True, 
        index=True,
        help="Unique reference for this scan item"
    )
    description = fields.Text(
        string="Item Description", 
        required=True,
        help="Detailed description of what needs to be scanned"
    )
    sequence = fields.Integer(
        string="Sequence", 
        default=10,
        help="Order in which items should be processed"
    )
    
    # ============================================================================
    # WORK ORDER RELATIONSHIP
    # ============================================================================
    work_order_id = fields.Many2one(
        "scan.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete='cascade',
        help="Parent scan retrieval work order"
    )
    
    # ============================================================================
    # SOURCE INFORMATION
    # ============================================================================
    container_id = fields.Many2one(
        "records.container", 
        string="Source Container",
        help="Container holding the documents to scan"
    )
    document_id = fields.Many2one(
        "records.document", 
        string="Source Document/File",
        help="Specific document/file containing pages to scan"
    )
    page_range = fields.Char(
        string="Page Range", 
        help="Specific pages to scan (e.g., '1-5, 8, 10-12')"
    )
    page_count = fields.Integer(
        string="Page Count", 
        default=1,
        help="Number of pages to be scanned for this item"
    )
    
    # ============================================================================
    # SCANNING SPECIFICATIONS (Override work order defaults)
    # ============================================================================
    custom_resolution = fields.Selection([
        ('150', '150 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI'),
        ('1200', '1200 DPI'),
    ], string='Custom Resolution', 
       help="Override default resolution for this specific item")
    
    custom_color_mode = fields.Selection([
        ('bw', 'Black & White'),
        ('grayscale', 'Grayscale'),
        ('color', 'Full Color'),
    ], string='Custom Color Mode', 
       help="Override default color mode for this specific item")
    
    # ============================================================================
    # STATUS AND QUALITY TRACKING
    # ============================================================================
    status = fields.Selection([
        ('pending', 'Pending'),
        ('located', 'Located'),
        ('scanning', 'Scanning'),
        ('scanned', 'Scanned'),
        ('processing', 'Processing'),
        ('quality_review', 'Quality Review'),
        ('approved', 'Approved'),
        ('rescan_needed', 'Rescan Needed'),
    ], string='Status', default='pending', tracking=True,
       help="Current processing status of this scan item")
    
    quality_rating = fields.Float(
        string="Quality Rating", 
        help="Quality rating on a 1-10 scale"
    )
    quality_notes = fields.Text(
        string="Quality Notes",
        help="Notes about scan quality or issues encountered"
    )
    
    # ============================================================================
    # OUTPUT FILE INFORMATION
    # ============================================================================
    scanned_file_path = fields.Char(
        string="Scanned File Path",
        help="File system path to the scanned output file"
    )
    file_size_mb = fields.Float(
        string="File Size (MB)",
        help="Size of the scanned file in megabytes"
    )
    
    # ============================================================================
    # PROCESSING TIMESTAMPS
    # ============================================================================
    scan_start_time = fields.Datetime(
        string="Scan Start Time",
        help="When scanning of this item began"
    )
    scan_completion_time = fields.Datetime(
        string="Scan Completion Time",
        help="When scanning of this item was completed"
    )
    
    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft')
    action_cancel = fields.Char(string='Action Cancel')
    action_complete = fields.Char(string='Action Complete')
    action_start_processing = fields.Char(string='Action Start Processing')
    action_view_work_order = fields.Char(string='Action View Work Order')
    active = fields.Boolean(string='Active', default=True)
    actual_completion_date = fields.Date(string='Actual Completion Date')
    additional_attachments = fields.Char(string='Additional Attachments')
    assigned_user_id = fields.Many2one('assigned.user', string='Assigned User Id')
    assignment = fields.Char(string='Assignment')
    attachments = fields.Char(string='Attachments')
    barcode = fields.Char(string='Barcode')
    button_box = fields.Char(string='Button Box')
    color_depth = fields.Char(string='Color Depth')
    company_id = fields.Many2one('res.company', string='Company Id', default=lambda self: self.env.company)
    completed = fields.Boolean(string='Completed', default=False)
    compression_type = fields.Selection([], string='Compression Type')  # TODO: Define selection options
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    create_uid = fields.Char(string='Create Uid')
    document_description = fields.Char(string='Document Description')
    document_type = fields.Selection([], string='Document Type')  # TODO: Define selection options
    draft = fields.Char(string='Draft')
    due_today = fields.Char(string='Due Today')
    expected_completion_date = fields.Date(string='Expected Completion Date')
    file_size = fields.Char(string='File Size')
    group_by_company = fields.Char(string='Group By Company')
    group_by_document_type = fields.Selection([], string='Group By Document Type')  # TODO: Define selection options
    group_by_priority = fields.Selection([], string='Group By Priority')  # TODO: Define selection options
    group_by_scan_date = fields.Date(string='Group By Scan Date')
    group_by_state = fields.Selection([], string='Group By State')  # TODO: Define selection options
    group_by_user = fields.Char(string='Group By User')
    group_by_work_order = fields.Char(string='Group By Work Order')
    help = fields.Char(string='Help')
    high_priority = fields.Selection([], string='High Priority')  # TODO: Define selection options
    in_progress = fields.Char(string='In Progress')
    low_priority = fields.Selection([], string='Low Priority')  # TODO: Define selection options
    main_info = fields.Char(string='Main Info')
    medium_priority = fields.Selection([], string='Medium Priority')  # TODO: Define selection options
    metadata = fields.Char(string='Metadata')
    my_items = fields.Char(string='My Items')
    notes = fields.Char(string='Notes')
    ocr_confidence = fields.Char(string='Ocr Confidence')
    overdue = fields.Char(string='Overdue')
    processing_notes = fields.Char(string='Processing Notes')
    quality = fields.Char(string='Quality')
    quality_check_passed = fields.Char(string='Quality Check Passed')
    quality_passed = fields.Char(string='Quality Passed')
    quality_score = fields.Char(string='Quality Score')
    res_model = fields.Char(string='Res Model')
    resolution_dpi = fields.Char(string='Resolution Dpi')
    retrieval_work_order_id = fields.Many2one('retrieval.work.order', string='Retrieval Work Order Id')
    scan_date = fields.Date(string='Scan Date')
    scan_quality = fields.Char(string='Scan Quality')
    scanned_document_attachment = fields.Char(string='Scanned Document Attachment')
    scanned_this_month = fields.Char(string='Scanned This Month')
    scanned_this_week = fields.Char(string='Scanned This Week')
    scanned_today = fields.Char(string='Scanned Today')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    unassigned = fields.Char(string='Unassigned')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    write_date = fields.Date(string='Write Date')
    write_uid = fields.Char(string='Write Uid'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_scanning(self):
        """Mark this item as scanning started"""
        self.ensure_one()
        if self.status not in ['pending', 'located']:
            raise UserError(_("Can only start scanning from pending or located status"))
        
        self.write({
            'status': 'scanning',
            'scan_start_time': fields.Datetime.now()
        })
        self.message_post(
            body=_("Started scanning item: %s", self.description),
            message_type='notification'
        )

    def action_complete_scanning(self):
        """Mark this item as scanned"""
        self.ensure_one()
        if self.status != 'scanning':
            raise UserError(_("Can only complete scanning from scanning status"))
        
        self.write({
            'status': 'scanned',
            'scan_completion_time': fields.Datetime.now()
        })
        self.message_post(
            body=_("Completed scanning item: %s", self.description),
            message_type='notification'
        )

    def action_approve_quality(self):
        """Approve the quality of this scanned item"""
        self.ensure_one()
        if self.status != 'quality_review':
            raise UserError(_("Can only approve quality from quality review status"))
        
        self.write({'status': 'approved'})
        self.message_post(
            body=_("Quality approved for item: %s", self.description),
            message_type='notification'
        )

    def action_request_rescan(self):
        """Request that this item be rescanned due to quality issues"""
        self.ensure_one()
        if self.status not in ['scanned', 'quality_review']:
            raise UserError(_("Can only request rescan from scanned or quality review status"))
        
        self.write({
            'status': 'rescan_needed',
            'scan_start_time': False,
            'scan_completion_time': False
        })
        self.message_post(
            body=_("Rescan requested for item: %s", self.description),
            message_type='notification'
        )
