"""
records_retention_policy_version.py

Policy version tracking model for retention policy versioning system.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsRetentionPolicyVersion(models.Model):
    """
    Records Retention Policy Version
    Tracks versions of retention policies for audit and compliance.
    """
    _name = 'records.retention.policy.version'
    _description = 'Records Retention Policy Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_id, version desc'

    # === CORE IDENTIFICATION ===
    name = fields.Char(string="Version Name", required=True, tracking=True)
    policy_id = fields.Many2one('records.retention.policy', string="Policy", required=True, ondelete='cascade')
    version = fields.Integer(string='Version Number', required=True, default=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('superseded', 'Superseded'),
        ('archived', 'Archived'),
    ], string='State', default='draft', tracking=True)

    # === VERSION DETAILS ===
    description = fields.Text(string="Version Description")
    changes = fields.Text(string="Changes in this Version")
    created_by_id = fields.Many2one('res.users', string="Created By", default=lambda self: self.env.user)
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    approved_by_id = fields.Many2one('res.users', string="Approved By")
    approved_date = fields.Datetime(string="Approved Date")

    # === METADATA ===
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', related='policy_id.company_id', store=True, readonly=True)

    @api.model
    def create(self, vals):
        """Auto-generate version name if not provided."""
        if not vals.get('name') and vals.get('policy_id') and vals.get('version'):
            policy = self.env['records.retention.policy'].browse(vals['policy_id'])
            vals['name'] = f"{policy.name} v{vals['version']}"
        return super().create(vals)

    @api.constrains('policy_id', 'version')
    def _check_unique_version(self):
        """Ensure version numbers are unique per policy."""
        for version in self:
            existing = self.search([
                ('policy_id', '=', version.policy_id.id),
                ('version', '=', version.version),
                ('id', '!=', version.id)
            ])
            if existing:
                raise ValidationError(_("Version %s already exists for policy %s") % (version.version, version.policy_id.name))
