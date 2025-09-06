from odoo import models, fields, api, _
from odoo.exceptions import UserError


class NAIDAuditLog(models.Model):
    _name = 'naid.audit.log'
    _description = 'NAID AAA Compliance Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    user_id = fields.Many2one('res.users', string='User', required=True, readonly=True, ondelete='restrict')

    action_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('unlink', 'Delete'),
        ('login_success', 'Login Success'),
        ('login_failure', 'Login Failure'),
        ('access', 'Record Access'),
        ('destruction', 'Destruction'),
        ('pickup', 'Pickup'),
        ('security', 'Security Event'),
        ('report', 'Report Generation'),
        ('export', 'Data Export'),
        ('other', 'Other'),
    ], string='Action Type', required=True, readonly=True)

    description = fields.Text(string='Description', required=True, readonly=True)

    # Polymorphic relationship to link to any model record
    res_model = fields.Char(string='Related Model', readonly=True)
    res_id = fields.Integer(string='Related Record ID', readonly=True)
    res_name = fields.Char(string='Related Record Name', compute='_compute_res_name', store=False)

    ip_address = fields.Char(string='IP Address', readonly=True)
    naid_compliant = fields.Boolean(string='NAID Compliant Action', default=True, readonly=True)

    # Event timing (explicit separate from create_date for clarity & potential backfill)
    event_date = fields.Datetime(string='Event Date', readonly=True, index=True, default=fields.Datetime.now)

    # Value change tracking (optional old/new or JSON diff)
    old_value = fields.Char(string='Old Value', readonly=True)
    new_value = fields.Char(string='New Value', readonly=True)
    value_json = fields.Text(string='Structured Value Data', readonly=True, help='JSON snapshot or diff for complex value changes.')

    # Inverse field for the One2many in destruction.event
    event_id = fields.Many2one('destruction.event', string='Destruction Event', ondelete='cascade', index=True)
    document_id = fields.Many2one('records.document', string="Document")
    custody_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Chain of Custody',
        ondelete='set null',
        index=True,
        help='Related chain of custody record for this audit entry.'
    )
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade', index=True)
    audit_requirement_id = fields.Many2one(
        'naid.audit.requirement',
        string='Audit Requirement',
        ondelete='set null',
        index=True,
        help='Related NAID audit requirement for this audit log entry.'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for log in self:
            log.res_name = False
            if log.res_model and log.res_id:
                try:
                    record = self.env[log.res_model].browse(log.res_id).exists()
                    if record:
                        log.res_name = record.display_name
                except (KeyError, AttributeError):
                    # The model might not exist or have a display_name
                    log.res_name = f"{log.res_model}/{log.res_id}"

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    @api.model
    def action_log(self, description, action_type, record=None, user_id=None, old_value=None, new_value=None, value_json=None, event_date=None):
        """
        Central method to create a new audit log entry.
        This should be called from other models whenever a significant action occurs.
        """
        if user_id is None:
            user_id = self.env.user.id

        vals = {
            'user_id': user_id,
            'description': description,
            'action_type': action_type,
            'ip_address': self.env.context.get('ip_address', self.env.request.httprequest.remote_addr if self.env.request else 'N/A'),
            'old_value': old_value,
            'new_value': new_value,
            'value_json': value_json,
        }
        if event_date:
            vals['event_date'] = event_date
        if record and record.exists():
            vals.update({
                'res_model': record._name,
                'res_id': record.id,
            })
        return self.create(vals)

    # ============================================================================
    # ORM OVERRIDES - To ensure immutability
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('naid.audit.log') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modification of audit logs."""
        raise UserError(_("NAID Audit logs are immutable and cannot be modified."))

    def unlink(self):
        """Prevent deletion of audit logs."""
        raise UserError(_("NAID Audit logs are immutable and cannot be deleted."))
