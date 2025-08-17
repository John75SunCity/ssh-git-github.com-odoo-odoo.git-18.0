from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ScanRetrievalWorkOrder(models.Model):
    _name = 'scan.retrieval.work.order'
    _description = 'Scan Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.integration.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    priority = fields.Selection()
    partner_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    scan_request_description = fields.Text()
    scan_item_ids = fields.One2many()
    item_count = fields.Integer()
    total_pages_to_scan = fields.Integer()
    scan_resolution = fields.Selection()
    color_mode = fields.Selection()
    output_format = fields.Selection()
    container_ids = fields.Many2many()
    file_ids = fields.Many2many()
    location_ids = fields.Many2many()
    scheduled_date = fields.Datetime()
    estimated_completion_date = fields.Datetime()
    actual_start_date = fields.Datetime()
    actual_completion_date = fields.Datetime()
    scanner_id = fields.Many2one()
    scanning_station = fields.Char()
    ocr_required = fields.Boolean()
    image_enhancement = fields.Boolean()
    auto_crop = fields.Boolean()
    deskew = fields.Boolean()
    delivery_method = fields.Selection()
    email_delivery_address = fields.Char()
    file_naming_convention = fields.Selection()
    custom_naming_pattern = fields.Char()
    progress_percentage = fields.Float()
    pages_scanned_count = fields.Integer()
    pages_processed_count = fields.Integer()
    pages_quality_approved_count = fields.Integer()
    average_scan_quality = fields.Float()
    rescan_required_count = fields.Integer()
    total_file_size_mb = fields.Float()
    file_count = fields.Integer()
    digital_asset_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    coordinator_id = fields.Many2one('work.order.coordinator')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code()
                        'scan.retrieval.work.order') or _('New'
            return super().create(vals_list)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            for record in self:
                if record.partner_id and record.total_pages_to_scan:
                    record.display_name = _("%s - %s (%s pages)",
                        record.name, record.partner_id.name, record.total_pages_to_scan
                elif record.partner_id:
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New Scan Retrieval")


    def _compute_scan_metrics(self):
            for record in self:
                items = record.scan_item_ids
                record.item_count = len(items)
                record.total_pages_to_scan = sum(items.mapped('page_count')) if items else 0:

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


    def _compute_progress(self):
            for record in self:
                if record.total_pages_to_scan > 0:
                    record.progress_percentage = (record.pages_scanned_count / record.total_pages_to_scan) * 100
                else:
                    record.progress_percentage = 0.0


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


