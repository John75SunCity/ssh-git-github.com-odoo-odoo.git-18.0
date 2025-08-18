from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PortalFeedbackResolution(models.Model):
    _name = 'portal.feedback.resolution'
    _description = 'Portal Feedback Resolution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Resolution Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(default=True)

    feedback_id = fields.Many2one('portal.feedback', string='Related Feedback', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='feedback_id.partner_id', string='Customer', store=True, readonly=True)

    resolved_by_id = fields.Many2one('res.users', string='Resolved By', default=lambda self: self.env.user, tracking=True)
    resolution_date = fields.Datetime(string='Resolution Date', readonly=True, copy=False)

    resolution_type = fields.Selection([
        ('correction', 'Correction'),
        ('training', 'User Training'),
        ('process_improvement', 'Process Improvement'),
        ('communication', 'Communication'),
        ('other', 'Other'),
    ], string='Resolution Type', tracking=True)

    description = fields.Html(string='Resolution Details', required=True)
    internal_notes = fields.Text(string='Internal Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('implemented', 'Implemented'),
        ('verified', 'Verified'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    customer_satisfaction = fields.Selection([
        ('5', 'Very Satisfied'),
        ('4', 'Satisfied'),
        ('3', 'Neutral'),
        ('2', 'Unsatisfied'),
        ('1', 'Very Unsatisfied'),
    ], string='Customer Satisfaction', tracking=True)

    follow_up_required = fields.Boolean(string='Follow-up Required?', tracking=True)
    follow_up_date = fields.Date(string='Follow-up Date', tracking=True)
    follow_up_notes = fields.Text(string='Follow-up Notes')

    resolution_time_hours = fields.Float(string='Resolution Time (Hours)', compute='_compute_resolution_time', store=True)

    # ============================================================================
    # COMPUTE & ONCHANGE
    # ============================================================================
    @api.depends('feedback_id.create_date', 'resolution_date')
    def _compute_resolution_time(self):
        """Calculate resolution time in hours"""
        for record in self:
            if record.feedback_id and record.feedback_id.create_date and record.resolution_date:
                delta = record.resolution_date - record.feedback_id.create_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0.0

    @api.onchange('follow_up_required')
    def _onchange_follow_up_required(self):
        """Clear follow-up fields when not required"""
        if not self.follow_up_required:
            self.follow_up_date = False
            self.follow_up_notes = False

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('follow_up_required', 'follow_up_date')
    def _check_follow_up_date(self):
        """Validate follow-up date"""
        for record in self:
            if record.follow_up_required and not record.follow_up_date:
                raise ValidationError(_('A follow-up date is required when a follow-up is marked as needed.'))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('portal.feedback.resolution') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_implement(self):
        """Mark resolution as implemented"""
        self.ensure_one()
        self.write({'state': 'implemented'})
        self.message_post(body=_('Resolution has been marked as implemented.'))

    def action_verify(self):
        """Verify resolution by management"""
        self.ensure_one()
        self.write({'state': 'verified'})
        self.message_post(body=_('Resolution has been verified by management.'))

    def action_close(self):
        """Close the resolution"""
        self.ensure_one()
        self.write({
            'state': 'closed',
            'resolution_date': fields.Datetime.now()
        })
        self.message_post(body=_('Resolution has been closed.'))
        # Optionally, notify the customer
        template = self.env.ref('records_management.email_template_feedback_resolved', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_cancel(self):
        """Cancel the resolution"""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Resolution has been cancelled.'))
