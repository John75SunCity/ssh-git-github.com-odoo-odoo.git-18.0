from odoo import models, fields, _
from odoo.exceptions import UserError


class TransitoryItem(models.Model):
    _name = 'transitory.item'
    _description = 'Transitory Item for Workflow Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
        help="A brief title for the transitory item."
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the item or task."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
        help="The user responsible for this item."
    )
    related_model = fields.Char(string="Related Model")
    related_record_id = fields.Integer(string="Related Record ID")

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
    # ACTION METHODS
    # ============================================================================
    def action_complete(self):
        """Mark the transitory item as done."""
        self.ensure_one()
        self.write({'state': 'done'})
        self.message_post(body=_("Item marked as complete."))

    def action_cancel(self):
        """Cancel the transitory item."""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Item has been cancelled."))

    def action_reset_to_draft(self):
        """Reset the transitory item to draft state."""
        self.ensure_one()
        if self.state not in ['cancelled', 'done']:
            raise UserError(_("Only cancelled or completed items can be reset to draft."))
        self.write({'state': 'draft'})
        self.message_post(body=_("Item reset to draft."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_related_record(self):
        """
        Dynamically fetches the record linked to this transitory item.
        Returns an empty recordset if no related record is found.
        """
        self.ensure_one()
        if self.related_model and self.related_record_id:
            if self.related_model not in self.env:
                raise UserError(_("The model '%s' does not exist.", self.related_model))
            return self.env[self.related_model].browse(self.related_record_id)
        return self.env[self.related_model]  # Returns empty recordset
