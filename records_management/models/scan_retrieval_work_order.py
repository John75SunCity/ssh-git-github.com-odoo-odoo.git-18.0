# -*- coding: utf-8 -*-

Scan Retrieval Work Order Module

This module manages work orders for creating digital scans of documents from pages:
    pass
within files contained in containers. The scans are delivered electronically to customers,
providing digital access while preserving original documents.:
Key Features
- Precise page-level scanning from within files and containers
- High-quality digital reproduction with multiple format options
- Electronic delivery via email, portal, or secure file transfer
- Integration with file and container retrieval workflows
- OCR and document enhancement capabilities
- Secure digital asset management and version control

Business Processes
1. Scan Request Creation: Customer requests specific pages or documents for scanning:
2. File Location and Access: Locate source files within containers
3. Page Identification: Identify specific pages or document sections to scan
4. Digital Scanning: Create high-quality digital copies with appropriate settings
5. Quality Assurance: Review and enhance scanned images as needed
6. Electronic Delivery: Deliver digital files via secure channels
7. Archive Management: Store and manage digital assets for future access""":"
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ScanRetrievalWorkOrder(models.Model):
    _name = "scan.retrieval.work.order"
    _description = "Scan Retrieval Work Order"
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
        ,
    default=lambda self: _("New"),
        help="Unique scan retrieval work order number"
    
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name for the work order":
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary user responsible for this work order":
    
    active = fields.Boolean(string="Active", default=True,,
    tracking=True)

        # ============================================================================
    # WORK ORDER STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locating', 'Locating Documents'),
        ('accessing', 'Accessing Files'),
        ('scanning', 'Scanning in Progress'),
        ('processing', 'Image Processing'),
        ('quality_review', 'Quality Review'),
        ('preparing', 'Preparing for Delivery'),:
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    
        help="Current status of the scan retrieval work order"

    priority = fields.Selection([))
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    
        help="Work order priority level for processing"
    # ============================================================================
        # CUSTOMER AND REQUEST INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        ,
    domain="[('is_company', '=', True))",
        help="Customer requesting document scanning"
    
    portal_request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Originating portal request if applicable":
    
    scan_request_description = fields.Text(
        string="Scan Request Description",
        required=True,
        help="Detailed description of documents/pages to be scanned"
    

        # ============================================================================
    # SCAN SPECIFICATION AND REQUIREMENTS
        # ============================================================================
    scan_item_ids = fields.One2many(
        "scan.retrieval.item",
        "work_order_id",
        string="Scan Items",
        help="Specific documents/pages to be scanned"
    
    item_count = fields.Integer(
        string="Item Count",
        compute="_compute_scan_metrics",
        store=True,
        help="Number of scan items"
    
    total_pages_to_scan = fields.Integer(
        string="Total Pages to Scan",
        compute="_compute_scan_metrics",
        store=True,
        help="Total number of pages to be scanned"
    
    
        # Scanning specifications
    ,
    scan_resolution = fields.Selection([))
        ('150', '150 DPI - Basic'),
        ('300', '300 DPI - Standard'),
        ('600', '600 DPI - High Quality'),
        ('1200', '1200 DPI - Archive Quality'),
    
        help="Resolution for document scanning"
    color_mode = fields.Selection([))
        ('bw', 'Black & White'),
        ('grayscale', 'Grayscale'),
        ('color', 'Full Color'),
    
        help="Color mode for scanning"
    output_format = fields.Selection([))
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
    
        help="File format for scanned documents"
    # ============================================================================
        # SOURCE TRACKING
    # ============================================================================
    container_ids = fields.Many2many(
        "records.container",
        "scan_retrieval_container_rel",
        "work_order_id",
        "container_id",
        string="Source Containers",
        help="Containers containing documents to be scanned"
    
    file_ids = fields.Many2many(
        "records.document",
        "scan_retrieval_document_rel",
        "work_order_id",
        "document_id",
        string="Source Files",
        help="Specific files containing pages to scan"
    
    location_ids = fields.Many2many(
        "records.location",
        "scan_retrieval_location_rel",
        "work_order_id",
        "location_id",
        string="Source Locations",
        help="Locations where source materials are stored"
    

        # ============================================================================
    # SCHEDULING AND TIMING
        # ============================================================================
    scheduled_date = fields.Datetime(
        string="Scheduled Start Date",
        required=True,
        tracking=True,
        help="Planned date to start scanning process"
    
    estimated_completion_date = fields.Datetime(
        string="Estimated Completion",
        compute="_compute_estimated_completion",
        store=True,
        help="Estimated completion date based on scanning workload"
    
    actual_start_date = fields.Datetime(
        string="Actual Start Date",
        tracking=True,
        help="Actual date when scanning started"
    
    actual_completion_date = fields.Datetime(
        string="Actual Completion Date",
        tracking=True,
        help="Actual date when all scanning was completed"
    

        # ============================================================================
    # EQUIPMENT AND PROCESSING OPTIONS
        # ============================================================================
    scanner_id = fields.Many2one(
        "scan.equipment",
        string="Assigned Scanner",
        help="Scanner equipment assigned for this work order":
    
    scanning_station = fields.Char(
        string="Scanning Station",
        help="Physical location/station where scanning will be performed"
    
    
        # Processing options
    ocr_required = fields.Boolean(
        string="OCR Processing Required",
        help="Whether OCR text recognition is needed"
    
    image_enhancement = fields.Boolean(
        string="Image Enhancement",
        ,
    help="Apply image enhancement (noise reduction, contrast adjustment)"
    
    auto_crop = fields.Boolean(
        string="Auto Crop",
        default=True,
        help="Automatically crop pages to remove borders"
    
    deskew = fields.Boolean(
        string="Deskew Images",
        default=True,
        help="Automatically straighten skewed pages"
    

        # ============================================================================
    # DELIVERY SPECIFICATIONS
        # ============================================================================
    ,
    delivery_method = fields.Selection([))
        ('email', 'Email Delivery'),
        ('portal', 'Customer Portal'),
        ('ftp', 'FTP Upload'),
        ('secure_link', 'Secure Download Link'),
        ('usb_drive', 'USB Drive'),
        ('cd_dvd', 'CD/DVD'),
    
        help="Method for delivering scanned files"
    email_delivery_address = fields.Char(
        string="Email Delivery Address",
        ,
    help="Email address for delivery (if different from customer contact)":
    
    file_naming_convention = fields.Selection([))
        ('sequential', 'Sequential (1, 2, 3...)'),
        ('descriptive', 'Descriptive (based on content)'),
        ('date_based', 'Date-based (YYYYMMDD_001)'),
        ('custom', 'Custom Pattern'),
    
        help="Convention for naming scanned files"
    custom_naming_pattern = fields.Char(
        string="Custom Naming Pattern",
        ,
    help="Custom pattern for file naming (use {seq}, {date}, {desc) placeholders)":
    

        # ============================================================================
    # PROGRESS TRACKING AND QUALITY
        # ============================================================================
    progress_percentage = fields.Float(
        string="Progress %",
        compute="_compute_progress",
        help="Overall progress percentage of the scanning work order"
    
    pages_scanned_count = fields.Integer(
        string="Pages Scanned",
        help="Number of pages successfully scanned"
    
    pages_processed_count = fields.Integer(
        string="Pages Processed",
        help="Number of pages that completed image processing"
    
    pages_quality_approved_count = fields.Integer(
        string="Pages Quality Approved",
        help="Number of pages that passed quality review"
    
    
        # Quality metrics
    average_scan_quality = fields.Float(
        string="Average Scan Quality",
        ,
    help="Average quality rating for scanned pages (1-10 scale)":
    
    rescan_required_count = fields.Integer(
        string="Rescans Required",
        help="Number of pages requiring rescanning due to quality issues"
    

        # ============================================================================
    # DIGITAL ASSET MANAGEMENT
        # ============================================================================
    total_file_size_mb = fields.Float(
        ,
    string="Total File Size (MB)",
        compute="_compute_file_metrics",
        store=True,
        help="Total size of all scanned files in megabytes"
    
    file_count = fields.Integer(
        string="File Count",
        compute="_compute_file_metrics",
        store=True,
        help="Number of output files created"
    
    digital_asset_ids = fields.One2many(
        "scan.digital.asset",
        "work_order_id",
        string="Digital Assets",
        help="Created digital assets from scanning process"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages"),
    coordinator_id = fields.Many2one('work.order.coordinator',,
    string='Coordinator'),
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

        # ============================================================================
    # MODEL CREATE WITH SEQUENCE
        # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name') = self.env['ir.sequence'].next_by_code()
                    'scan.retrieval.work.order') or _('New'
        return super().create(vals_list)

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id', 'total_pages_to_scan')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.total_pages_to_scan:
                record.display_name = _("%s - %s (%s pages)", 
                    record.name, record.partner_id.name, record.total_pages_to_scan
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Scan Retrieval")

    @api.depends('scan_item_ids')
    def _compute_scan_metrics(self):
        for record in self:
            items = record.scan_item_ids
            record.item_count = len(items)
            record.total_pages_to_scan = sum(items.mapped('page_count')) if items else 0:
    @api.depends('scheduled_date', 'total_pages_to_scan', 'scan_resolution')
    def _compute_estimated_completion(self):
        for record in self:
            if record.scheduled_date and record.total_pages_to_scan:
                # Estimate scanning time based on resolution and page count
                base_minutes_per_page = {}
                    '150': 1,    # 1 minute per page at 150 DPI
                    '300': 2,    # 2 minutes per page at 300 DPI
                    '600': 4,    # 4 minutes per page at 600 DPI
                    '1200': 8,   # 8 minutes per page at 1200 DPI
                
                
                # Add processing time if OCR or enhancement is enabled:
                if record.ocr_required:
                    base_minutes_per_page += 2
                if record.image_enhancement:
                    base_minutes_per_page += 1
                
                total_minutes = record.total_pages_to_scan * base_minutes_per_page
                # Add 2 hours for setup and quality review:
                total_minutes += 120
                
                record.estimated_completion_date = record.scheduled_date + timedelta(minutes=total_minutes)
            else:
                record.estimated_completion_date = False

    @api.depends('pages_scanned_count', 'total_pages_to_scan')
    def _compute_progress(self):
        for record in self:
            if record.total_pages_to_scan > 0:
                record.progress_percentage = (record.pages_scanned_count / record.total_pages_to_scan) * 100
            else:
                record.progress_percentage = 0.0

    @api.depends('digital_asset_ids')
    def _compute_file_metrics(self):
        for record in self:
            assets = record.digital_asset_ids
            record.file_count = len(assets)
            record.total_file_size_mb = sum(assets.mapped('file_size_mb')) if assets else 0.0:
    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the scan work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed"))
        
        self.write({'state': 'confirmed'})
        self.message_post()
            body=_("Scan retrieval work order confirmed for %s", self.partner_id.name),:
            message_type='notification'
        
        return True

    def action_start_scanning(self):
        """Start the scanning process"""
        self.ensure_one()
        if self.state not in ['confirmed', 'locating', 'accessing']:
            raise UserError(_("Can only start scanning from confirmed, locating, or accessing state"))
        
        self.write({)}
            'state': 'scanning',
            'actual_start_date': fields.Datetime.now()
        
        self.message_post()
            body=_("Started scanning process"),
            message_type='notification'
        
        return True

    def action_complete_scanning(self):
        """Complete scanning and move to processing"""
        self.ensure_one()
        if self.state != 'scanning':
            raise UserError(_("Can only complete scanning from scanning state"))
        
        self.write({'state': 'processing'})
        self.message_post()
            body=_("Scanning completed, starting image processing"),
            message_type='notification'
        
        return True

    def action_quality_review(self):
        """Start quality review process"""
        self.ensure_one()
        if self.state != 'processing':
            raise UserError(_("Can only start quality review after processing"))
        
        self.write({'state': 'quality_review'})
        self.message_post()
            body=_("Started quality review process"),
            message_type='notification'
        
        return True

    def action_prepare_delivery(self):
        """Prepare files for delivery""":
        self.ensure_one()
        if self.state != 'quality_review':
            raise UserError(_("Can only prepare delivery after quality review"))
        
        self.write({'state': 'preparing'})
        self.message_post()
            body=_("Preparing scanned files for delivery"),:
            message_type='notification'
        
        return True

    def action_deliver(self):
        """Deliver scanned files to customer"""
        self.ensure_one()
        if self.state != 'preparing':
            raise UserError(_("Can only deliver from preparing state"))
        
        # Implement delivery logic based on delivery_method
        if self.delivery_method == 'email':
            self._send_email_delivery()
        elif self.delivery_method == 'portal':
            self._upload_to_portal()
        elif self.delivery_method == 'secure_link':
            self._create_secure_link()
        
        self.write({'state': 'delivered'})
        self.message_post()
            body=_("Scanned files delivered to %s via %s", 
                    self.partner_id.name, 
                    dict(self._fields['delivery_method'].selection)[self.delivery_method]
            message_type='notification'
        
        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed"))
        
        self.write({)}
            'state': 'completed',
            'actual_completion_date': fields.Datetime.now()
        
        self.message_post()
            body=_("Scan retrieval work order completed successfully"),
            message_type='notification'
        
        return True

    # ============================================================================
        # DELIVERY METHODS
    # ============================================================================
    def _send_email_delivery(self):
        """Send scanned files via email"""
        # Implementation for email delivery:
        pass

    def _upload_to_portal(self):
        """Upload files to customer portal"""
        # Implementation for portal upload:
        pass

    def _create_secure_link(self):
        """Create secure download link"""
        # Implementation for secure link creation:
        pass

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def update_scan_progress(self, pages_scanned):
        """Update scanning progress"""
        self.ensure_one()
        self.pages_scanned_count = pages_scanned
        self.message_post()
            body=_("%s pages scanned out of %s", pages_scanned, self.total_pages_to_scan),
            message_type='comment'
        

    def generate_scan_report(self):
        """Generate scanning completion report"""
        self.ensure_one()
        return {}
            'type': 'ir.actions.report',
            'report_name': 'records_management.report_scan_retrieval',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'target': 'new',
        

    """")))))))))))))))))))))))))