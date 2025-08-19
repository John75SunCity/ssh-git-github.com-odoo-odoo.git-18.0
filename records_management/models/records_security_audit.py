from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsSecurityAudit(models.Model):
    _name = 'records.security.audit'
    _description = 'Records Security Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Event Summary", required=True, readonly=True)
    event_date = fields.Datetime(string="Event Timestamp", default=fields.Datetime.now, required=True, readonly=True)

    # ============================================================================
    # EVENT DETAILS
    # ============================================================================
    event_type = fields.Selection([
        ('login_success', 'Successful Login'),
        ('login_failure', 'Failed Login'),
        ('access_grant', 'Access Granted'),
        ('access_revoke', 'Access Revoked'),
        ('record_view', 'Record Viewed'),
        ('record_create', 'Record Created'),
        ('record_write', 'Record Modified'),
        ('record_unlink', 'Record Deleted'),
        ('destruction_auth', 'Destruction Authorized'),
        ('policy_change', 'Policy Changed'),
        ('export', 'Data Exported'),
    ], string="Event Type", required=True, readonly=True)

    description = fields.Text(string="Detailed Description", readonly=True)

    # ============================================================================
    # ACTOR & CONTEXT
    # ============================================================================
    user_id = fields.Many2one('res.users', string="User", readonly=True, required=True)
    ip_address = fields.Char(string="IP Address", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    # ============================================================================
    # TARGET RECORD
    # ============================================================================
    res_model = fields.Char(string="Model", readonly=True)
    res_id = fields.Integer(string="Record ID", readonly=True)
    res_name = fields.Char(string="Record Name", compute='_compute_res_name', store=False)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for audit in self:
            audit.res_name = False
            if audit.res_model and audit.res_id:
                try:
                    record = self.env[audit.res_model].browse(audit.res_id).exists()
                    if record:
                        audit.res_name = record.display_name
                except (KeyError, AttributeError):
                    # Handle cases where the model or record might not exist anymore
                    audit.res_name = _("N/A")

    # ============================================================================
    # ORM OVERRIDES FOR IMMUTABILITY
    # ============================================================================
    def write(self, vals):
        """Prevent any modification of audit logs."""
        raise UserError(_("Security audit logs are immutable and cannot be modified."))

    def unlink(self):
        """Prevent deletion of audit logs."""
        raise UserError(_("Security audit logs are immutable and cannot be deleted."))

    @api.model
    def create(self, vals):
        """Override create to ensure it can be called from other parts of the system."""
        # This method is kept to allow creation, but write/unlink are blocked.
        return super(RecordsSecurityAudit, self).create(vals)
