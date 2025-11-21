# -*- coding: utf-8 -*-
"""
Barcode Reprint Wizards
=======================

Wizards for handling barcode label reprints with signature authorization.
Ensures accountability when reprinting labels that have already been printed.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BarcodeReprintWizard(models.TransientModel):
    """
    Wizard for reprinting a single barcode label with signature authorization.
    
    Triggered when attempting to print a label for a container/folder that
    already has a printed label. Requires electronic signature before proceeding.
    """
    _name = 'barcode.reprint.wizard'
    _description = 'Barcode Reprint Authorization'
    
    container_id = fields.Many2one(
        'records.container',
        string='Container',
    )
    
    file_id = fields.Many2one(
        'records.file',
        string='File Folder',
    )
    
    record_type = fields.Selection([
        ('container', 'Container'),
        ('folder', 'File Folder'),
    ], string='Record Type', required=True)
    
    barcode = fields.Char(
        string='Barcode',
        readonly=True,
        help='The barcode that will be reprinted',
    )
    
    previous_print_date = fields.Datetime(
        string='Previous Print Date',
        readonly=True,
        help='When this barcode was last printed',
    )
    
    reason = fields.Text(
        string='Reprint Reason',
        required=True,
        help='Explain why this barcode needs to be reprinted (e.g., "Label damaged", "Lost label", etc.)',
    )
    
    signature = fields.Binary(
        string='Authorization Signature',
        required=True,
        help='Electronic signature authorizing this reprint',
    )
    
    signature_name = fields.Char(
        string='Signature Name',
        compute='_compute_signature_name',
        store=True,
    )
    
    warning_acknowledged = fields.Boolean(
        string='I understand this creates a duplicate barcode',
        required=True,
    )
    
    @api.depends('signature')
    def _compute_signature_name(self):
        """Set signature name to current user"""
        for wizard in self:
            wizard.signature_name = self.env.user.name if wizard.signature else False
    
    @api.constrains('warning_acknowledged')
    def _check_warning_acknowledged(self):
        """Ensure user acknowledged the warning"""
        for wizard in self:
            if not wizard.warning_acknowledged:
                raise ValidationError(_("You must acknowledge the duplicate barcode warning before proceeding."))
    
    def action_confirm_reprint(self):
        """
        Process the approved reprint request.
        
        - Generates new label PDF
        - Logs the reprint with signature in chatter
        - Attaches PDF for future reference
        - Returns download action
        """
        self.ensure_one()
        
        if not self.signature:
            raise UserError(_("Electronic signature is required to authorize barcode reprint."))
        
        # Determine which record to print
        if self.record_type == 'container':
            record = self.container_id
            model_name = 'records.container'
        else:
            record = self.file_id
            model_name = 'records.file'
        
        if not record:
            raise UserError(_("No record selected for reprint."))
        
        # Generate the label
        generator = self.env['zpl.label.generator']
        
        if self.record_type == 'container':
            result = generator.generate_container_label(record)
        else:
            result = generator.generate_folder_label(record)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f"{result['filename']}_REPRINT",
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': model_name,
            'res_id': record.id,
            'mimetype': 'application/pdf',
            'description': f"REPRINT authorized by {self.env.user.name}: {self.reason}",
        })
        
        # Create signature attachment
        signature_attachment = self.env['ir.attachment'].create({
            'name': f"reprint_signature_{self.barcode}_{fields.Datetime.now()}.png",
            'type': 'binary',
            'datas': self.signature,
            'res_model': model_name,
            'res_id': record.id,
            'mimetype': 'image/png',
            'description': f"Authorization signature for barcode reprint by {self.env.user.name}",
        })
        
        # Log in chatter with signature
        record.message_post(
            body=_("""
                <p><strong>⚠️ BARCODE LABEL REPRINTED</strong></p>
                <p><strong>Barcode:</strong> %s</p>
                <p><strong>Previous Print:</strong> %s</p>
                <p><strong>Authorized By:</strong> %s</p>
                <p><strong>Reason:</strong> %s</p>
                <p><strong>⚠️ WARNING:</strong> Duplicate barcode label created. Destroy old label immediately.</p>
            """) % (
                self.barcode,
                self.previous_print_date,
                self.env.user.name,
                self.reason,
            ),
            subject=_("⚠️ Barcode Reprint Authorized"),
            attachment_ids=[attachment.id, signature_attachment.id],
        )
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class BarcodeBatchReprintWizard(models.TransientModel):
    """
    Wizard for batch reprinting with signature authorization.
    
    Used when batch printing includes containers/folders that already
    have printed labels. Requires signature to authorize reprinting all.
    """
    _name = 'barcode.batch.reprint.wizard'
    _description = 'Batch Barcode Reprint Authorization'
    
    container_ids = fields.Many2many(
        'records.container',
        string='All Containers',
        help='All containers selected for batch print',
    )
    
    file_ids = fields.Many2many(
        'records.file',
        string='All Folders',
        help='All folders selected for batch print',
    )
    
    reprint_ids = fields.Many2many(
        'records.container',
        'batch_reprint_container_rel',
        string='Previously Printed',
        help='Containers/folders that already have printed labels',
    )
    
    reprint_file_ids = fields.Many2many(
        'records.file',
        'batch_reprint_file_rel',
        string='Previously Printed Folders',
    )
    
    record_type = fields.Selection([
        ('container', 'Container'),
        ('folder', 'File Folder'),
    ], string='Record Type', required=True)
    
    total_count = fields.Integer(
        string='Total Labels',
        compute='_compute_counts',
    )
    
    reprint_count = fields.Integer(
        string='Reprints',
        compute='_compute_counts',
    )
    
    reason = fields.Text(
        string='Batch Reprint Reason',
        required=True,
        help='Explain why these barcodes need to be reprinted',
    )
    
    signature = fields.Binary(
        string='Authorization Signature',
        required=True,
        help='Electronic signature authorizing this batch reprint',
    )
    
    warning_acknowledged = fields.Boolean(
        string='I understand this creates duplicate barcodes',
        required=True,
    )
    
    @api.depends('container_ids', 'reprint_ids', 'file_ids', 'reprint_file_ids')
    def _compute_counts(self):
        """Calculate total and reprint counts"""
        for wizard in self:
            if wizard.record_type == 'container':
                wizard.total_count = len(wizard.container_ids)
                wizard.reprint_count = len(wizard.reprint_ids)
            else:
                wizard.total_count = len(wizard.file_ids)
                wizard.reprint_count = len(wizard.reprint_file_ids)
    
    def action_confirm_batch_reprint(self):
        """Process batch reprint with signature"""
        self.ensure_one()
        
        if not self.signature:
            raise UserError(_("Electronic signature required for batch reprint authorization."))
        
        # Determine records
        if self.record_type == 'container':
            records = self.container_ids
            generator_method = 'generate_batch_container_labels'
        else:
            records = self.file_ids
            generator_method = 'generate_batch_folder_labels'
        
        # Generate batch labels
        generator = self.env['zpl.label.generator']
        result = getattr(generator, generator_method)(records)
        
        # Create batch tracking
        batch_record = self.env['barcode.batch.print'].create({
            'record_type': self.record_type,
            'record_count': len(records),
            'printed_by_id': self.env.user.id,
            'print_date': fields.Datetime.now(),
        })
        
        # Create PDF attachment
        attachment = self.env['ir.attachment'].create({
            'name': f"{result['filename']}_BATCH_REPRINT",
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': batch_record._name,
            'res_id': batch_record.id,
            'mimetype': 'application/pdf',
            'description': f"Batch reprint authorized by {self.env.user.name}: {self.reason}",
        })
        
        batch_record.attachment_id = attachment.id
        
        # Create signature attachment
        signature_attachment = self.env['ir.attachment'].create({
            'name': f"batch_reprint_signature_{fields.Datetime.now()}.png",
            'type': 'binary',
            'datas': self.signature,
            'res_model': batch_record._name,
            'res_id': batch_record.id,
            'mimetype': 'image/png',
        })
        
        # Log in batch record
        batch_record.message_post(
            body=_("""
                <p><strong>⚠️ BATCH REPRINT AUTHORIZED</strong></p>
                <p><strong>Total Labels:</strong> %s</p>
                <p><strong>Reprints:</strong> %s</p>
                <p><strong>Authorized By:</strong> %s</p>
                <p><strong>Reason:</strong> %s</p>
            """) % (
                self.total_count,
                self.reprint_count,
                self.env.user.name,
                self.reason,
            ),
            subject=_("Batch Reprint Authorized"),
            attachment_ids=[signature_attachment.id],
        )
        
        # Log in each record's chatter
        reprint_records = self.reprint_ids if self.record_type == 'container' else self.reprint_file_ids
        
        for record in records:
            is_reprint = record in reprint_records
            record.message_post(
                body=_("Included in batch %s<br/>%s") % (
                    batch_record.name,
                    "⚠️ <strong>REPRINT - Destroy old label</strong>" if is_reprint else "New print"
                ),
                subject=_("Batch Label Printed"),
            )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class BatchLabelErrorWizard(models.TransientModel):
    """Wizard for handling batch label printing errors (missing barcodes, etc.)"""
    _name = 'batch.label.error.wizard'
    _description = 'Batch Label Error Handler'
    
    container_ids = fields.Many2many(
        'records.container',
        'batch_error_container_rel',
        string='All Selected Containers',
    )
    
    missing_barcode_ids = fields.Many2many(
        'records.container',
        'batch_error_missing_rel',
        string='Containers Missing Barcodes',
    )
    
    error_type = fields.Selection([
        ('missing_barcode', 'Missing Barcodes'),
        ('api_failure', 'API Connection Failed'),
    ], string='Error Type', default='missing_barcode')
    
    error_message = fields.Text(
        string='Error Details',
        compute='_compute_error_message',
    )
    
    @api.depends('missing_barcode_ids', 'error_type')
    def _compute_error_message(self):
        """Generate helpful error message"""
        for wizard in self:
            if wizard.error_type == 'missing_barcode':
                wizard.error_message = _(
                    "The following %s containers do not have barcodes assigned:\n\n%s\n\n"
                    "Please assign barcodes to these containers before printing labels."
                ) % (
                    len(wizard.missing_barcode_ids),
                    '\n'.join(f"- {c.name}" for c in wizard.missing_barcode_ids)
                )
            else:
                wizard.error_message = _("Error connecting to label printing service. Please try again.")
    
    def action_print_valid_only(self):
        """Print labels for containers that have barcodes, skip the rest"""
        self.ensure_one()
        
        valid_containers = self.container_ids - self.missing_barcode_ids
        
        if not valid_containers:
            raise UserError(_("No valid containers to print."))
        
        # Call batch print with valid containers only
        return self.env['records.container'].action_print_batch_labels(
            container_ids=valid_containers.ids
        )
    
    def action_cancel(self):
        """Cancel and return to container list"""
        return {'type': 'ir.actions.act_window_close'}
