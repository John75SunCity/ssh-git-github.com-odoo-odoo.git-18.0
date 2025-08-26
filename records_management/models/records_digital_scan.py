from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDigitalScan(models.Model):
    _name = 'records.digital.scan'
    _description = 'Digital Scan of Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_id, sequence, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Scan Name", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Order of the scan within the document.")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    document_id = fields.Many2one('records.document', string="Parent Document", required=True, ondelete='cascade', tracking=True)
    scanned_by_id = fields.Many2one('hr.employee', string='Scanned By', tracking=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SCAN DETAILS
    # ============================================================================
    description = fields.Text(string='Description')
    notes = fields.Text(string='Internal Notes')
    scan_date = fields.Datetime(string="Scan Date", default=fields.Datetime.now, required=True, tracking=True)
    file_format = fields.Selection([
        ('pdf', 'PDF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
        ('tiff', 'TIFF'),
    ], string="File Format", default='pdf', required=True, tracking=True)
    resolution = fields.Integer(string='Resolution (DPI)', default=300, tracking=True)
    file_size = fields.Float(string='File Size (MB)', tracking=True)
    scan_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('archival', 'Archival'),
    ], string="Scan Quality", default='medium', tracking=True)
    scanner_id = fields.Char(string="Scanner ID/Name", help="Identifier for the scanning hardware used.")
    scan_info = fields.Char(string="Scan Info", compute='_compute_scan_info', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.digital.scan') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('resolution', 'file_size')
    def _compute_scan_info(self):
        """Compute a display string for key scan information."""
        for record in self:
            info_parts = []
            if record.resolution:
                info_parts.append(_("%s DPI") % record.resolution)
            if record.file_size:
                info_parts.append(_("%.2f MB") % record.file_size)
            record.scan_info = " - ".join(info_parts) if info_parts else _("No scan info")

    @api.constrains('file_size', 'resolution')
    def _check_scan_parameters(self):
        """Validate scan parameters are within reasonable limits."""
        for record in self:
            if record.file_size < 0:
                raise ValidationError(_("File size cannot be negative."))
            if record.file_size > 2048:  # 2GB limit
                raise ValidationError(_("File size cannot exceed 2048 MB."))
            if record.resolution and (record.resolution < 50 or record.resolution > 1200):
                raise ValidationError(_("Resolution must be between 50 and 1200 DPI."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the digital scan record."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft scans can be confirmed."))
    self.write({"state": "confirmed"})
    self.message_post(body=_("Digital scan confirmed by %s.") % self.env.user.name)
    return True

    def action_done(self):
        """Mark the digital scan as completed."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed scans can be marked as done."))
    self.write({"state": "done"})
    self.message_post(body=_("Digital scan completed by %s.") % self.env.user.name)
    return True

    def action_reset_to_draft(self):
        """Reset the scan to the draft state."""
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Cannot reset a completed scan to draft."))
    self.write({"state": "draft"})
    self.message_post(body=_("Digital scan reset to draft by %s.") % self.env.user.name)
    return True
