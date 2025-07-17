# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import hashlib

class RecordsDocument(models.Model):
    """Document model for records management, with NAID/ISO compliance."""
    _name = 'records.document'
    _description = 'Records Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Document Reference', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, tracking=True)  # Added to fix KeyError; links to customer
    department_id = fields.Many2one('records.department', string='Department', index=True, tracking=True)  # For departmental access/billing
    box_id = fields.Many2one('records.box', string='Box', tracking=True)
    document_type_id = fields.Many2one('records.document.type', string='Type', tracking=True)
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    content = fields.Html(string='Content/Description', tracking=True)  # For previews in modern UI
    attachment_id = fields.Many2one('ir.attachment', string='Attachment', tracking=True)  # For digital docs; suggest encryption
    hashed_content = fields.Char(compute='_compute_hashed_content', store=True, help='For ISO 27001 integrity checks')
    expiry_date = fields.Date(compute='_compute_expiry_date', store=True, help='Auto for shredding scheduling')
    destruction_method = fields.Selection([
        ('shred', 'Shred (Paper)'), ('crush', 'Crush (Hard Drive)'), ('uniform_shred', 'Uniform Shred')
    ], string='Destruction Method', tracking=True, help='NAID AAA: Ensure particle size <5/8 inch')
    state = fields.Selection([
        ('active', 'Active'), ('archived', 'Archived'), ('destroyed', 'Destroyed')
    ], default='active', tracking=True)
    storage_fee = fields.Float(string='Storage Fee', default=0.0, tracking=True)  # Added for billing computes

    @api.depends('content', 'attachment_id.datas')
    def _compute_hashed_content(self):
        for rec in self:
            data = rec.content or rec.attachment_id.datas or ''
            rec.hashed_content = hashlib.sha256(str(data).encode()).hexdigest()

    @api.depends('retention_policy_id.duration_days')
    def _compute_expiry_date(self):
        for rec in self:
            if rec.retention_policy_id:
                rec.expiry_date = fields.Date.today() + fields.Date.timedelta(days=rec.retention_policy_id.duration_days)
            else:
                rec.expiry_date = False

    @api.constrains('state', 'destruction_method')
    def _check_destruction(self):
        for rec in self:
            if rec.state == 'destroyed' and not rec.destruction_method:
                raise ValidationError(_("Destruction method required for NAID compliance."))

    def action_preview(self):
        """Modern UI: Open attachment preview."""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=ir.attachment&id={self.attachment_id.id}&field=datas&filename_field=name&download=false',
            'target': 'new',
        }

    def action_schedule_destruction(self):
        """Innovative: Auto-create shredding request."""
        shredding = self.env['shredding.service'].create({
            'customer_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'service_type': 'box' if self.box_id else 'hard_drive',
            'shredded_box_ids': [(6, 0, [self.box_id.id])] if self.box_id else False,
        })
        self.message_post(body=_('Destruction scheduled: %s' % shredding.name))
        return shredding