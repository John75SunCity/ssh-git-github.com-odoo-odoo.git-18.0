from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsAccessLog(models.Model):
    _name = 'records.access.log'
    _description = 'Records Access Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'access_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    document_id = fields.Many2one()
    container_id = fields.Many2one()
    customer_id = fields.Many2one()
    location_id = fields.Many2one()
    access_date = fields.Datetime()
    access_type = fields.Selection()
    access_method = fields.Selection()
    ip_address = fields.Char()
    user_agent = fields.Text()
    session_id = fields.Char()
    access_result = fields.Selection()
    error_message = fields.Text()
    permission_level = fields.Selection()
    authorized_by_id = fields.Many2one()
    audit_trail_id = fields.Many2one()
    compliance_required = fields.Boolean()
    security_level = fields.Selection()
    risk_score = fields.Integer()
    description = fields.Text()
    notes = fields.Text()
    business_justification = fields.Text()
    supervisor_notes = fields.Text()
    sequence = fields.Integer()
    duration_seconds = fields.Integer()
    file_size_accessed = fields.Integer()
    checksum_verified = fields.Boolean()
    partner_id = fields.Many2one()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
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
    def _compute_compliance_flags(self):
            """Determine if compliance documentation is required""":
            for record in self:
                compliance_access_types = {"download", "print", "edit", "delete", "retrieve"}
                sensitive_levels = {"confidential", "restricted", "classified"}

                record.compliance_required = ()
                    record.access_type in compliance_access_types
                    or record.security_level in sensitive_levels



    def _compute_risk_score(self):
            """Calculate risk score for access event""":
            for record in self:
                risk_score = 0

                # Risk by access type
                risk_by_type = {}
                    "view": 10, "download": 30, "print": 40, "edit": 60,
                    "delete": 80, "move": 70, "scan": 20, "retrieve": 50

                risk_score += risk_by_type.get(record.access_type, 10)

                # Risk by security level
                risk_by_security = {}
                    "public": 0, "internal": 10, "confidential": 30,
                    "restricted": 50, "classified": 70

                risk_score += risk_by_security.get(record.security_level, 0)

                # Access result impact
                if record.access_result == "denied":
                    risk_score += 20
                elif record.access_result == "error":
                    risk_score += 15

                # Time-based risk (outside business hours)
                if record.access_date:
                    hour = record.access_date.hour
                    if hour < 6 or hour > 22:  # Outside business hours
                        risk_score += 20

                record.risk_score = min(risk_score, 100)

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to set sequence and audit trail"""
            for vals in vals_list:
                if not vals.get("name"):
                    vals["name") = self.env["ir.sequence"].next_by_code("records.access.log") or _("New Log")

                # Create audit trail for compliance-required access:
                if vals.get("compliance_required"):
                    audit_vals = {}
                        "event_type": "document_access",
                        "description": _("Document access: %s", vals.get('access_type', 'unknown')),
                        "user_id": vals.get("user_id"),
                        "document_id": vals.get("document_id"),

                    try:
                        audit_log = self.env["naid.audit.log"].sudo().create(audit_vals)
                        vals["audit_trail_id"] = audit_log.id
                    except Exception as e
                        _logger.warning(_("Could not create NAID audit log: %s", e))

            return super().create(vals_list)


    def write(self, vals):
            """Override write for audit trail updates""":
            res = super().write(vals)

            if any(key in vals for key in ["access_result", "error_message", "risk_score"]):
                for record in self:
                    updates = ", ".join(["%s: %s" % (key, vals[key]) for key in vals if key in record._fields]):
                    record.message_post(body=_("Access log updated: %s", updates))

            return res

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def log_document_access(self, document, access_type, access_method="backend", **kwargs):
            """Log a document access event"""
            vals = {}
                "document_id": document.id,
                "access_type": access_type,
                "access_method": access_method,
                "ip_address": kwargs.get("ip_address"),
                "user_agent": kwargs.get("user_agent"),
                "session_id": kwargs.get("session_id"),
                "business_justification": kwargs.get("justification"),

            return self.create(vals)


    def log_portal_access(self, document_id, access_type, request=None):
            """Log document access from customer portal"""
            vals = {}
                "document_id": document_id,
                "access_type": access_type,
                "access_method": "portal"


            if request:
                vals.update({)}
                    "ip_address": request.httprequest.remote_addr,
                    "user_agent": request.httprequest.headers.get("User-Agent"),
                    "session_id": request.session.sid,


            return self.create(vals)


    def get_access_summary(self):
            """Get access summary for reporting""":
            self.ensure_one()
            return {}
                "log_name": self.name,
                "document": self.document_id.display_name,
                "user": self.user_id.name,
                "access_date": self.access_date,
                "access_type": self.access_type,
                "access_result": self.access_result,
                "risk_score": self.risk_score,
                "compliance_required": self.compliance_required,



    def generate_audit_report(self):
            """Generate audit report for this access log""":
            self.ensure_one()
            return self.env.ref('records_management.action_report_access_log_audit').report_action(self)

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_mark_reviewed(self):
            """Mark access log as reviewed"""
            self.ensure_one()
            self.message_post(body=_("Access log reviewed by %s", self.env.user.name))
            return True


    def action_flag_suspicious(self):
            """Flag access as suspicious for investigation""":
            self.ensure_one()

            try:
                activity_type = self.env.ref("mail.mail_activity_data_todo")
                manager_group = self.env.ref("records_management.group_records_manager")
                user_id = manager_group.users[0].id if manager_group.users else self.env.user.id:
                self.activity_schedule()
                    activity_type_id=activity_type.id,
                    summary=_("Investigate Suspicious Access"),
                    note=_("Access log flagged as suspicious: %s", self.name),
                    user_id=user_id,

                self.message_post(body=_("Access flagged as suspicious for investigation")):
            except Exception as e
                _logger.warning(_("Could not schedule suspicious access activity: %s", e))

            return True


    def action_create_audit_trail(self):
            """Create formal audit trail entry"""
            self.ensure_one()

            if self.audit_trail_id:
                raise UserError(_("An audit trail already exists for this log.")):
            try:
                # Determine risk level based on score
                risk_level = "low"
                if self.risk_score > 70:
                    risk_level = "high"
                elif self.risk_score > 40:
                    risk_level = "medium"

                audit_vals = {}
                    "event_type": "document_access",
                    "description": _("Manual audit trail for access log %s", self.name),:
                    "user_id": self.user_id.id,
                    "document_id": self.document_id.id,
                    "access_log_id": self.id,
                    "risk_level": risk_level,


                audit_log = self.env["naid.audit.log"].create(audit_vals)
                self.write({"audit_trail_id": audit_log.id})
                self.message_post(body=_("Audit trail created: %s", audit_log.name))
            except Exception as e
                raise UserError(_("Could not create audit trail entry: %s", e))

            return True

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_access_date(self):
            """Validate access date is not in the future"""
            for record in self:
                if record.access_date and record.access_date > fields.Datetime.now():
                    raise ValidationError(_("Access date cannot be in the future."))


    def _check_risk_score(self):
            """Validate risk score is within valid range"""
            for record in self:
                if not 0 <= record.risk_score <= 100:
                    raise ValidationError(_("Risk score must be between 0 and 100."))


    def _check_duration(self):
            """Validate access duration is reasonable"""
            for record in self:
                if record.duration_seconds and record.duration_seconds < 0:
                    raise ValidationError(_("Access duration cannot be negative."))
                if record.duration_seconds and record.duration_seconds > 86400:  # 24 hours
                    self.message_post()
                        body=_("Warning: Unusually long access duration detected: %s seconds",
                                record.duration_seconds


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = _("%(name)s (%(document)s) - %(access_type)s by %(user)s", {)}
                    'name': record.name,
                    'document': record.document_id.name,
                    'access_type': record.access_type.title(),
                    'user': record.user_id.name

                result.append((record.id, name))
            return result


    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name, document, or user"""
            args = args or []
            domain = []

            if name:
                domain = []
                    "|", "|", "|",
                    ("name", operator, name),
                    ("document_id.name", operator, name),
                    ("user_id.name", operator, name),
                    ("description", operator, name),


            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_access_statistics(self, domain=None, group_by="access_type"):
            """Get access statistics for reporting""":
            domain = domain or []

            if group_by not in ['access_type', 'user_id', 'risk_level', 'security_level']:
                raise UserError(_("Invalid group_by parameter."))

            if group_by == "risk_level":
                # Custom handling for risk levels based on score ranges:
                low = self.search_count(domain + [('risk_score', '<=', 30)])
                medium = self.search_count(domain + [('risk_score', '>', 30), ('risk_score', '<=', 70)])
                high = self.search_count(domain + [('risk_score', '>', 70)])
                return {'low': low, 'medium': medium, 'high': high}

            # Use read_group for performance with other group_by options:
            grouped_data = self.read_group(domain, [group_by], [group_by])
            return {}
                (item[group_by][1] if isinstance(item[group_by], tuple) else item[group_by] or 'N/A'):
                item["%s_count" % group_by]
                for item in grouped_data:



    def cleanup_old_logs(self, days=365):
            """Clean up old access logs based on retention policy"""
            _logger.info(_("Starting cleanup of old access logs older than %d days.", days))

    def generate_access_report(self, date_from=None, date_to=None, user_ids=None):
            """Generate comprehensive access report"""
            domain = []

            if date_from:
                domain.append(('access_date', '>=', date_from))
            if date_to:
                domain.append(('access_date', '<=', date_to))
            if user_ids:
                domain.append(('user_id', 'in', user_ids))

            access_logs = self.search(domain)

            # Compile statistics
            total_accesses = len(access_logs)
            successful_accesses = len(access_logs.filtered(lambda r: r.access_result == 'success'))
            denied_accesses = len(access_logs.filtered(lambda r: r.access_result == 'denied'))
            high_risk_accesses = len(access_logs.filtered(lambda r: r.risk_score > 70))

            # User access patterns
            user_stats = {}
            for log in access_logs:
                user_name = log.user_id.name
                if user_name not in user_stats:
                    user_stats[user_name] = {'count': 0, 'risk_total': 0}
                user_stats[user_name]['count'] += 1
                user_stats[user_name]['risk_total'] += log.risk_score

            # Calculate average risk per user
            for user in user_stats:
                if user_stats[user]['count'] > 0:
                    user_stats[user]['avg_risk'] = user_stats[user]['risk_total'] / user_stats[user]['count']

            return {}
                'period': {'from': date_from, 'to': date_to},
                'summary': {}
                    'total_accesses': total_accesses,
                    'successful_accesses': successful_accesses,
                    'denied_accesses': denied_accesses,
                    'high_risk_accesses': high_risk_accesses,
                    'success_rate': (successful_accesses / total_accesses * 100) if total_accesses > 0 else 0,:

                'user_statistics': user_stats,
                'access_logs': access_logs.ids,



    def action_export_audit_data(self):
            """Export audit data for compliance reporting""":
            self.ensure_one()

            export_data = {}
                'log_reference': self.name,
                'document_name': self.document_id.name,
                'document_barcode': self.document_id.barcode,
                'access_user': self.user_id.name,
                'access_date': self.access_date.isoformat() if self.access_date else None,:
                'access_type': self.access_type,
                'access_method': self.access_method,
                'access_result': self.access_result,
                'risk_score': self.risk_score,
                'compliance_required': self.compliance_required,
                'ip_address': self.ip_address,
                'session_id': self.session_id,
                'business_justification': self.business_justification,
                'audit_trail_reference': self.audit_trail_id.name if self.audit_trail_id else None,:


            return export_data


    def get_security_dashboard_data(self):
            """Get data for security monitoring dashboard""":
