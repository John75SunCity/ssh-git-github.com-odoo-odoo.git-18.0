from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SignedDocumentAudit(models.Model):
    _name = 'signed.document.audit'
    _description = 'Signed Document Audit Trail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'timestamp desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    document_id = fields.Many2one()
    action = fields.Selection()
    action_description = fields.Char()
    performing_user_id = fields.Many2one()
    partner_id = fields.Many2one()
    ip_address = fields.Char()
    user_agent = fields.Text()
    session_id = fields.Char()
    timestamp = fields.Datetime()
    timezone = fields.Char()
    geolocation = fields.Char()
    details = fields.Text()
    before_state = fields.Text()
    after_state = fields.Text()
    compliance_required = fields.Boolean()
    naid_compliant = fields.Boolean()
    verification_hash = fields.Char()
    signature_verification = fields.Boolean()
    certificate_id = fields.Many2one()
    risk_level = fields.Selection()
    state = fields.Selection()
    request_id = fields.Many2one()
    workflow_instance_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    audit_summary = fields.Char()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    cutoff_date = fields.Datetime()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_audit_summary(self):
            """Compute audit summary for reporting""":
            for record in self:
                if record.performing_user_id and record.timestamp:
                    record.audit_summary = _("%(action)s by %(user)s at %(time)s", {)}
                        'action': dict(record._fields['action'].selection).get(record.action, record.action),
                        'user': record.performing_user_id.name,
                        'time': record.timestamp.strftime('%Y-%m-%d %H:%M:%S')

                else:
                    record.audit_summary = _("Incomplete audit entry")


    def create(self, vals_list):
            """Override create to add auto-numbering and validation"""
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name") = self.env["ir.sequence"].next_by_code("signed.document.audit") or _("New")

                # Set performing user if not specified:
                if not vals.get("performing_user_id"):
                    vals["performing_user_id"] = self.env.user.id

                # Generate verification hash
                if not vals.get("verification_hash"):
                    vals["verification_hash"] = self._generate_verification_hash(vals)

            records = super().create(vals_list)

            # Create NAID audit log entry for compliance:
            for record in records:
                if record.naid_compliant:
                    record._create_naid_audit_log()

            return records


    def write(self, vals):
            """Override write to track changes"""
            result = super().write(vals)

            # Log state changes
            if "state" in vals:
                for record in self:
                    record.message_post()
                        body=_("Audit entry state changed to %s", vals["state"])


            return result

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_verify_audit(self):
            """Verify the integrity of this audit entry"""
            self.ensure_one()

            # Verify hash integrity
            current_hash = self._generate_verification_hash({)}
                'document_id': self.document_id.id,
                'action': self.action,
                'performing_user_id': self.performing_user_id.id,
                'timestamp': self.timestamp,


            if current_hash != self.verification_hash:
                raise UserError(_("Audit entry integrity verification failed"))

            self.write({'state': 'verified'})
            self.message_post(body=_("Audit entry verified successfully"))


    def action_archive_audit(self):
            """Archive this audit entry"""
            self.ensure_one()

            if self.state != 'verified':
                raise UserError(_("Only verified audit entries can be archived"))

            self.write({'state': 'archived'})
            self.message_post(body=_("Audit entry archived"))


    def action_view_document(self):
            """View the related signed document"""
            self.ensure_one()

            if not self.document_id:
                raise UserError(_("No document associated with this audit entry"))

            return {}
                "type": "ir.actions.act_window",
                "res_model": "signed.document",
                "view_mode": "form",
                "res_id": self.document_id.id,
                "target": "current",


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def log_document_action(self, document, action, details=None, **kwargs):
            """Log an action performed on a document"""
            vals = {}
                'document_id': document.id,
                'action': action,
                'details': details or '',
                'performing_user_id': kwargs.get('user_id', self.env.user.id),
                'partner_id': kwargs.get('partner_id'),
                'ip_address': kwargs.get('ip_address'),
                'user_agent': kwargs.get('user_agent'),
                'session_id': kwargs.get('session_id'),
                'before_state': kwargs.get('before_state'),
                'after_state': kwargs.get('after_state'),


            return self.create(vals)


    def _generate_verification_hash(self, vals):
            """Generate verification hash for audit entry integrity""":
            import hashlib
            import json

            # Create a deterministic hash from key audit data
            hash_data = {}
                'document_id': vals.get('document_id'),
                'action': vals.get('action'),
                'user_id': vals.get('performing_user_id'),
                'timestamp': str(vals.get('timestamp', fields.Datetime.now())),


            hash_string = json.dumps(hash_data, sort_keys=True)
            return hashlib.sha256(hash_string.encode()).hexdigest()[:32]


    def _create_naid_audit_log(self):
            """Create NAID audit log entry for compliance""":
            self.ensure_one()

            try:
                self.env['naid.audit.log'].create({)}
                    'event_type': 'document_action',
                    'description': _("Signed document action: %s", self.action),
                    'user_id': self.performing_user_id.id,
                    'document_id': self.document_id.id,
                    'audit_entry_id': self.id,
                    'compliance_level': 'aaa',

            except Exception as e
                # Log error but don't fail the audit entry creation'
                self.message_post()
                    body=_("Warning: Could not create NAID audit log: %s", str(e)),
                    message_type='comment'



    def get_audit_summary_data(self):
            """Get audit summary data for reporting""":
            self.ensure_one()

            return {}
                'entry_name': self.name,
                'document_name': self.document_id.name if self.document_id else '',:
                'action': self.action,
                'action_display': dict(self._fields['action'].selection).get(self.action, self.action),
                'performing_user': self.performing_user_id.name,
                'timestamp': self.timestamp,
                'ip_address': self.ip_address or '',
                'partner': self.partner_id.name if self.partner_id else '',:
                'risk_level': self.risk_level,
                'compliance_status': 'Compliant' if self.naid_compliant else 'Non-Compliant',:
                'state': self.state,


        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def generate_audit_report(self, date_from=None, date_to=None, document_ids=None):
            """Generate comprehensive audit report"""
            domain = []

            if date_from:
                domain.append(('timestamp', '>=', date_from))
            if date_to:
                domain.append(('timestamp', '<=', date_to))
            if document_ids:
                domain.append(('document_id', 'in', document_ids))

            audit_entries = self.search(domain, order='timestamp desc')

            # Compile statistics
            total_entries = len(audit_entries)
            by_action = {}
            by_user = {}
            risk_summary = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

            for entry in audit_entries:
                # By action
                if entry.action not in by_action:
                    by_action[entry.action] = 0
                by_action[entry.action] += 1

                # By user
                user_name = entry.performing_user_id.name
                if user_name not in by_user:
                    by_user[user_name] = 0
                by_user[user_name] += 1

                # Risk level
                if entry.risk_level in risk_summary:
                    risk_summary[entry.risk_level] += 1

            return {}
                'period': {'from': date_from, 'to': date_to},
                'total_entries': total_entries,
                'by_action': by_action,
                'by_user': by_user,
                'risk_summary': risk_summary,
                'entries': [entry.get_audit_summary_data() for entry in audit_entries],:
                'compliance_rate': len(audit_entries.filtered('naid_compliant')) / total_entries * 100 if total_entries > 0 else 0,:


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_timestamp(self):
            """Validate timestamp is not in the future"""
            for record in self:
                if record.timestamp and record.timestamp > fields.Datetime.now():
                    raise ValidationError(_("Audit timestamp cannot be in the future"))


    def _check_hash_integrity(self):
            """Validate hash integrity"""
            for record in self:
                if record.verification_hash and len(record.verification_hash) != 32:
                    raise ValidationError(_("Invalid verification hash format"))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = _("%(name)s - %(action)s (%(user)s)", {)}
                    'name': record.name,
                    'action': dict(record._fields['action'].selection).get(record.action, record.action),
                    'user': record.performing_user_id.name

                result.append((record.id, name))
            return result


    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name, action, or user"""
            args = args or []
            domain = []

            if name:
                domain = []
                    "|", "|", "|",
                    ("name", operator, name),
                    ("action", operator, name),
                    ("performing_user_id.name", operator, name),
                    ("document_id.name", operator, name),


            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def cleanup_old_audits(self, days=365):
            """Clean up old audit entries based on retention policy"""
            from datetime import timedelta


    def get_security_dashboard_data(self):
            """Get security monitoring dashboard data"""

    def _calculate_compliance_rate(self):
            """Calculate overall compliance rate"""
            total_audits = self.search_count([
            compliant_audits = self.search_count([('naid_compliant', '=', True)])

            if total_audits > 0:
                return round((compliant_audits / total_audits) * 100, 2)
            return 100.0


