from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models


class PortalFeedbackCommunication(models.Model):
    _name = 'portal.feedback.communication'
    _description = 'Portal Feedback Communication'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'feedback_id, communication_date desc'
    _rec_name = 'subject'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    subject = fields.Char(string='Subject', required=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    feedback_id = fields.Many2one()
    communication_date = fields.Datetime()
    communication_type = fields.Selection()
    direction = fields.Selection()
    message = fields.Text(string='Message Content')
    sender_id = fields.Many2one('res.users')
    recipient_id = fields.Many2one('res.partner')
    channel = fields.Char(string='Communication Channel')
    response_required = fields.Boolean()
    response_deadline = fields.Datetime(string='Response Deadline')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            """Override create to add auto-numbering"""
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name'] = self.env['ir.sequence'].next_by_code('portal.feedback.communication') or _('New')
            return super().create(vals_list)

    def action_mark_responded(self):
            """Mark communication as responded"""
            self.ensure_one()
            self.write({"response_required": False})
            self.message_post()
                body=_("Communication has been responded to."), message_type="notification"



    def action_send_followup(self):
            """Send a follow-up communication"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Send Follow-up"),
                "res_model": "communication.followup.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_original_communication_id": self.id})))))

