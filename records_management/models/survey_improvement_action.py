from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SurveyImprovementAction(models.Model):
    _name = 'survey.improvement.action'
    _description = 'Survey Improvement Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, sequence, create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string='Action Title',
        required=True,
        tracking=True,
        help="A concise title for the improvement action."
    )
    description = fields.Html(
        string='Detailed Description',
        help="A full description of the action to be taken, including goals and context."
    )
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='new', required=True, tracking=True, copy=False)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', index=True)

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
        help="The user responsible for implementing this action."
    )
    feedback_id = fields.Many2one(
        'customer.feedback',
        string="Related Feedback",
        ondelete='set null',
        help="The customer feedback that prompted this action."
    )
    deadline = fields.Date(string='Deadline', tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    active = fields.Boolean(string='Active', default=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Post a message when a new action is created."""
        records = super().create(vals_list)
        for record in records:
            record.message_post(body=_("Improvement action created."))
        return records

    def write(self, vals):
        """Post state change messages to the chatter."""
        if 'state' in vals:
            old_state = self.state
            new_state_val = vals.get('state')
            state_field = self._fields['state']
            new_state_label = dict(state_field.selection).get(new_state_val, new_state_val)

            self.message_post(body=_("Status changed from %s to %s.") % (old_state, new_state_label))

        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_as_done(self):
        """Set the state of the action to 'Done'."""
        self.write({'state': 'done'})

    def action_reset_to_new(self):
        """Reset the action back to the 'New' state."""
        self.write({'state': 'new'})
