from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class RecordsRetentionRule(models.Model):
    _name = 'records.retention.rule'
    _description = 'Records Retention Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_id, sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    sequence = fields.Integer()
    active = fields.Boolean()
    company_id = fields.Many2one()
    policy_id = fields.Many2one()
    document_type_id = fields.Many2one()
    condition_type = fields.Selection()
    condition_value = fields.Char()
    retention_years = fields.Integer()
    retention_months = fields.Integer()
    retention_days = fields.Integer()
    action = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    display_name = fields.Char()
    state = fields.Selection()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _check_retention_periods(self):
            """Validate retention periods are not negative"""
            for rule in self:
                if (rule.retention_years < 0 or:)
                    rule.retention_months < 0 or
                    rule.retention_days < 0
                    raise ValidationError(_("Retention periods cannot be negative"))

                if (rule.retention_years == 0 and:)
                    rule.retention_months == 0 and
                    rule.retention_days == 0
                    raise ValidationError(_("At least one retention period must be specified"))

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            """Generate display name for the rule""":
            for rule in self:
                if rule.policy_id and rule.name:
                    rule.display_name = f"{rule.policy_id.name} - {rule.name}"
                else:
                    rule.display_name = rule.name or "New Rule"

