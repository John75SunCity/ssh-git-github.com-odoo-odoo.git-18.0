"""Scan Retrieval Work Order model.

Coordinates scanning work for retrieved physical files into digital assets.
Key capabilities:
- Lifecycle/state machine: draft → confirmed → scanning → processing → quality_review → ready_for_delivery → delivered → completed/cancelled
- Scheduling and timing: scheduled start, estimated completion (heuristic per resolution/OCR/enhancement), actual timestamps
- Metrics and progress: item/page counts, progress %, produced file count and total MB
- Relations:
  * scan_item_ids (scan.retrieval.item) – items to scan, provides page counts
  * digital_asset_ids (scan.digital.asset) – files produced by this order
  * partner_id (res.partner), portal_request_id (portal.request), scanner_id (maintenance.equipment)
- Delivery methods: portal, email, secure link
- Chatter integration via mail.thread + mail.activity.mixin
- Sequence: scan.retrieval.work.order (assigned at create)
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class ScanRetrievalWorkOrder(models.Model):
    """Scan Retrieval Work Order.

    Manages end-to-end execution of a scanning request:
    - Tracks items to scan and resulting digital assets
    - Plans and measures throughput with estimates and progress
    - Enforces state transitions and records key timestamps
    - Supports multiple delivery methods and naming conventions
    """

    _name = 'scan.retrieval.work.order'
    _description = 'Scan Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Work Order #", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned To', tracking=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], string='Priority', default='0')
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    portal_request_id = fields.Many2one('portal.request', string="Portal Request", ondelete='set null')
    scan_request_description = fields.Text(string="Scan Request Description")
    coordinator_id = fields.Many2one('work.order.coordinator', string="Coordinator")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scanning', 'Scanning'),
        ('processing', 'Processing'),
        ('quality_review', 'Quality Review'),
        ('ready_for_delivery', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SCAN ITEMS & METRICS
    # ============================================================================
    # Link to scan retrieval items (correct comodel + inverse)
    scan_item_ids = fields.One2many(
        comodel_name='scan.retrieval.item',
        inverse_name='work_order_id',
        string="Items to Scan",
    )
    item_count = fields.Integer(string="Item Count", compute='_compute_scan_metrics', store=True)
    total_pages_to_scan = fields.Integer(string="Total Pages to Scan", compute='_compute_scan_metrics', store=True)
    # Digital assets produced by this work order
    digital_asset_ids = fields.One2many(
        comodel_name='scan.digital.asset',
        inverse_name='work_order_id',
        string="Digital Assets",
    )

    # ============================================================================
    # SCAN SPECIFICATIONS
    # ============================================================================
    scan_resolution = fields.Selection([('150', '150 DPI'), ('300', '300 DPI'), ('600', '600 DPI')], string="Resolution", default='300')
    color_mode = fields.Selection([('color', 'Color'), ('grayscale', 'Grayscale'), ('bw', 'Black & White')], string="Color Mode", default='color')
    output_format = fields.Selection([('pdf', 'PDF'), ('tiff', 'TIFF'), ('jpeg', 'JPEG')], string="Output Format", default='pdf')
    ocr_required = fields.Boolean(string="OCR Required", default=False)
    image_enhancement = fields.Boolean(string="Image Enhancement", default=True)
    auto_crop = fields.Boolean(string="Auto Crop", default=True)
    deskew = fields.Boolean(string="Deskew", default=True)

    # ============================================================================
    # SCHEDULING
    # ============================================================================
    scheduled_date = fields.Datetime(string="Scheduled Start Date", tracking=True)
    estimated_completion_date = fields.Datetime(string="Estimated Completion", compute='_compute_estimated_completion', store=True)
    actual_start_date = fields.Datetime(string="Actual Start Date", readonly=True)
    actual_completion_date = fields.Datetime(string="Actual Completion Date", readonly=True)
    scanner_id = fields.Many2one('maintenance.equipment', string="Scanner Used", domain="[('category_id.name', '=', 'Scanner')]")
    scanning_station = fields.Char(string="Scanning Station ID")

    # ============================================================================
    # DELIVERY
    # ============================================================================
    delivery_method = fields.Selection([
        ('portal', 'Customer Portal'),
        ('email', 'Email'),
        ('secure_link', 'Secure Link'),
    ], string="Delivery Method", default='portal')
    email_delivery_address = fields.Char(string="Delivery Email Address")
    file_naming_convention = fields.Selection([('default', 'Default'), ('custom', 'Custom')], string="File Naming", default='default')
    custom_naming_pattern = fields.Char(string="Custom Naming Pattern", help="e.g., {customer_name}_{date}_{sequence}")

    # ============================================================================
    # PROGRESS & ANALYTICS
    # ============================================================================
    progress_percentage = fields.Float(string="Progress (%)", compute='_compute_progress', store=True)
    pages_scanned_count = fields.Integer(string="Pages Scanned", tracking=True)
    pages_processed_count = fields.Integer(string="Pages Processed", tracking=True)
    pages_quality_approved_count = fields.Integer(string="Pages Approved", tracking=True)
    total_file_size_mb = fields.Float(string="Total File Size (MB)", compute='_compute_file_metrics', store=True)
    file_count = fields.Integer(string="File Count", compute='_compute_file_metrics', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Assign a unique work order sequence on creation.

        Behavior:
        - If 'name' is 'New', fetch next sequence 'scan.retrieval.work.order'
        - Returns the created recordset
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('scan.retrieval.work.order') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'total_pages_to_scan')
    def _compute_display_name(self):
        """Compute display_name for user-friendly identification.

        Format: "<sequence> - <customer> - (<pages> pages)" when available.
        """
        for record in self:
            parts = [record.name]
            if record.partner_id:
                parts.append(record.partner_id.name)
            if record.total_pages_to_scan > 0:
                parts.append(_("(%s pages)", record.total_pages_to_scan))
            record.display_name = " - ".join(filter(None, parts))

    @api.depends('scan_item_ids', 'scan_item_ids.page_count')
    def _compute_scan_metrics(self):
        """Compute scan metrics.

        - item_count: number of scan items
        - total_pages_to_scan: sum of page_count over scan_item_ids
        """
        for record in self:
            record.item_count = len(record.scan_item_ids)
            record.total_pages_to_scan = sum(record.scan_item_ids.mapped('page_count'))

    @api.depends('scheduled_date', 'total_pages_to_scan', 'scan_resolution', 'ocr_required', 'image_enhancement')
    def _compute_estimated_completion(self):
        """Estimate completion datetime based on workload and options.

        Heuristic:
        - minutes/page by resolution: 150→0.5, 300→1.0, 600→2.0
        - +0.5 min/page if OCR required
        - +0.2 min/page if image enhancement enabled
        - +120 minutes fixed overhead (setup + quality)
        """
        for record in self:
            if record.scheduled_date and record.total_pages_to_scan > 0:
                minutes_per_page = {'150': 0.5, '300': 1, '600': 2}.get(record.scan_resolution, 1)
                if record.ocr_required:
                    minutes_per_page += 0.5
                if record.image_enhancement:
                    minutes_per_page += 0.2

                total_minutes = record.total_pages_to_scan * minutes_per_page
                total_minutes += 120  # Add 2 hours for setup and quality review
                record.estimated_completion_date = record.scheduled_date + timedelta(minutes=total_minutes)
            else:
                record.estimated_completion_date = False

    @api.depends('pages_scanned_count', 'total_pages_to_scan')
    def _compute_progress(self):
        """Compute progress percentage = scanned_pages / total_pages_to_scan * 100.

        Sets 0 when total_pages_to_scan is 0.
        """
        for record in self:
            if record.total_pages_to_scan > 0:
                record.progress_percentage = (record.pages_scanned_count / record.total_pages_to_scan) * 100
            else:
                record.progress_percentage = 0.0

    @api.depends('digital_asset_ids.file_size')
    def _compute_file_metrics(self):
        """Compute produced file metrics.

        - file_count = len(digital_asset_ids)
        - total_file_size_mb = sum(file_size bytes) / (1024*1024)
        """
        for record in self:
            record.file_count = len(record.digital_asset_ids)
            total_bytes = sum(record.digital_asset_ids.mapped('file_size'))
            record.total_file_size_mb = total_bytes / (1024 * 1024)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Transition draft → confirmed and post a chatter note.

        Guard: only allowed from 'draft'.
        """
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Work order confirmed."))

    def action_start_scanning(self):
        """Transition confirmed → scanning, set actual_start_date, and post a note.

        Guard: only allowed from 'confirmed'.
        """
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Can only start scanning from a confirmed state."))
        self.write({'state': 'scanning', 'actual_start_date': fields.Datetime.now()})
        self.message_post(body=_("Scanning process started."))

    def action_complete_scanning(self):
        """Transition scanning → processing and post a note.

        Guard: only allowed from 'scanning'.
        """
        self.ensure_one()
        if self.state != 'scanning':
            raise UserError(_("Can only complete scanning from the 'Scanning' state."))
        self.write({'state': 'processing'})
        self.message_post(body=_("Scanning completed, starting image processing."))

    def action_start_quality_review(self):
        """Transition processing → quality_review and post a note.

        Guard: only allowed from 'processing'.
        """
        self.ensure_one()
        if self.state != 'processing':
            raise UserError(_("Can only start quality review after processing."))
        self.write({'state': 'quality_review'})
        self.message_post(body=_("Quality review process started."))

    def action_mark_ready_for_delivery(self):
        """Transition quality_review → ready_for_delivery and post a note.

        Guard: only allowed from 'quality_review'.
        """
        self.ensure_one()
        if self.state != 'quality_review':
            raise UserError(_("Can only prepare for delivery after quality review."))
        self.write({'state': 'ready_for_delivery'})
        self.message_post(body=_("Files are ready for delivery."))

    def action_deliver(self):
        """Deliver files via the selected method and transition to 'delivered'.

        Guard: only allowed from 'ready_for_delivery'.
        Notes: Delivery logic placeholder; posts method used to chatter.
        """
        self.ensure_one()
        if self.state != 'ready_for_delivery':
            raise UserError(_("Can only deliver from the 'Ready for Delivery' state."))

        # Placeholder for delivery logic
        delivery_method_str = dict(self._fields['delivery_method'].selection).get(self.delivery_method)
        self.message_post(body=_("Delivering files via %s.", delivery_method_str))

        self.write({'state': 'delivered'})

    def action_complete(self):
        """Transition delivered → completed, set completion timestamp, and post a note.

        Guard: only allowed from 'delivered'.
        """
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed."))
        self.write({'state': 'completed', 'actual_completion_date': fields.Datetime.now()})
        self.message_post(body=_("Work order completed successfully."))

    def action_cancel(self):
        """Cancel the work order and post a note.

        Sets state to 'cancelled' from any state.
        """
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order has been cancelled."))


