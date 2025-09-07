"""
records_retention_policy_version.py

Policy version tracking model for retention policy versioning system.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RecordsRetentionPolicyVersion(models.Model):
    """Records Retention Policy Version
    Tracks versions of retention policies for audit and compliance.

    NOTE: Field renamed to policy_id (was parent_policy_id) for consistency.
    """
    _name = 'records.retention.policy.version'
    _description = 'Records Retention Policy Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_id, version desc'

    # === CORE IDENTIFICATION ===
    name = fields.Char(string="Version Name", required=True, tracking=True)
    policy_id = fields.Many2one(
        comodel_name='records.retention.policy',
        string="Policy",
        required=True,
        ondelete='cascade'
    )
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
    created_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Created By",
        default=lambda self: self.env.user
    )
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    approved_by_id = fields.Many2one(comodel_name='res.users', string="Approved By")
    approved_date = fields.Datetime(string="Approved Date")

    # === AUDIT TRACKING ===
    effective_date = fields.Date(
        string="Effective Date",
        help="Date when this version becomes effective"
    )
    expiry_date = fields.Date(
        string="Expiry Date",
        help="Date when this version expires"
    )
    superseded_by_id = fields.Many2one(
        comodel_name='records.retention.policy.version',
        string="Superseded By",
        help="Version that superseded this one"
    )

    # === METADATA ===
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='policy_id.company_id',
        store=True,
        readonly=True
    )

    # === COMPUTED FIELDS ===
    is_current = fields.Boolean(
        string="Is Current Version",
        compute='_compute_is_current',
        store=True
    )

    @api.depends('policy_id', 'state', 'version')
    def _compute_is_current(self):
        """Determine if this is the current active version."""
        for record in self:
            if record.state == 'active':
                latest_active = self.search([
                    ('policy_id', '=', record.policy_id.id),
                    ('state', '=', 'active')
                ], order='version desc', limit=1)
                record.is_current = (latest_active.id == record.id)
            else:
                record.is_current = False

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate version name if not provided."""
        for vals in vals_list:
            if not vals.get('name') and vals.get('policy_id') and vals.get('version'):
                policy = self.env['records.retention.policy'].browse(vals['policy_id'])
                vals['name'] = _("%s v%s") % (policy.name, vals['version'])
        return super().create(vals_list)

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

    @api.constrains('state')
    def _check_single_active_version(self):
        """Ensure only one active version per policy."""
        for record in self:
            if record.state == 'active':
                other_active = self.search([
                    ('policy_id', '=', record.policy_id.id),
                    ('state', '=', 'active'),
                    ('id', '!=', record.id)
                ])
                if other_active:
                    raise ValidationError(_("Only one version can be active per policy. Please supersede the existing active version first."))

    def action_activate(self):
        """Activate this version and supersede the current active one."""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Only draft versions can be activated."))

        # Find current active version
        current_active = self.search([
            ('policy_id', '=', self.policy_id.id),
            ('state', '=', 'active')
        ])

        # Supersede current active version
        if current_active:
            current_active.write({
                'state': 'superseded',
                'superseded_by_id': self.id,
                'expiry_date': fields.Date.today()
            })

        # Activate this version
        self.write({
            'state': 'active',
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
            'effective_date': fields.Date.today()
        })

        self.message_post(body=_("Version %s activated by %s") % (self.version, self.env.user.name))

    def action_archive(self):
        """Archive this version."""
        self.ensure_one()
        if self.state == 'active':
            raise ValidationError(_("Cannot archive the active version. Please activate another version first."))

        self.write({'state': 'archived'})
        self.message_post(body=_("Version %s archived by %s") % (self.version, self.env.user.name))

    def action_create_new_version(self):
        """Create a new version based on this one."""
        self.ensure_one()

        # Get the next version number
        max_version = self.search([
            ('policy_id', '=', self.policy_id.id)
        ], order='version desc', limit=1).version

        new_version = self.copy({
            'version': max_version + 1,
            'name': _("%s v%s") % (self.policy_id.name, max_version + 1),
            'state': 'draft',
            'created_by_id': self.env.user.id,
            'created_date': fields.Datetime.now(),
            'approved_by_id': False,
            'approved_date': False,
            'effective_date': False,
            'expiry_date': False,
            'superseded_by_id': False,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('New Policy Version'),
            'res_model': self._name,
            'res_id': new_version.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # -------------------------------------------------------------
    # Placeholder Buttons (XML references) - Safe Stubs
    # -------------------------------------------------------------
    def action_compare_versions(self):
        self.ensure_one()
        return False

    def action_view_audit_trail(self):
        self.ensure_one()
        return False

    # Rename handling note:
    # If upgrading from a version where the field was parent_policy_id,
    # a manual column rename is required:
    #   ALTER TABLE records_retention_policy_version RENAME COLUMN parent_policy_id TO policy_id;
    # Or handle via a migration script.
