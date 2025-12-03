# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class DocumentUploadWizard(models.TransientModel):
    """
    Wizard for bulk document upload to file folders.
    
    Features:
    - Multiple file upload support
    - Automatic document creation with metadata
    - Barcode generation for uploaded documents  
    - Association with specific file folder
    """
    _name = 'document.upload.wizard'
    _description = 'Document Upload Wizard'

    # File folder selection
    file_id = fields.Many2one(
        comodel_name='records.file',
        string='File Folder',
        required=True,
        help="Target file folder for document upload"
    )
    
    # Document upload fields
    document_name = fields.Char(
        string='Document Name',
        required=True,
        help="Name for the uploaded document"
    )
    
    document_type_id = fields.Many2one(
        comodel_name='records.document.type',
        string='Document Type',
        required=True,
        help="Type/category of the document"
    )
    
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Files to Upload',
        help="Select one or more PDF files to upload"
    )
    
    # Document metadata
    received_date = fields.Date(
        string='Received Date',
        default=fields.Date.context_today,
        help="Date when document was received"
    )
    
    description = fields.Text(
        string='Description',
        help="Additional notes about the document(s)"
    )
    
    # Options
    generate_barcode = fields.Boolean(
        string='Generate Barcodes',
        default=True,
        help="Automatically generate barcodes for uploaded documents"
    )
    
    auto_assign_sequence = fields.Boolean(
        string='Auto-assign Document Numbers',
        default=True,
        help="Automatically assign sequential document numbers"
    )

    @api.model
    def default_get(self, fields_list):
        """Set default file_id from context"""
        res = super().default_get(fields_list)
        if 'file_id' in fields_list:
            file_id = self.env.context.get('default_file_id')
            if file_id:
                res['file_id'] = file_id
        return res

    def action_upload_documents(self):
        """
        Process document upload and create records.document entries.
        
        Returns: Action to view created documents
        """
        self.ensure_one()
        
        if not self.attachment_ids:
            raise UserError(_("Please select at least one file to upload."))
        
        if not self.file_id:
            raise UserError(_("Please select a target file folder."))
        
        created_documents = self.env['records.document']
        
        for i, attachment in enumerate(self.attachment_ids):
            try:
                # Create document name with sequence if multiple files
                if len(self.attachment_ids) > 1 and self.auto_assign_sequence:
                    doc_name = f"{self.document_name} - {i + 1:03d}"
                else:
                    doc_name = self.document_name
                
                # Create document record
                document_vals = {
                    'name': doc_name,
                    'file_id': self.file_id.id,
                    'document_type_id': self.document_type_id.id,
                    'partner_id': self.file_id.partner_id.id if self.file_id.partner_id else False,
                    'received_date': self.received_date,
                    'description': self.description,
                }
                
                document = self.env['records.document'].create(document_vals)
                
                # Associate attachment with document
                attachment.write({
                    'res_model': 'records.document',
                    'res_id': document.id,
                    'name': f"{doc_name}_{attachment.name}",
                })
                
                # Generate barcode if requested
                if self.generate_barcode and hasattr(document, 'action_generate_document_barcode'):
                    try:
                        document.action_generate_document_barcode()
                    except Exception as e:
                        _logger.warning("Failed to generate barcode for document %s: %s", document.id, str(e))
                
                created_documents |= document
                
            except Exception as e:
                _logger.error("Failed to create document from attachment %s: %s", attachment.name, str(e))
                raise UserError(
                    _("Failed to process file '%s': %s") % (attachment.name, str(e))
                )
        
        # Log success
        _logger.info("Successfully uploaded %d documents to file folder %s", len(created_documents), self.file_id.name)
        
        # Return action to view created documents
        if len(created_documents) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Uploaded Document'),
                'res_model': 'records.document',
                'res_id': created_documents.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Uploaded Documents'),
                'res_model': 'records.document',
                'domain': [('id', 'in', created_documents.ids)],
                'view_mode': 'list,form',
                'target': 'current',
                'context': {'search_default_file_id': self.file_id.id}
            }

    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}
