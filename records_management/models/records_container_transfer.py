from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class RecordsContainerTransfer(models.Model):
    _name = 'records.container.transfer'
    _description = 'Records Container Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Transfer Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready to Transfer'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True, copy=False)

    # ============================================================================
    # TRANSFER DETAILS
    # ============================================================================
    from_location_id = fields.Many2one('stock.location', string="From Location", required=True, readonly=True, states={'draft': [('readonly', False)]})
    to_location_id = fields.Many2one('stock.location', string="To Location", required=True, readonly=True, states={'draft': [('readonly', False)]})
    scheduled_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now, required=True, tracking=True)
    actual_transfer_date = fields.Datetime(string="Actual Transfer Date", readonly=True)
    notes = fields.Text(string="Notes")

    # ============================================================================
    # CONTENTS
    # ============================================================================
    transfer_line_ids = fields.One2many('records.container.transfer.line', 'transfer_id', string="Transfer Lines", readonly=True, states={'draft': [('readonly', False)]})
    container_count = fields.Integer(string="Container Count", compute='_compute_container_count', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.container.transfer') or _('New')
        return super().create(vals_list)

    def unlink(self):
        if any(rec.state not in ('draft', 'cancelled') for rec in self):
            raise UserError(_("You can only delete draft or cancelled transfers."))
        return super().unlink()

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('transfer_line_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.transfer_line_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if not self.transfer_line_ids:
            raise UserError(_("You cannot confirm a transfer with no container lines."))
        self.write({'state': 'ready'})
        self.message_post(body=_("Transfer confirmed and is ready to be processed."))

    def action_start_transfer(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Transfer is now in progress."))

    def action_complete_transfer(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only transfers in progress can be completed."))

        for line in self.transfer_line_ids:
            line.container_id.write({'location_id': self.to_location_id.id})

        self.write({
            'state': 'done',
            'actual_transfer_date': fields.Datetime.now()
        })
        self.message_post(body=_("Transfer completed. Container locations have been updated."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Transfer has been cancelled."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Transfer has been reset to draft."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('from_location_id', 'to_location_id')
    def _check_locations(self):
        for record in self:
            if record.from_location_id == record.to_location_id:
                raise ValidationError(_("The source and destination locations cannot be the same."))
