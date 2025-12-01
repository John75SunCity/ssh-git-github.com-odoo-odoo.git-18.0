from odoo import models, fields, api, _


class FeedbackImprovementArea(models.Model):
    _name = 'feedback.improvement.area'
    _description = 'Feedback Improvement Area'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Area Name', required=True, tracking=True)
    description = fields.Text(string='Description', help="Detailed description of what this improvement area covers.")
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index', help="Color index for kanban view.")

    # This field links to the feedback entries that are tagged with this area.
    feedback_ids = fields.Many2many('customer.feedback', 'feedback_improvement_area_rel', 'area_id', 'feedback_id', string='Feedback Entries')

    feedback_count = fields.Integer(
        string='Feedback Count',
        compute='_compute_feedback_count',
        store=True,
        help="Number of feedback entries associated with this area."
    )

    state = fields.Selection([
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('action_plan_defined', 'Action Plan Defined'),
        ('monitoring', 'Monitoring'),
        ('closed', 'Closed'),
    ], string='Status', default='new', tracking=True)

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('feedback_ids')
    def _compute_feedback_count(self):
        """Compute number of related feedback entries."""
        for record in self:
            record.feedback_count = len(record.feedback_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_feedback(self):
        """Action method to open a view of all feedback related to this area."""
        self.ensure_one()
        return {
            "name": _("Feedback for %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "customer.feedback",
            "view_mode": "list,form,kanban",
            "domain": [("id", "in", self.feedback_ids.ids)],
            "context": {"default_improvement_area_ids": [(6, 0, [self.id])]},
        }

    def action_create_improvement_plan(self):
        """Action to create an improvement plan (e.g., a project task) for this area."""
        self.ensure_one()
        # This is an example assuming you use project tasks for improvement plans.
        # You could create a dedicated 'improvement.plan' model instead.
        return {
            "name": _("New Improvement Plan"),
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": _("Improvement Plan for: %s", self.name),
                "default_description": self.description,
            },
        }
