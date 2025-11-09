from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class WorkOrderShredding(models.Model):
    _name = "work.order.shredding"
    _description = 'Shredding Work Order Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Work Order #", required=True, copy=False, readonly=True, default=lambda self: "New")
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, tracking=True)
    portal_request_id = fields.Many2one(comodel_name='portal.request', string="Portal Request", ondelete='set null')

    scheduled_date = fields.Datetime(string="Scheduled Date", required=True, tracking=True)
    start_date = fields.Datetime(string='Start Time', readonly=True, copy=False)
    completion_date = fields.Datetime(string='Completion Time', readonly=True, copy=False)
    actual_duration = fields.Float(string="Duration (Hours)", compute='_compute_actual_duration', store=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string="Priority", default='0', tracking=True)

    assigned_team_id = fields.Many2one(comodel_name='maintenance.team', string="Assigned Team")
    technician_ids = fields.Many2many(
        'hr.employee',
        relation='work_order_shredding_technician_rel',
        column1='work_order_id',
        column2='employee_id',
        string="Assigned Technicians"
    )
    equipment_ids = fields.Many2many(
        'maintenance.equipment',
        relation='work_order_shredding_equipment_rel',
        column1='work_order_id',
        column2='equipment_id',
        string="Assigned Equipment"
    )
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string="Assigned Vehicle")

    material_type = fields.Selection([
        ('paper', 'Paper'),
        ('hard_drive', 'Hard Drives'),
        ('mixed_media', 'Mixed Media'),
    ], string="Material Type", default='paper')
    estimated_weight = fields.Float(string="Estimated Weight (kg)")
    actual_weight = fields.Float(string="Actual Weight (kg)", tracking=True)

    special_instructions = fields.Text(string="Special Instructions")
    completion_notes = fields.Text(string="Completion Notes")

    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    certificate_id = fields.Many2one(comodel_name='naid.certificate', string="Destruction Certificate", readonly=True, copy=False)

    # Invoice related fields
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', readonly=True, copy=False)
    invoiced = fields.Boolean(string="Invoiced", compute='_compute_invoiced', store=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id')
    active = fields.Boolean(default=True)

    # Computed count fields for stat buttons
    certificate_count = fields.Integer(string="Certificates Count", compute='_compute_certificate_count', store=False)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'state')
    def _compute_display_name(self):
        for order in self:
            state_label = dict(order._fields['state'].selection).get(order.state, '')
            customer_name = order.partner_id.name or ''
            order.display_name = f"{order.name} - {customer_name} ({state_label})"

    @api.depends('start_date', 'completion_date')
    def _compute_actual_duration(self):
        for order in self:
            if order.start_date and order.completion_date:
                delta = order.completion_date - order.start_date
                order.actual_duration = delta.total_seconds() / 3600.0
            else:
                order.actual_duration = 0.0

    @api.depends('state', 'invoice_id')
    def _compute_invoiced(self):
        for order in self:
            order.invoiced = order.state == 'invoiced' or bool(order.invoice_id)

    @api.depends('certificate_id')
    def _compute_certificate_count(self):
        """Compute whether a destruction certificate exists"""
        for order in self:
            order.certificate_count = 1 if order.certificate_id else 0

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.shredding') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'in_progress':
            vals.setdefault('start_date', fields.Datetime.now())
        if 'state' in vals and vals['state'] == 'completed':
            vals.setdefault('completion_date', fields.Datetime.now())
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Work order confirmed."))

    def action_start_work(self):
        self.ensure_one()
        if self.state not in ['confirmed', 'assigned']:
            raise UserError(_("Work order must be confirmed or assigned before starting."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Work order started."))

    def action_complete_work(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress work orders can be completed."))
        self.write({'state': 'completed'})
        if self.certificate_required and not self.certificate_id:
            self._generate_destruction_certificate()
        self.message_post(body=_("Work order completed."))

    def action_verify(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed work orders can be verified."))
        self.write({'state': 'verified'})
        self.message_post(body=_("Work order verified by %s.", self.env.user.name))

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['completed', 'verified', 'invoiced', 'cancelled']:
            raise UserError(_("Cannot cancel a work order that is already completed, verified, invoiced, or cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Work order reset to draft."))

    def action_invoice(self):
        """Mark work order as invoiced"""
        self.ensure_one()
        if self.state not in ['completed', 'verified']:
            raise UserError(_("Only completed or verified work orders can be invoiced."))
        self.write({'state': 'invoiced'})
        self.message_post(body=_("Work order marked as invoiced."))

    def action_view_certificate(self):
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(_("No certificate associated with this work order."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificate"),
            "res_model": "naid.certificate",
            "res_id": self.certificate_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_certificates(self):
        """Open the associated destruction certificate"""
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(_("No certificate associated with this work order."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificate"),
            "res_model": "naid.certificate",
            "res_id": self.certificate_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _generate_destruction_certificate(self):
        self.ensure_one()
        if self.certificate_id:
            return self.certificate_id

        certificate_vals = {
            'name': _("Certificate for %s", self.name),
            'certificate_type': 'destruction',
            'partner_id': self.partner_id.id,
            'work_order_id': self.id,
            'destruction_date': self.completion_date or fields.Datetime.now(),
            'total_weight': self.actual_weight,
            'material_type': self.material_type,
        }
        certificate = self.env['naid.certificate'].create(certificate_vals)
        self.certificate_id = certificate
        self.message_post(body=_("Destruction Certificate %s created.", certificate.name))
        return certificate

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for order in self:
            if order.state == 'draft' and order.scheduled_date and order.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled date cannot be in the past."))

    @api.constrains('start_date', 'completion_date')
    def _check_date_sequence(self):
        for order in self:
            if order.start_date and order.completion_date and order.start_date > order.completion_date:
                raise ValidationError(_("Completion date must be after the start date."))

    @api.constrains('estimated_weight', 'actual_weight')
    def _check_weights(self):
        for order in self:
            if order.estimated_weight and order.estimated_weight < 0:
                raise ValidationError(_("Estimated weight cannot be negative."))
            if order.actual_weight and order.actual_weight < 0:
                raise ValidationError(_("Actual weight cannot be negative."))
