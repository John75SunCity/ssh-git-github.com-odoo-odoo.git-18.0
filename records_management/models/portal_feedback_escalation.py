from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PortalFeedbackEscalation(models.Model):
    _name = 'portal.feedback.escalation'
    _description = 'Portal Feedback Escalation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'feedback_id, escalation_date desc'
    _rec_name = 'feedback_id'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    feedback_id = fields.Many2one()
    escalation_date = fields.Datetime()
    escalated_by_id = fields.Many2one()
    escalated_to_id = fields.Many2one()
    escalation_reason = fields.Text(string='Escalation Reason')
    escalation_level = fields.Selection()
    urgency = fields.Selection()
    deadline = fields.Datetime(string='Response Deadline')
    status = fields.Selection()
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
                    vals['name'] = self.env['ir.sequence'].next_by_code('portal.feedback.escalation') or _('New')
            return super().create(vals_list)

    def action_acknowledge(self):
            """Acknowledge the escalation"""
            self.ensure_one()
            if self.status != "pending":
                raise UserError(_("Only pending escalations can be acknowledged."))

            self.write({"status": "acknowledged"})
            self.message_post()
                body=_("Escalation has been acknowledged."), message_type="notification"



    def action_start_progress(self):
            """Start working on the escalation"""
            self.ensure_one()
            if self.status not in ["pending", "acknowledged"]:
                raise UserError()
                    _("Can only start progress on pending or acknowledged escalations.")


            self.write({"status": "in_progress"})
            self.message_post()
                body=_("Work has started on this escalation."), message_type="notification"



    def action_resolve(self):
            """Mark escalation as resolved"""
            self.ensure_one()
            self.write({"status": "resolved"})
            self.message_post()
                body=_("Escalation has been resolved."), message_type="notification"


