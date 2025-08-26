from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PortalFeedbackEscalation(models.Model):
    _name = 'portal.feedback.escalation'
    _description = 'Portal Feedback Escalation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'escalation_date desc, id desc'

    name = fields.Char(string='Escalation Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(default=True)

    feedback_id = fields.Many2one('portal.feedback', string='Related Feedback', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one(related='feedback_id.partner_id', string='Customer', store=True, readonly=True)

    escalation_date = fields.Datetime(string='Escalation Date', default=fields.Datetime.now, required=True, readonly=True)
    escalated_by_id = fields.Many2one('res.users', string='Escalated By', default=lambda self: self.env.user, required=True, tracking=True)
    escalated_to_id = fields.Many2one('res.users', string='Assigned To', tracking=True)

    escalation_reason = fields.Text(string='Reason for Escalation', required=True)

    escalation_level = fields.Selection([
        ('level_1', 'Level 1'),
        ('level_2', 'Level 2'),
        ('management', 'Management'),
    ], string='Escalation Level', default='level_1', tracking=True)

    deadline = fields.Datetime(string='Resolution Deadline', tracking=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', readonly=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering and link to feedback."""
        records = super().create(vals_list)
        for record in records:
            if record.name == _('New'):
                record.name = self.env['ir.sequence'].next_by_code('portal.feedback.escalation') or _('New')

            # Post a message on the original feedback record
            log_body = _(
                "Feedback escalated to %s by %s.<br/>Reason: %s"
            ) % (
                record.escalated_to_id.name if record.escalated_to_id else 'the appropriate team',
                record.escalated_by_id.name,
                record.escalation_reason
            )
            record.feedback_id.message_post(body=log_body)
        return records

    def action_acknowledge(self):
        """Acknowledge the escalation."""
        self.ensure_one()
        if self.state != "pending":
            raise UserError(_("Only pending escalations can be acknowledged."))
    self.write({"state": "acknowledged"})
    self.message_post(body=_("Escalation has been acknowledged by %s.") % self.env.user.name)

    def action_start_progress(self):
        """Start working on the escalation."""
        self.ensure_one()
        if self.state not in ["pending", "acknowledged"]:
            raise UserError(_("Can only start progress on pending or acknowledged escalations."))
        self.write({"state": "in_progress"})
        self.message_post(body=_("Work has started on this escalation."))

    def action_resolve(self):
        """Mark escalation as resolved."""
        self.ensure_one()
        if self.state not in ['acknowledged', 'in_progress']:
            raise UserError(_("Only acknowledged or in-progress escalations can be resolved."))
        self.write({"state": "resolved"})
        self.message_post(body=_("Escalation has been marked as resolved."))

    def action_cancel(self):
        """Cancel the escalation."""
        self.ensure_one()
        self.write({"state": "cancelled"})
        self.message_post(body=_("Escalation has been cancelled."))


