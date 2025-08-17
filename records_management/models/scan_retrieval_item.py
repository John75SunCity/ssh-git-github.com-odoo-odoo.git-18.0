from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError


class ScanRetrievalItem(models.Model):
    _name = 'scan.retrieval.item'
    _description = 'Scan Retrieval Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence'
    _rec_name = 'description'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    work_order_id = fields.Many2one()
    container_id = fields.Many2one()
    document_id = fields.Many2one()
    page_range = fields.Char()
    page_count = fields.Integer()
    custom_resolution = fields.Selection()
    custom_color_mode = fields.Selection()
    status = fields.Selection()
    quality_rating = fields.Float()
    quality_notes = fields.Text()
    scanned_file_path = fields.Char()
    file_size_mb = fields.Float()
    scan_start_time = fields.Datetime()
    scan_completion_time = fields.Datetime()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    state = fields.Selection()
    action_cancel = fields.Char(string='Action Cancel')
    action_complete = fields.Char(string='Action Complete')
    action_start_processing = fields.Char(string='Action Start Processing')
    action_view_work_order = fields.Char(string='Action View Work Order')
    active = fields.Boolean(string='Active')
    actual_completion_date = fields.Date(string='Actual Completion Date')
    additional_attachments = fields.Char(string='Additional Attachments')
    assigned_user_id = fields.Many2one('assigned.user')
    assignment = fields.Char(string='Assignment')
    attachments = fields.Char(string='Attachments')
    barcode = fields.Char(string='Barcode')
    button_box = fields.Char(string='Button Box')
    color_depth = fields.Char(string='Color Depth')
    company_id = fields.Many2one('res.company', string='Company Id')
    completed = fields.Boolean(string='Completed')
    compression_type = fields.Selection(string='Compression Type')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    create_uid = fields.Char(string='Create Uid')
    document_description = fields.Char(string='Document Description')
    document_type = fields.Selection(string='Document Type')
    draft = fields.Char(string='Draft')
    due_today = fields.Char(string='Due Today')
    expected_completion_date = fields.Date(string='Expected Completion Date')
    file_size = fields.Char(string='File Size')
    group_by_company = fields.Char(string='Group By Company')
    group_by_document_type = fields.Selection(string='Group By Document Type')
    group_by_priority = fields.Selection(string='Group By Priority')
    group_by_scan_date = fields.Date(string='Group By Scan Date')
    group_by_state = fields.Selection(string='Group By State')
    group_by_user = fields.Char(string='Group By User')
    group_by_work_order = fields.Char(string='Group By Work Order')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    in_progress = fields.Char(string='In Progress')
    low_priority = fields.Selection(string='Low Priority')
    main_info = fields.Char(string='Main Info')
    medium_priority = fields.Selection(string='Medium Priority')
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
    retrieval_work_order_id = fields.Many2one('retrieval.work.order')
    scan_date = fields.Date(string='Scan Date')
    scan_quality = fields.Char(string='Scan Quality')
    scanned_document_attachment = fields.Char(string='Scanned Document Attachment')
    scanned_this_month = fields.Char(string='Scanned This Month')
    scanned_this_week = fields.Char(string='Scanned This Week')
    scanned_today = fields.Char(string='Scanned Today')
    search_view_id = fields.Many2one('search.view')
    type = fields.Selection(string='Type')
    unassigned = fields.Char(string='Unassigned')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    write_date = fields.Date(string='Write Date')
    write_uid = fields.Char(string='Write Uid')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_start_scanning(self):
            """Mark this item as scanning started"""
            self.ensure_one()
            if self.status not in ['pending', 'located']:
                raise UserError(_("Can only start scanning from pending or located status"))

            self.write({)}
                'status': 'scanning',
                'scan_start_time': fields.Datetime.now()

            self.message_post()
                body=_("Started scanning item: %s", self.description),
                message_type='notification'



    def action_complete_scanning(self):
            """Mark this item as scanned"""
            self.ensure_one()
            if self.status != 'scanning':
                raise UserError(_("Can only complete scanning from scanning status"))

            self.write({)}
                'status': 'scanned',
                'scan_completion_time': fields.Datetime.now()

            self.message_post()
                body=_("Completed scanning item: %s", self.description),
                message_type='notification'



    def action_approve_quality(self):
            """Approve the quality of this scanned item"""
            self.ensure_one()
            if self.status != 'quality_review':
                raise UserError(_("Can only approve quality from quality review status"))

            self.write({'status': 'approved'})
            self.message_post()
                body=_("Quality approved for item: %s", self.description),
                message_type='notification'



    def action_request_rescan(self):
            """Request that this item be rescanned due to quality issues"""
            self.ensure_one()
            if self.status not in ['scanned', 'quality_review']:
                raise UserError(_("Can only request rescan from scanned or quality review status"))

            self.write({)}
                'status': 'rescan_needed',
                'scan_start_time': False,
                'scan_completion_time': False

            self.message_post()
                body=_("Rescan requested for item: %s", self.description),
                message_type='notification'


