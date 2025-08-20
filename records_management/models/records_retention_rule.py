from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsRetentionRule(models.Model):
    _name = 'records.retention.rule'
    _description = 'Records Retention Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Rule Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    sequence = fields.Integer(string="Sequence", default=10, help="Determines the order of execution for rules within a policy.")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        related='policy_id.company_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # RELATIONSHIPS & APPLICABILITY
    # ============================================================================
    policy_id = fields.Many2one('records.retention.policy', string="Policy", required=True, ondelete='cascade', index=True, tracking=True)
    document_type_id = fields.Many2one('records.document.type', string="Document Type", help="Apply this rule only to this type of document. Leave empty to apply to all.")

    # ============================================================================
    # RETENTION PERIOD
    # ============================================================================
    retention_period = fields.Integer(string="Retention Period", required=True, tracking=True)
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite'),
    ], string="Retention Unit", default='years', required=True, tracking=True)

    # ============================================================================
    # ACTION & STATE
    # ============================================================================
    action_on_expiry = fields.Selection([
        ('destroy', 'Schedule for Destruction'),
        ('archive', 'Archive'),
        ('review', 'Flag for Review'),
    ], string="Action on Expiry", default='destroy', required=True, tracking=True)

    state = fields.Selection(related='policy_id.state', readonly=True, store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('policy_id.name', 'name')
    def _compute_display_name(self):
        """Generate display name for the rule."""
        for rule in self:
            if rule.policy_id and rule.name:
                rule.display_name = f"{rule.policy_id.name} - {rule.name}"
            else:
                rule.display_name = rule.name or _("New Rule")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('retention_period', 'retention_unit')
    def _check_retention_period(self):
        """Validate retention period is not negative and is set if not indefinite."""
        for rule in self:
            if rule.retention_unit != 'indefinite':
                if rule.retention_period <= 0:
                    raise ValidationError(_("The retention period must be a positive number."))
            else:
                # For indefinite, we can standardize the period to 0 for consistency
                if rule.retention_period != 0:
                    rule.retention_period = 0

