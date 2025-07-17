# -*- coding: utf-8 -*-
import hashlib
from odoo import fields, models, api, _

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Portal Request for Services (e.g., Destruction, Shredding)'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # For tracking and notifications

    name = fields.Char(string='Request Reference', required=True, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, domain="[('is_company', '=', True)]", 
                                 help='Linked customer for NAID auditing and ownership checks.')
    request_type = fields.Selection([
        ('destruction', 'Document Destruction'),
        ('shredding', 'Shredding Service'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform', 'Uniform Shredding'),
    ], string='Request Type', required=True)
    description = fields.Text(string='Description')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', track_visibility='onchange')
    hashed_partner_ref = fields.Char(string='Hashed Partner Reference', compute='_compute_hashed_partner_ref', store=True, 
                                     help='ISO-compliant hashed reference for secure auditing without exposing PII.')
    linked_visitor_id = fields.Many2one('frontdesk.visitor', string='Linked Visit', readonly=True, 
                                        help='Associated frontdesk visit for walk-in services (NAID traceable).')
    is_walk_in = fields.Boolean(string='Walk-in Request', default=False, 
                                help='Flag if this is a walk-in shred/destruction request.')

    @api.depends('partner_id')
    def _compute_hashed_partner_ref(self):
        """Compute hashed partner ref for data integrity/encryption (ISO 27001)."""
        for rec in self:
            if rec.partner_id:
                rec.hashed_partner_ref = hashlib.sha256(str(rec.partner_id.id).encode()).hexdigest()
            else:
                rec.hashed_partner_ref = False

    @api.model
    def create(self, vals):
        """Override create to auto-sequence name, notify partner, and auto-link to visitor if context provides."""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('portal.request') or _('New')
        res = super(PortalRequest, self).create(vals)
        if res.partner_id:
            res.message_post(body=_('New request created: %s') % res.name, partner_ids=[res.partner_id.id])
        # Innovative: Auto-link to visitor from context (e.g., if created via POS wizard)
        if self.env.context.get('visitor_id'):
            res.linked_visitor_id = self.env.context['visitor_id']
            res.is_walk_in = True
        return res

    def write(self, vals):
        """Override write to log changes for auditing (NAID compliance)."""
        res = super(PortalRequest, self).write(vals)
        if 'status' in vals or 'request_type' in vals:
            self.env['mail.activity'].create({
                'res_id': self.id,
                'res_model': self._name,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Request Updated'),
                'note': _('Status or type changed; NAID audit trail updated.'),
            })
        return res

    def action_submit(self):
        """Submit request and update status for auditing."""
        self.write({'status': 'submitted'})
        self.env['mail.activity'].create({
            'res_id': self.id,
            'res_model': self._name,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': _('Request Submitted'),
            'note': _('Submitted for approval; NAID audit trail updated.'),
        })

    def action_approve(self):
        """Approve request, update status, and notify for workflow (innovative automation)."""
        self.write({'status': 'approved'})
        self.message_post(body=_('Request approved and ready for processing.'), subtype_xmlid='mail.mt_note')
        if self.linked_visitor_id:
            self.linked_visitor_id.message_post(body=_('Linked request approved: %s') % self.name)
