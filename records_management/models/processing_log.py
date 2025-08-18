import os
import traceback
try:
    import psutil
except ImportError:
    psutil = None

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProcessingLog(models.Model):
    _name = 'processing.log'
    _description = 'System Processing Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'timestamp desc, id desc'
    _rec_name = 'reference'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Log Entry', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    active = fields.Boolean(default=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, required=True, readonly=True)

    process_type = fields.Selection([
        ('fsm', 'FSM'),
        ('billing', 'Billing'),
        ('destruction', 'Destruction'),
        ('api', 'API'),
        ('report', 'Report'),
        ('system', 'System'),
        ('other', 'Other'),
    ], string='Process Type', required=True, tracking=True)

    log_level = fields.Selection([
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], string='Log Level', default='info', required=True, tracking=True)

    # ============================================================================
    # REFERENCE & MESSAGE
    # ============================================================================
    reference = fields.Char(string='Reference', compute='_compute_reference', store=True, readonly=True)
    res_model = fields.Char(string='Related Model', readonly=True)
    res_id = fields.Integer(string='Related Record ID', readonly=True)
    message = fields.Text(string='Message', required=True, readonly=True)
    details = fields.Html(string='Details', readonly=True)
    error_code = fields.Char(string='Error Code', readonly=True)
    stack_trace = fields.Text(string='Stack Trace', readonly=True)

    # ============================================================================
    # RESOLUTION
    # ============================================================================
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('ignored', 'Ignored'),
    ], string='Status', default='new', tracking=True)
    resolution_notes = fields.Text(string='Resolution Notes')
    resolved_by_id = fields.Many2one('res.users', string='Resolved By', readonly=True)
    resolved_date = fields.Datetime(string='Resolved Date', readonly=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('processing.log') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_reference(self):
        for log in self:
            if log.res_model and log.res_id:
                try:
                    if log.res_model in self.env:
                        record = self.env[log.res_model].browse(log.res_id).exists()
                        if record:
                            log.reference = f"{record._description} [{record.display_name}]"
                        else:
                            log.reference = _("Deleted %s(%s)", log.res_model, log.res_id)
                    else:
                        log.reference = _("Unknown Model %s(%s)", log.res_model, log.res_id)
                except Exception:
                    log.reference = _("Error accessing %s(%s)", log.res_model, log.res_id)
            else:
                log.reference = log.process_type.capitalize() if log.process_type else _("Unreferenced Log")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_resolve(self):
        """Opens a wizard to add resolution notes and mark as resolved."""
        self.ensure_one()
        # This would typically open a wizard. For simplicity, we'll just update the state here.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Resolve Log Entry'),
            'res_model': 'processing.log.resolution.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_log_id': self.id,
            }
        }

    def action_escalate(self):
        self.ensure_one()
        self.write({'status': 'escalated'})
        self.message_post(body=_("Log entry escalated for further review."))
        # You could create an activity for a manager here
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('Escalated Log: %s', self.name),
            note=_('Please review this escalated log entry.'),
            user_id=self.env.user.id # Or a specific manager
        )

    def action_view_related_record(self):
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_("This log entry is not linked to a specific record."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

# ============================================================================
# WIZARD FOR RESOLUTION
# ============================================================================
class ProcessingLogResolutionWizard(models.TransientModel):
    _name = 'processing.log.resolution.wizard'
    _description = 'Processing Log Resolution Wizard'

    log_id = fields.Many2one('processing.log', string="Log Entry", required=True, readonly=True)
    resolution_notes = fields.Text(string="Resolution Notes", required=True)

    def action_confirm_resolution(self):
        self.ensure_one()
        self.log_id.write({
            'status': 'resolved',
            'resolution_notes': self.resolution_notes,
            'resolved_by_id': self.env.user.id,
            'resolved_date': fields.Datetime.now(),
        })
        self.log_id.message_post(body=_("Log marked as resolved.<br/>Notes: %s", self.resolution_notes))
        return {'type': 'ir.actions.act_window_close'}
