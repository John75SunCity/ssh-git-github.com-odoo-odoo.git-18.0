from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ScanRetrieval(models.Model):
    _name = 'scan.retrieval'
    _description = 'Scan Retrieval Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Core identification
    name = fields.Char(string='Scan Reference', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # Source document/file
    document_id = fields.Many2one('records.document', string='Document')
    file_retrieval_id = fields.Many2one('file.retrieval', string='Related File Retrieval')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)

    # Scanning specifications
    scan_required = fields.Boolean(string='Scan Required', default=True)
    scan_completed = fields.Boolean(string='Scan Completed')
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

    # Status workflow
    status = fields.Selection([
        ('pending', 'Pending'),
        ('retrieved', 'Retrieved for Scan'),
        ('scanning', 'Scanning in Progress'),
        ('completed', 'Scan Completed'),
        ('quality_check', 'Quality Check'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned')
    ], string='Status', default='pending', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')

    # Quality control
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_issues = fields.Text(string='Quality Issues')
    completeness_verified = fields.Boolean(string='Completeness Verified')

    # Return handling
    return_required = fields.Boolean(string='Return Required', default=True)
    return_date = fields.Date(string='Return Date')
    return_location_id = fields.Many2one('records.location', string='Return Location')
    return_notes = fields.Text(string='Return Notes')

    # Timing
    estimated_time = fields.Float(string='Estimated Scan Time (hours)')
    actual_time = fields.Float(string='Actual Scan Time (hours)')
    scan_date = fields.Datetime(string='Scan Date')

    # Display
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.depends('name', 'digital_format', 'scan_quality')
    def _compute_display_name(self):
        for record in self:
            parts = [record.name or "New Scan"]
            if record.digital_format and record.scan_quality:
                parts.append(f"({record.digital_format.upper()} - {record.scan_quality.title()})")
            record.display_name = " ".join(parts)

    def action_start_scanning(self):
        """Start the scanning process"""
        for record in self:
            if record.status != 'retrieved':
                raise UserError(_("Document must be retrieved before scanning."))
            record.write({
                'status': 'scanning',
                'scan_date': fields.Datetime.now()
            })
            record.message_post(body=_("Scanning started by %s") % self.env.user.name)

    def action_complete_scan(self):
        """Mark scanning as completed"""
        for record in self:
            if record.status != 'scanning':
                raise UserError(_("Scanning must be in progress to complete."))
            record.write({
                'status': 'completed',
                'scan_completed': True
            })
            record.message_post(body=_("Scanning completed by %s") % self.env.user.name)

    def action_quality_check(self):
        """Perform quality check on scanned documents"""
        for record in self:
            if record.status != 'completed':
                raise UserError(_("Scan must be completed before quality check."))
            record.write({
                'status': 'quality_check',
                'quality_checked': True
            })
            record.message_post(body=_("Quality check performed by %s") % self.env.user.name)
