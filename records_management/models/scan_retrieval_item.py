from odoo import models, fields, _
from odoo.exceptions import UserError


class ScanRetrievalItem(models.Model):
    _name = 'scan.retrieval.item'
    _description = 'Scan Retrieval Item'
    _inherit = ['retrieval.item.base']  # Now inherits from the new base model
    _rec_name = 'display_name'

    # Scan-specific fields
    document_id = fields.Many2one('records.document', string='Document to Scan')
    file_retrieval_item_id = fields.Many2one('file.retrieval.item', string='Related File Retrieval')

    scan_required = fields.Boolean(string='Scan Required', default=True)
    scan_completed = fields.Boolean(string='Scan Completed')
    scan_start_time = fields.Datetime(string='Scan Start Time', readonly=True)
    scan_completion_time = fields.Datetime(string='Scan Completion Time', readonly=True)

    digital_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpg', 'JPEG'),
        ('png', 'PNG')
    ], string='Digital Format', default='pdf')

    scan_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('archive', 'Archive Quality')
    ], string='Scan Quality', default='high')

    status = fields.Selection(
        selection_add=[
            ('file_retrieved', 'File Retrieved'),
            ('scanning', 'Scanning'),
            ('quality_check', 'Quality Check'),
            ('delivered', 'Delivered'),
            ('rescan_needed', 'Rescan Needed'),
        ],
        ondelete={
            'file_retrieved': 'set default',
            'scanning': 'set default',
            'quality_check': 'set default',
            'delivered': 'set default',
            'rescan_needed': 'set default',
        }
    )

    # ============================================================================
    # NOTE: The following block of fields appears to be incorrectly generated
    # and is the source of many errors. Many are standard fields that should not
    # be redefined (e.g., company_id, create_date). This block should be
    # reviewed and removed or corrected. I have commented it out for now.
    # ============================================================================
    # assigned_user_id = fields.Many2one('assigned.user')
    # ... (rest of the problematic fields) ...
    # write_uid = fields.Char(string='Write Uid')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_start_scanning(self):
        """Mark this item as scanning started"""
        self.ensure_one()
        if self.status not in ['pending', 'file_retrieved', 'rescan_needed']:
            raise UserError(_("Can only start scanning from 'Pending', 'File Retrieved', or 'Rescan Needed' status."))

        self.write({
            'status': 'scanning',
            'scan_start_time': fields.Datetime.now()
        })

        self.message_post(
            body=_("Started scanning item"),
            message_type='notification'
        )

    def action_complete_scanning(self):
        """Mark this item as scanned and move to quality check"""
        self.ensure_one()
        if self.status != 'scanning':
            raise UserError(_("Can only complete scanning from 'Scanning' status."))

        self.write({
            'status': 'quality_check',
            'scan_completion_time': fields.Datetime.now()
        })

        self.message_post(
            body=_("Completed scanning. Awaiting quality check."),
            message_type='notification'
        )

    def action_approve_quality(self):
        """Approve the quality of this scanned item"""
        self.ensure_one()
        if self.status != 'quality_check':
            raise UserError(_("Can only approve quality from 'Quality Check' status."))

        self.write({'status': 'completed'})
        self.message_post(
            body=_("Quality approved for scanned item"),
            message_type='notification'
        )

    def action_request_rescan(self):
        """Request that this item be rescanned due to quality issues"""
        self.ensure_one()
        if self.status not in ['quality_check']:
            raise UserError(_("Can only request rescan from 'Quality Check' status."))

        self.write({
            'status': 'rescan_needed',
            'scan_start_time': False,
            'scan_completion_time': False
        })

        self.message_post(
            body=_("Rescan requested for item"),
            message_type='notification'
        )


