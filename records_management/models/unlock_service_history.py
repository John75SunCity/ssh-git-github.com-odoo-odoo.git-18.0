from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UnlockServiceHistory(models.Model):
    _name = 'unlock.service.history'
    _description = 'Unlock Service History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Service Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    technician_id = fields.Many2one('res.users', string="Technician", default=lambda self: self.env.user, tracking=True)

    service_type = fields.Selection([
        ('unlock', 'Unlock'),
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('installation', 'Installation'),
    ], string="Service Type", required=True, default='unlock')

    date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now, required=True)
    start_time = fields.Datetime(string="Start Time", readonly=True)
    end_time = fields.Datetime(string="End Time", readonly=True)
    duration = fields.Float(string="Duration (Minutes)", compute='_compute_duration', store=True)

    reason = fields.Text(string="Reason for Service")
    resolution = fields.Text(string="Service Resolution")
    notes = fields.Text(string="Internal Notes")

    parts_used_ids = fields.One2many('unlock.service.part', 'service_history_id', string="Parts Used")

    billable = fields.Boolean(string="Billable", default=True)
    cost = fields.Monetary(string="Total Cost", compute='_compute_total_cost', store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, copy=False)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'service_type', 'partner_id.name')
    def _compute_display_name(self):
        for record in self:
            service_type_display = dict(record._fields['service_type'].selection).get(record.service_type, '')
            customer_name = record.partner_id.name or _("Unknown")
            record.display_name = f"{record.name} - {service_type_display} ({customer_name})"

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                duration_delta = record.end_time - record.start_time
                record.duration = duration_delta.total_seconds() / 60.0
            else:
                record.duration = 0.0

    @api.depends('parts_used_ids.total_price')
    def _compute_total_cost(self):
        for record in self:
            record.cost = sum(part.total_price for part in record.parts_used_ids)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('unlock.service.history') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_service(self):
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled services can be started."))
        self.write({'state': 'in_progress', 'start_time': fields.Datetime.now()})
        self.message_post(body=_("Service has been started."))

    def action_complete_service(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress services can be completed."))
        self.write({'state': 'completed', 'end_time': fields.Datetime.now()})
        self.message_post(body=_("Service marked as completed."))
        if self.billable and not self.invoice_id:
            self.action_create_invoice()

    def action_cancel_service(self):
        self.ensure_one()
        if self.state in ['completed', 'invoiced', 'cancelled']:
            raise UserError(_("Cannot cancel a service that is already completed, invoiced, or cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Service has been cancelled."))

    def action_create_invoice(self):
        self.ensure_one()
        if not self.billable:
            raise UserError(_("This service is not billable."))
        if self.invoice_id:
            raise UserError(_("An invoice already exists for this service."))

        invoice_vals = self._prepare_invoice_values()
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'invoice_id': invoice.id, 'state': 'invoiced'})
        self.message_post(body=_("Invoice %s created.", invoice.name))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reschedule_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Reschedule Service"),
            'res_model': 'unlock.service.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_service_id': self.id, 'default_current_date': self.date},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _prepare_invoice_values(self):
        self.ensure_one()
        invoice_lines = []
        for part in self.parts_used_ids:
            invoice_lines.append((0, 0, {
                'product_id': part.product_id.id,
                'name': f"{part.product_id.name} ({self.name})",
                'quantity': part.quantity,
                'price_unit': part.service_price,
            }))

        return {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'ref': self.name,
        }
