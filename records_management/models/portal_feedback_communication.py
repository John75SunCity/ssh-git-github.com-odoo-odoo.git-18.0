from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PortalFeedbackCommunication(models.Model):
    _name = 'portal.feedback.communication'
    _description = 'Portal Feedback Communication Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'communication_date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    subject = fields.Char(string='Subject', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(default=True)

    feedback_id = fields.Many2one('portal.feedback', string='Related Feedback', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='feedback_id.partner_id', string='Customer', store=True, readonly=True)

    communication_date = fields.Datetime(string='Communication Date', default=fields.Datetime.now, required=True)
    communication_type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('internal_note', 'Internal Note'),
        ('other', 'Other'),
    ], string='Type', default='email', required=True, tracking=True)

    direction = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ], string='Direction', default='outbound', tracking=True)

    message = fields.Html(string='Message Content', required=True)
    
    sender_id = fields.Many2one('res.users', string='Sender (Internal)', default=lambda self: self.env.user)
    recipient_id = fields.Many2one('res.partner', string='Recipient (Customer)')

    response_required = fields.Boolean(string='Response Required?', tracking=True)
    response_deadline = fields.Datetime(string='Response Deadline', tracking=True)
    is_responded = fields.Boolean(string='Responded', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('responded', 'Responded'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('portal.feedback.communication') or _('New')
        return super().create(vals_list)

    def action_send(self):
        """Mark communication as sent and post to feedback chatter."""
        self.ensure_one()
        self.write({'state': 'sent'})
        
        log_body = _("Communication Sent: <strong>%s</strong><br/>%s", self.subject, self.message)
        self.feedback_id.message_post(body=log_body, subtype_xmlid='mail.mt_comment')
        
        # Optionally, send an actual email here if it's an outbound email
        if self.communication_type == 'email' and self.direction == 'outbound':
            # Logic to send email using mail.mail model
            pass

    def action_mark_responded(self):
        """Mark communication as having been responded to."""
        self.ensure_one()
        if not self.response_required:
            raise UserError(_("This communication was not marked as requiring a response."))
            
        self.write({
            'state': 'responded',
            'is_responded': True,
        })
        self.message_post(body=_("Communication has been marked as responded to."))

    def action_cancel(self):
        """Cancel the communication record."""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Communication cancelled."))

