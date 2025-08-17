from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NAIDAuditLog(models.Model):
    _name = 'naid.audit.log'
    _description = 'NAID Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'timestamp desc, id desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    event_type = fields.Selection()
    timestamp = fields.Datetime()
    severity = fields.Selection()
    container_id = fields.Many2one()
    document_id = fields.Many2one()
    location_id = fields.Many2one()
    compliance_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    shredding_service_id = fields.Many2one()
    task_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    partner_id = fields.Many2one()
    bin_key_id = fields.Many2one()
    unlock_service_id = fields.Many2one()
    description = fields.Text()
    before_values = fields.Text()
    after_values = fields.Text()
    metadata = fields.Text()
    ip_address = fields.Char()
    user_agent = fields.Char()
    session_id = fields.Char()
    chain_of_custody_verified = fields.Boolean()
    compliance_status = fields.Selection()
    audit_hash = fields.Char()
    previous_log_hash = fields.Char()
    state = fields.Selection()
    event_level = fields.Selection(string='Event Level')
    res_id = fields.Integer(string='Related Record ID')
    chain_of_custody_id = fields.Many2one('records.chain.of.custody')
    naid_compliance_id = fields.Many2one('naid.compliance')
    event_date = fields.Datetime(string='Event Date')
    timestamp = fields.Datetime()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    message_ids = fields.One2many('mail.message')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    filter_this_week = fields.Char(string='Filter This Week')
    filter_today = fields.Char(string='Filter Today')
    group_by_date = fields.Date(string='Group By Date')
    group_by_event_type = fields.Selection(string='Group By Event Type')
    group_by_level = fields.Char(string='Group By Level')
    group_by_model = fields.Char(string='Group By Model')
    group_by_user = fields.Char(string='Group By User')
    help = fields.Char(string='Help')
    level_critical = fields.Char(string='Level Critical')
    level_info = fields.Char(string='Level Info')
    level_warning = fields.Char(string='Level Warning')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute user-friendly display name"""
            for record in self:
                if record.event_type and record.timestamp:
                    event_label = dict(record._fields["event_type").selection).get(]
                        record.event_type, record.event_type

                    timestamp_str = ()
                        record.timestamp.strftime("%Y-%m-%d %H:%M")
                        if record.timestamp:
                        else "Unknown"

                    user_name = ()
                        record.user_id.name if record.user_id else "Unknown":

                    record.display_name = ()
                        f"{event_label} - {timestamp_str} ({user_name})"

                else:
                    record.display_name = record.name or "Audit Log Entry"


    def _check_timestamp(self):
            """Ensure timestamp is not in the future"""
            for record in self:
                if record.timestamp and record.timestamp > fields.Datetime.now():
                    raise ValidationError()
                        _("Audit timestamp cannot be in the future")



    def _check_json_fields(self):
            """Validate JSON format in text fields"""
            for record in self:
                for field_name in ["before_values", "after_values", "metadata"]:
                    field_value = getattr(record, field_name)
                    if field_value:
                        try:
                            json.loads(field_value)
                        except json.JSONDecodeError as exc
                            raise ValidationError()
                                _()
                                    "Invalid JSON format in field '%s'",
                                    record._fields[field_name].string,



        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_validate(self):
            """Validate audit log entry"""
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft audit logs can be validated"))

            # Generate audit hash for tamper detection:
            self._generate_audit_hash()

            self.write()
                {"state": "validated", "name": self._generate_audit_reference()}


            # Create activity for critical events:
            if self.severity in ["error", "critical"]:
                self.activity_schedule()
                    "records_management.mail_activity_audit_review",
                    summary=_("Critical audit event requires review"),
                    note=self.description,
                    user_id=self.env.ref("base.user_admin").id,



    def action_flag_for_review(self):
            """Flag audit log for manual review""":
            self.ensure_one()
            self.write({"state": "flagged"})

            # Notify compliance officers
            compliance_users = self.env.ref()
                "records_management.group_records_manager"

            for user in compliance_users:
                self.activity_schedule()
                    "mail.mail_activity_data_todo",
                    summary=_("Audit log flagged for review"),:
                    note=self.description,
                    user_id=user.id,



    def action_archive(self):
            """Archive audit log"""
            self.ensure_one()
            if self.state not in ["validated", "flagged"]:
                raise UserError()
                    _("Only validated or flagged audit logs can be archived")


            self.write({"state": "archived"})

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def create_audit_log(self, event_type, description, **kwargs):
            """Utility method to create audit log entries from other models"""
            vals = {}
                "event_type": event_type,
                "description": description,
                "timestamp": fields.Datetime.now(),
                "user_id": self.env.user.id,
                "company_id": self.env.company.id,


            # Add any additional fields from kwargs
            for key, value in kwargs.items():
                if key in self._fields:
                    vals[key] = value

            # Auto-generate name
            vals["name"] = self._generate_audit_reference(event_type)

            audit_log = self.create(vals)

            # Auto-validate non-critical events
            if audit_log.severity in ["info", "warning"]:
                audit_log.action_validate()

            return audit_log


    def _generate_audit_reference(self, event_type=None):
            """Generate unique audit reference"""
            event_type = event_type or self.event_type or "general"

    def _generate_audit_hash(self):
            """Generate cryptographic hash for tamper detection""":
            # Get previous log hash for chaining:
            previous_log = self.search()
                [("id", "<", self.id), ("company_id", "=", self.company_id.id)],
                order="id desc",
                limit=1,


            previous_hash = previous_log.audit_hash if previous_log else "GENESIS":
            # Create hash input string
            hash_input = f"{self.timestamp}{self.event_type}{self.user_id.id}{self.description}{previous_hash}"

            # Generate SHA-256 hash
            audit_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            self.write()
                {"audit_hash": audit_hash, "previous_log_hash": previous_hash}



    def verify_audit_chain(self):
            """Verify the integrity of the audit log chain"""
            logs = self.search()
                []
                    ("company_id", "=", self.env.company.id),
                    ("state", "=", "validated"),

                order="id",


            errors = []
            for i, log in enumerate(logs):
                if i == 0:
                    # First log should have GENESIS as previous hash
                    if log.previous_log_hash != "GENESIS":
                        errors.append(_("Log %s: Invalid genesis hash", log.id))
                else:
                    # Subsequent logs should reference the previous log's hash'
                    previous_log = logs[i - 1]
                    if log.previous_log_hash != previous_log.audit_hash:
                        errors.append(_("Log %s: Broken chain link", log.id))

            return errors

        # ============================================================================
            # MAIL THREAD FRAMEWORK FIELDS (REQUIRED)
        # ============================================================================
