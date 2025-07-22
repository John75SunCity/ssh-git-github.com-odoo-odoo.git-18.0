from odoo import models, fields, api

class RecordsChainOfCustody(models.Model):
    _name = 'records.chain.of.custody'
    _description = 'Document Chain of Custody'
    _order = 'event_date desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    event_date = fields.Datetime('Event Date', required=True, default=fields.Datetime.now)
    event_type = fields.Selection([
        ('creation', 'Document Creation'),
        ('receipt', 'Receipt'),
        ('storage', 'Storage'),
        ('access', 'Access/Retrieval'),
        ('transfer', 'Transfer'),
        ('scan', 'Scanning/Digitization'),
        ('destruction', 'Destruction')
    ], string='Event Type', required=True)
    
    responsible_person = fields.Char('Responsible Person', required=True)
    location = fields.Char('Location', required=True)
    signature_verified = fields.Boolean('Signature Verified', default=False)
    notes = fields.Text('Notes')
    
    # Audit fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    created_on = fields.Datetime('Created On', default=fields.Datetime.now, readonly=True)

class RecordsAuditTrail(models.Model):
    _name = 'records.audit.trail'
    _description = 'Document Audit Trail'
    _order = 'timestamp desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    timestamp = fields.Datetime('Timestamp', required=True, default=fields.Datetime.now)
    action_type = fields.Selection([
        ('create', 'Created'),
        ('read', 'Accessed'),
        ('update', 'Modified'),
        ('delete', 'Deleted'),
        ('move', 'Moved'),
        ('scan', 'Scanned'),
        ('export', 'Exported'),
        ('print', 'Printed'),
        ('email', 'Emailed'),
        ('archive', 'Archived'),
        ('destroy', 'Destroyed')
    ], string='Action Type', required=True)
    
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    description = fields.Text('Description', required=True)
    compliance_verified = fields.Boolean('Compliance Verified', default=False)
    
    # Additional audit fields
    ip_address = fields.Char('IP Address')
    browser_info = fields.Char('Browser Info')

class RecordsDigitalCopy(models.Model):
    _name = 'records.digital.copy'
    _description = 'Document Digital Copy'
    _order = 'scan_date desc'

    document_id = fields.Many2one('records.document', string='Document', required=True, ondelete='cascade')
    scan_date = fields.Datetime('Scan Date', required=True, default=fields.Datetime.now)
    file_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('docx', 'DOCX'),
        ('txt', 'TXT')
    ], string='File Format', required=True)
    
    resolution = fields.Char('Resolution (DPI)')
    file_size = fields.Float('File Size (MB)')
    storage_location = fields.Char('Storage Location', required=True)
    checksum = fields.Char('File Checksum')
    
    # Scan metadata
    scanned_by = fields.Many2one('res.users', string='Scanned By', default=lambda self: self.env.user)
    scanner_device = fields.Char('Scanner Device')
    scan_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('archive', 'Archive Quality')
    ], string='Scan Quality', default='medium')
    
    # File access
    file_attachment_id = fields.Many2one('ir.attachment', string='File Attachment')
    
    def action_download(self):
        """Download the digital copy file"""
        if self.file_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.file_attachment_id.id}?download=true',
                'target': 'self',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No File Available',
                    'message': 'No digital file is attached to this record.',
                    'type': 'warning',
                }
            }
