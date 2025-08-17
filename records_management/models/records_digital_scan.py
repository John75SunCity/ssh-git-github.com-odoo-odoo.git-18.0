from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsDigitalScan(models.Model):
    _name = 'records.digital.scan'
    _description = 'Digital Scan of Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    document_id = fields.Many2one()
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    record_date = fields.Date()
    scan_date = fields.Datetime()
    file_format = fields.Selection()
    resolution = fields.Integer(string='Resolution (DPI)')
    file_size = fields.Float(string='File Size (MB)')
    scan_quality = fields.Selection()
    scanner_id = fields.Char()
    scanned_by_id = fields.Many2one()
    sequence = fields.Integer(string='Sequence')
    created_date = fields.Datetime(string='Created Date')
    updated_date = fields.Datetime(string='Updated Date')
    confirmed = fields.Boolean(string='Confirmed')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    scanned_by = fields.Many2one('hr.employee', string='Scanned By')
    scan_info = fields.Char()
    action_confirm = fields.Char(string='Action Confirm')
    action_done = fields.Char(string='Action Done')
    done = fields.Char(string='Done')
    draft = fields.Char(string='Draft')
    group_document = fields.Char(string='Group Document')
    group_format = fields.Char(string='Group Format')
    group_scanned_by = fields.Char(string='Group Scanned By')
    group_state = fields.Selection(string='Group State')
    help = fields.Char(string='Help')
    my_scans = fields.Char(string='My Scans')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_confirm(self):
            """Confirm the digital scan record"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Can only confirm draft scans"))

            self.write()
                {}
                    "state": "confirmed",
                    "confirmed": True,
                    "updated_date": fields.Datetime.now(),



            # Log activity
            self.message_post()
                body=_("Digital scan confirmed by %s", self.env.user.name),
                message_type="notification",



    def action_done(self):
            """Mark the digital scan as completed"""

            self.ensure_one()
            if self.state not in ["draft", "confirmed"]:
                raise UserError(_("Can only complete draft or confirmed scans"))

            self.write({"state": "done", "updated_date": fields.Datetime.now()})

            # Log activity
            self.message_post()
                body=_("Digital scan completed by %s", self.env.user.name),
                message_type="notification",



    def action_reset_to_draft(self):
            """Reset to draft state"""

            self.ensure_one()
            self.write()
                {}
                    "state": "draft",
                    "confirmed": False,
                    "updated_date": fields.Datetime.now(),



            # Log activity
            self.message_post()
                body=_("Digital scan reset to draft by %s", self.env.user.name),
                message_type="notification",


        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_scan_info(self):
            """Compute scan information display"""
            for record in self:
                info_parts = []
                if record.resolution:
                    info_parts.append(_("%s DPI", record.resolution))
                if record.file_size:
                    info_parts.append(_("%.2f MB", record.file_size))
                record.scan_info = ()
                    " - ".join(info_parts) if info_parts else _("No scan info"):



    def _check_file_size(self):
            for record in self:
                if record.file_size and record.file_size < 0:
                    raise ValidationError(_("File size cannot be negative"))
                if record.file_size and record.file_size > 1000:  # 1GB limit
                    raise ValidationError(_("File size cannot exceed 1000 MB"))


    def _check_resolution(self):
            for record in self:
                if record.resolution and record.resolution < 50:
                    raise ValidationError(_("Resolution must be at least 50 DPI"))
                if record.resolution and record.resolution > 10000:
                    raise ValidationError(_("Resolution cannot exceed 10000 DPI"))
