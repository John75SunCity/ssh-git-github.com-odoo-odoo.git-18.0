from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Customer Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, request_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(string='Active', default=True)

    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, readonly=True)
    preferred_pickup_date = fields.Date(string='Preferred Pickup Date', tracking=True)
    scheduled_pickup_date = fields.Datetime(string='Scheduled Pickup Date', tracking=True)
    completed_pickup_date = fields.Datetime(string='Completed Date', readonly=True, copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1', tracking=True)

    urgency_level = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Urgency', default='normal', tracking=True)

    pickup_item_ids = fields.One2many('pickup.request.item', 'request_id', string='Pickup Items')
    fsm_task_id = fields.Many2one('project.task', string='FSM Task', readonly=True, copy=False)
    route_id = fields.Many2one('pickup.route', string="Pickup Route")

    total_items = fields.Integer(string='Total Items', compute='_compute_total_items', store=True)
    container_count = fields.Integer(string='Container Count', compute='_compute_container_count', store=True)
    description = fields.Text(string='Description')
    internal_notes = fields.Text(string='Internal Notes')

    # Contact Information
    contact_name = fields.Char(string='Contact Name', tracking=True)
    contact_phone = fields.Char(string='Contact Phone', tracking=True)
    contact_email = fields.Char(string='Contact Email', tracking=True)

    # Address Information
    pickup_address = fields.Text(string='Pickup Address', tracking=True)
    special_instructions = fields.Text(string='Special Instructions')

    # Service Details
    service_type = fields.Selection([
        ('standard', 'Standard Pickup'),
        ('emergency', 'Emergency Pickup'),
        ('scheduled', 'Scheduled Pickup'),
        ('bulk', 'Bulk Pickup'),
    ], string='Service Type', default='standard', tracking=True)

    estimated_volume = fields.Float(string='Estimated Volume (cubic feet)', tracking=True)
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True)

    # Billing Information
    billable = fields.Boolean(string='Billable', default=True, tracking=True)
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('pickup_item_ids')
    def _compute_total_items(self):
        for request in self:
            request.total_items = len(request.pickup_item_ids)

    @api.depends('pickup_item_ids', 'pickup_item_ids.quantity')
    def _compute_container_count(self):
        for request in self:
            request.container_count = sum(item.quantity for item in request.pickup_item_ids)

    # ============================================================================
    # CREATE/WRITE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pickup.request') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        """Submit the pickup request for confirmation"""
        self.ensure_one()
        if not self.pickup_item_ids:
            raise ValidationError(_("Cannot submit request without pickup items."))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Request submitted for confirmation."))
        self._create_naid_audit_log('submit', 'Pickup request submitted')

    def action_confirm(self):
        """Confirm the pickup request"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be confirmed."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Request confirmed. Ready for scheduling."))
        self._create_naid_audit_log('confirm', 'Pickup request confirmed')

    def action_schedule(self):
        """Open wizard to schedule the pickup"""
        self.ensure_one()
        if self.state not in ['confirmed', 'scheduled']:
            raise UserError(_("Only confirmed requests can be scheduled."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Schedule Pickup"),
            'res_model': 'pickup.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_start_pickup(self):
        """Start the pickup process"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled requests can be started."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Pickup started."))
        self._create_naid_audit_log('start', 'Pickup process started')

    def action_complete(self):
        """Complete the pickup request"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress requests can be completed."))
        self.write({
            'state': 'completed',
            'completed_pickup_date': fields.Datetime.now()
        })
        self.message_post(body=_("Pickup completed successfully."))
        self._create_naid_audit_log('complete', 'Pickup request completed')

    def action_cancel(self):
        """Cancel the pickup request"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_("Completed requests cannot be cancelled."))
        if self.fsm_task_id:
            self.fsm_task_id.action_cancel()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Request has been cancelled."))
        self._create_naid_audit_log('cancel', 'Pickup request cancelled')

    def action_reset_to_draft(self):
        """Reset request back to draft"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_("Completed requests cannot be reset to draft."))
        self.write({'state': 'draft'})
        self.message_post(body=_("Request reset to draft."))

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _create_naid_audit_log(self, event_type, description):
        """Create NAID compliance audit log entry"""
        if self.env['ir.model'].search([('model', '=', 'naid.audit.log')]):
            self.env['naid.audit.log'].create({
                'event_type': event_type,
                'description': description,
                'related_model': self._name,
                'related_id': self.id,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
            })

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('preferred_pickup_date')
    def _check_preferred_pickup_date(self):
        """Validate preferred pickup date is not in the past"""
        for request in self:
            if request.preferred_pickup_date and request.preferred_pickup_date < fields.Date.today():
                raise ValidationError(_("Preferred pickup date cannot be in the past."))

    @api.constrains('scheduled_pickup_date')
    def _check_scheduled_pickup_date(self):
        """Validate scheduled pickup date"""
        for request in self:
            if request.scheduled_pickup_date and request.scheduled_pickup_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled pickup date cannot be in the past."))

    @api.constrains('estimated_volume', 'estimated_weight')
    def _check_estimates(self):
        """Validate estimated values are positive"""
        for request in self:
            if request.estimated_volume and request.estimated_volume < 0:
                raise ValidationError(_("Estimated volume must be positive."))
            if request.estimated_weight and request.estimated_weight < 0:
                raise ValidationError(_("Estimated weight must be positive."))

    @api.constrains('contact_email')
    def _check_contact_email(self):
        """Validate contact email format"""
        for request in self:
            if request.contact_email and '@' not in request.contact_email:
                raise ValidationError(_("Please enter a valid email address."))

