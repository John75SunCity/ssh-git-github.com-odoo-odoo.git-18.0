from odoo import models, fields, api, _

class SurveyFeedbackTheme(models.Model):
    _name = 'survey.feedback.theme'
    _description = 'Survey Feedback Theme'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string='Theme Name',
        required=True,
        help="The name of the feedback theme (e.g., Service Quality, Billing, Portal Usability)."
    )
    description = fields.Text(
        string='Description',
        help="A detailed description of what this feedback theme covers."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck this box to hide the theme without deleting it."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    feedback_ids = fields.One2many(
        'customer.feedback',
        'theme_id',
        string="Associated Feedback"
    )
    feedback_count = fields.Integer(
        string="Feedback Count",
        compute='_compute_feedback_count',
        store=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('feedback_ids')
    def _compute_feedback_count(self):
        """Calculate the number of feedback entries associated with this theme."""
        for theme in self:
            theme.feedback_count = len(theme.feedback_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_feedback(self):
        """Action to open the list of feedback associated with this theme."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Feedback for %s', self.name),
            'res_model': 'customer.feedback',
            'view_mode': 'tree,form,kanban',
            'domain': [('theme_id', '=', self.id)],
            'context': {'default_theme_id': self.id},
        }
