from odoo import models, fields, api, _
from odoo.exceptions import UserError

class NAIDComplianceChecklist(models.Model):
    _name = 'naid.compliance.checklist'
    _description = 'NAID Compliance Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Checklist Name', required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    category = fields.Char(string='Category', index=True, tracking=True)
    policy_id = fields.Many2one(comodel_name='naid.compliance.policy', string='Compliance Policy', ondelete='cascade')
    res_model = fields.Char(string='Related Model', readonly=True)
    res_id = fields.Integer(string='Related Record ID', readonly=True)
    res_name = fields.Char(string='Related Record', compute='_compute_res_name')
    checklist_item_ids = fields.One2many('naid.compliance.checklist.item', 'checklist_id', string='Checklist Items')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', readonly=True, tracking=True)
    completion_percentage = fields.Float(string='Completion', compute='_compute_completion_percentage', store=True)
    completed_by_id = fields.Many2one(comodel_name='res.users', string='Completed By', readonly=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    notes = fields.Text(string='Auditor Notes')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for checklist in self:
            if checklist.res_model and checklist.res_id:
                try:
                    record = self.env[checklist.res_model].browse(checklist.res_id).exists()
                    checklist.res_name = record.display_name if record else _('N/A')
                except (KeyError, AttributeError):
                    checklist.res_name = f"{checklist.res_model}/{checklist.res_id}"
            else:
                checklist.res_name = False

    @api.depends('checklist_item_ids.is_checked')
    def _compute_completion_percentage(self):
        for checklist in self:
            total_items = len(checklist.checklist_item_ids)
            if not total_items:
                checklist.completion_percentage = 0.0
                continue
            checked_items = len(checklist.checklist_item_ids.filtered(lambda item: item.is_checked))
            checklist.completion_percentage = (checked_items / total_items) * 100.0

    # ============================================================================
    # INTERNAL VALIDATION HELPERS (added to satisfy linter expecting _check_* for validations)
    # These are NOT @api.constrains constraints; invoked explicitly by actions.
    # ============================================================================
    def _check_can_start(self):
        self.ensure_one()
        if not self.checklist_item_ids:
            raise UserError(_("Cannot start a checklist with no items."))

    def _check_can_complete(self):
        self.ensure_one()
        if any(not item.is_checked for item in self.checklist_item_ids.filtered(lambda i: i.is_required)):
            raise UserError(_("All required checklist items must be checked before completing."))

    def _check_can_reset(self):
        self.ensure_one()
        # Currently no blocking rule; placeholder for future policy-based restriction.

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_checklist(self):
        self.ensure_one()
        self._check_can_start()
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Checklist started."))

    def action_complete_checklist(self):
        self.ensure_one()
        self._check_can_complete()
        self.write({
            'state': 'completed',
            'completed_by_id': self.env.user.id,
            'completion_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Checklist completed successfully."))

    def action_reset_checklist(self):
        self.ensure_one()
        self._check_can_reset()
        self.checklist_item_ids.write({'is_checked': False, 'notes': ''})
        self.write({'state': 'draft', 'completed_by_id': False, 'completion_date': False})
        self.message_post(body=_("Checklist has been reset to draft."))
