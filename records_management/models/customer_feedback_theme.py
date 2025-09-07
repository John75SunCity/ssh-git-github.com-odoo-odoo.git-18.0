from odoo import fields, models, _


class CustomerFeedbackTheme(models.Model):
    _name = 'customer.feedback.theme'
    _description = 'Customer Feedback Theme'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Theme Name', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index')
    feedback_ids = fields.Many2many(
        comodel_name='customer.feedback',
        relation='customer_feedback_theme_rel',
        column1='theme_id',
        column2='feedback_id',
        string='Feedback Items',
        help='Feedback records tagged with this theme.'
    )
