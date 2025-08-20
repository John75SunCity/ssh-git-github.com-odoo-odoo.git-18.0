from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsPolicyVersion(models.Model):
    _name = 'records.policy.version'
    _description = 'Records Retention Policy Version History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'version_number desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Version Name", compute='_compute_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(related='policy_id.company_id', store=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Created By", default=lambda self: self.env.user, readonly=True, required=True)
    version_number = fields.Integer(string="Version Number", required=True, readonly=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    policy_id = fields.Many2one('records.retention.policy', string="Policy", required=True, ondelete='cascade', index=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # VERSION DETAILS
    # ============================================================================
    change_summary = fields.Text(string="Change Summary", required=True, help="Briefly describe the changes made in this version.")
    effective_date = fields.Date(string="Effective Date", required=True, default=fields.Date.context_today)

    # Snapshot of policy fields at the time of versioning
    retention_period = fields.Integer(string="Retention Period (Days)", readonly=True)
    retention_unit = fields.Selection(related='policy_id.retention_unit', readonly=True) # Assuming unit is on policy
    destruction_method = fields.Selection(related='policy_id.destruction_method', readonly=True) # Assuming method is on policy

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('policy_id.name', 'version_number')
    def _compute_name(self):
        for version in self:
            if version.policy_id and version.version_number:
                version.name = f"{version.policy_id.name} - v{version.version_number}"
            else:
                version.name = _("New Version")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activates this version, making it the current policy standard."""
        self.ensure_one()
        if self.policy_id.state != 'active':
            raise UserError(_("You can only activate a version for an active policy."))

        # Archive other active versions of the same policy
        other_versions = self.search([
            ('policy_id', '=', self.policy_id.id),
            ('state', '=', 'active'),
            ('id', '!=', self.id),
        ])
        other_versions.action_archive()

        self.write({'state': 'active'})
        self.message_post(body=_("Policy version %s has been activated.", self.name))

    def action_archive(self):
        """Archives the policy version."""
        for record in self:
            if record.state == 'active':
                raise UserError(_("You cannot archive the currently active version. Please activate another version first."))
            record.write({'state': 'archived', 'active': False})
            record.message_post(body=_("Policy version %s has been archived.", record.name))

    def action_restore(self):
        """Restores an archived version to draft state."""
        self.ensure_one()
        if self.state != 'archived':
            raise UserError(_("Only archived versions can be restored."))
        self.write({'state': 'draft', 'active': True})
        self.message_post(body=_("Policy version %s has been restored to draft.", self.name))
