from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsLocationInspection(models.Model):
    _name = 'records.location.inspection'
    _description = 'Records Location Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Inspection ID', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    location_id = fields.Many2one('records.location', string="Location", required=True, ondelete='cascade', tracking=True)
    inspector_id = fields.Many2one('hr.employee', string='Inspector', tracking=True)
    inspection_line_ids = fields.One2many('records.location.inspection.line', 'inspection_id', string="Inspection Checklist")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # INSPECTION DETAILS
    # ============================================================================
    inspection_date = fields.Date(string="Inspection Date", default=fields.Date.context_today, required=True, tracking=True)
    description = fields.Text(string='Summary / Observations')
    notes = fields.Text(string='Corrective Actions Required')
    overall_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pass_with_notes', 'Pass with Notes'),
    ], string="Overall Result", compute='_compute_overall_result', store=True, tracking=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.location.inspection') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('inspection_line_ids.result')
    def _compute_overall_result(self):
        for inspection in self:
            if not inspection.inspection_line_ids:
                inspection.overall_result = False
                continue

            lines = inspection.inspection_line_ids
            if any(line.result == 'fail' for line in lines):
                inspection.overall_result = 'fail'
            elif any(line.result == 'pass_with_notes' for line in lines):
                inspection.overall_result = 'pass_with_notes'
            elif all(line.result == 'pass' for line in lines):
                inspection.overall_result = 'pass'
            else:
                inspection.overall_result = False

    @api.constrains('location_id', 'inspection_date')
    def _check_unique_inspection_per_day(self):
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('location_id', '=', record.location_id.id),
                ('inspection_date', '=', record.inspection_date),
                ('state', '!=', 'cancelled'),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("An inspection for this location on this date already exists."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_inspection(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft inspections can be started."))
    self.write({'state': 'in_progress'})
    self.message_post(body=_("Inspection started by %s.") % self.env.user.name)

    def action_complete_inspection(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only inspections in progress can be completed."))
    final_state = 'failed' if self.overall_result == 'fail' else 'done'
    self.write({'state': final_state})
    self.message_post(body=_("Inspection completed with result: %s.") % self.overall_result)

    def action_cancel(self):
        self.ensure_one()
        if self.state in ('done', 'failed'):
            raise UserError(_("Cannot cancel a completed or failed inspection."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Inspection cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Inspection reset to draft."))


class RecordsLocationInspectionLine(models.Model):
    _name = 'records.location.inspection.line'
    _description = 'Records Location Inspection Checklist Line'
    _order = 'sequence, id'

    inspection_id = fields.Many2one('records.location.inspection', string="Inspection", required=True, ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Checklist Item", required=True)
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pass_with_notes', 'Pass with Notes'),
        ('na', 'N/A'),
    ], string="Result", default='na', required=True)
    notes = fields.Text(string="Notes / Corrective Action")
    attachment_ids = fields.Many2many('ir.attachment', string="Photos")
