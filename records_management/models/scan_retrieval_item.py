"""
scan_retrieval_item.py

This module defines the ScanRetrievalItem model for the Odoo Records Management system.
It manages the workflow and metadata for scanning requests of physical documents,
including scan status, quality, digital format, and integration with file retrieval items.
The model supports actions for starting scans, completing scans, quality approval,
and requesting rescans, with full audit trail via chatter messages.
"""

from odoo import models, fields, _
from odoo.exceptions import UserError


class ScanRetrievalItem(models.Model):
    """
    ScanRetrievalItem model represents a single scan request for a document within the
    records management workflow. It tracks the scan process, digital output format,
    scan quality, and links to related file retrieval items. The model provides
    business logic for scan lifecycle actions and ensures compliance with
    document handling procedures.
    """

    _name = 'scan.retrieval.item'
    _description = 'Scan Retrieval Item'
    # Inherit from the custom retrieval.item.base model to reuse retrieval item logic
    _inherit = ['retrieval.item.base']
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
            ('completed', 'Completed'),
        ],
        ondelete={
            'file_retrieved': 'set default',
            'scanning': 'set default',
            'quality_check': 'set default',
            'delivered': 'set default',
            'rescan_needed': 'set default',
            'completed': 'set default',
        }
    )

    # ============================================================================
    # NOTE: The following block of fields appears to be incorrectly generated
    # and is the source of many errors. Many are standard fields that should not
    # be redefined (e.g., company_id, create_date). This block should be
    # reviewed and removed or corrected. These have been permanently removed.
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
        """Request a rescan for this item"""
        self.ensure_one()
        if self.status != 'quality_check':
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


