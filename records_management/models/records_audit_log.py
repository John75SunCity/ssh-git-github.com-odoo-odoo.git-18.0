from odoo import models, fields, api, _

class RecordsAuditLog(models.Model):
    _name = 'records.audit.log'
    _description = 'Records Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'description'

    document_type_id = fields.Many2one('records.document.type', string="Document Type", help="Related document type for this audit log entry.")

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    # Note: Most fields are readonly to ensure log integrity.
    user_id = fields.Many2one('res.users', string="User", readonly=True, required=True, ondelete='restrict')
    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now, readonly=True, required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True, required=True)

    # ============================================================================
    # LOG DETAILS
    # ============================================================================
    event_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('unlink', 'Delete'),
        ('action', 'Action'),
        ('login', 'Login'),
        ('access', 'Access/View'),
        ('export', 'Export'),
    ], string="Event Type", readonly=True, required=True)

    description = fields.Char(string="Description", readonly=True, required=True, help="A human-readable summary of the event.")

    # Additional fields for retention policy views
    action = fields.Char(string="Action", readonly=True, help="Specific action performed")
    action_date = fields.Datetime(string="Action Date", readonly=True, help="Date when action was performed")
    notes = fields.Text(string="Notes", readonly=True, help="Additional notes about the audit event")

    # ============================================================================
    # RELATED DOCUMENT
    # ============================================================================
    res_model = fields.Char(string="Model", readonly=True, help="The technical model name of the affected document.")
    res_id = fields.Integer(string="Record ID", readonly=True, help="The ID of the affected document.")
    res_name = fields.Char(string="Record Name", compute='_compute_res_name', store=False, readonly=True, help="The display name of the affected document.")

    # ============================================================================
    # RELATED POLICY AND RULE
    # ============================================================================
    policy_id = fields.Many2one('records.retention.policy', string="Retention Policy", readonly=True, help="Related retention policy for this audit log entry.")
    rule_id = fields.Many2one('records.retention.rule', string="Retention Rule", readonly=True, help="Related retention rule for this audit log entry.")

    # ============================================================================
    # TECHNICAL DETAILS
    # ============================================================================
    ip_address = fields.Char(string="IP Address", readonly=True, help="The IP address from which the action was performed.")
    user_agent = fields.Char(string="User Agent", readonly=True, help="The browser or client used to perform the action.")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for log in self:
            log.res_name = False
            if log.res_model and log.res_id and self.env[log.res_model].browse(log.res_id).exists():
                try:
                    log.res_name = self.env[log.res_model].browse(log.res_id).display_name
                except Exception:
                    log.res_name = _("Record not accessible or deleted")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def log_event(self, record, event_type, description):
        """
        Creates a new audit log entry. This is the primary method to be called
        from other models to record an auditable event.

        :param record: The recordset of the document being acted upon.
        :param event_type: The type of event (from the selection field).
        :param description: A clear, human-readable description of the event.
        """
        request = self.env.context.get('request', None)
        ip_address = request.httprequest.remote_addr if request else None
        user_agent = request.httprequest.user_agent.string if request else None

        self.create({
            'user_id': self.env.user.id,
            'event_type': event_type,
            'description': description,
            'res_model': record._name if record else None,
            'res_id': record.id if record else None,
            'ip_address': ip_address,
            'user_agent': user_agent,
        })
        return True
