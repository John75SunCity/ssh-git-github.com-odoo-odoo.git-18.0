import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class RecordsAccessLog(models.Model):
    _name = 'records.access.log'
    _description = 'Records Access Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'access_date desc, id desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Log Entry", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='User', required=True, readonly=True, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string="Customer", related='container_id.partner_id', store=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # RELATED OBJECTS
    # ============================================================================
    container_id = fields.Many2one('records.container', string="Container", readonly=True)
    location_id = fields.Many2one('stock.location', string="Location", related='container_id.location_id', store=True, readonly=True)

    # ============================================================================
    # ACCESS DETAILS
    # ============================================================================
    access_date = fields.Datetime(string="Access Timestamp", default=fields.Datetime.now, required=True, readonly=True)
    access_type = fields.Selection([
        ('view', 'View'), ('download', 'Download'), ('print', 'Print'),
        ('edit', 'Edit'), ('create', 'Create'), ('delete', 'Delete'),
        ('move', 'Move'), ('scan', 'Scan'), ('retrieve', 'Retrieval Request'),
        ('destroy', 'Destruction Request'), ('portal_view', 'Portal View'),
    ], string="Access Type", required=True, readonly=True)
    access_method = fields.Selection([
        ('backend', 'Backend UI'), ('portal', 'Customer Portal'), ('api', 'API'), ('mobile', 'Mobile App')
    ], string="Access Method", default='backend', readonly=True)
    access_result = fields.Selection([
        ('success', 'Success'), ('denied', 'Denied'), ('error', 'Error')
    ], string="Result", default='success', readonly=True)
    error_message = fields.Text(string="Error Message", readonly=True)
    duration_seconds = fields.Integer(string="Duration (s)", help="Duration of the access session in seconds.")

    # ============================================================================
    # TECHNICAL & SECURITY INFO
    # ============================================================================
    ip_address = fields.Char(string="IP Address", readonly=True)
    user_agent = fields.Text(string="User Agent", readonly=True)
    session_id = fields.Char(string="Session ID", readonly=True)
    business_justification = fields.Text(string="Business Justification")

    # ============================================================================
    # COMPLIANCE & RISK
    # ============================================================================
    security_level = fields.Selection(related='container_id.security_level', string="Security Level", store=True, readonly=True)
    compliance_required = fields.Boolean(string="Compliance Documentation Required", compute='_compute_compliance_flags', store=True)
    risk_score = fields.Integer(string="Risk Score", compute='_compute_risk_score', store=True, help="Calculated risk score (0-100). Higher is more risky.")
    audit_trail_id = fields.Many2one('naid.audit.log', string="NAID Audit Trail", readonly=True)
    state = fields.Selection([
        ('new', 'New'), ('reviewed', 'Reviewed'), ('suspicious', 'Suspicious'), ('resolved', 'Resolved')
    ], string="Status", default='new', tracking=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.access.log') or _('New')
        return super().create(vals_list)

    def unlink(self):
        raise UserError(_("Access logs are part of the audit trail and cannot be deleted."))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('access_type', 'security_level')
    def _compute_compliance_flags(self):
        """Determine if compliance documentation is required."""
        for record in self:
            compliance_access_types = {'download', 'print', 'edit', 'delete', 'retrieve', 'destroy'}
            sensitive_levels = {'high', 'vault'}
            record.compliance_required = (record.access_type in compliance_access_types or
                                           record.security_level in sensitive_levels)

    @api.depends('access_type', 'security_level', 'access_result', 'access_date')
    def _compute_risk_score(self):
        """Calculate risk score for the access event."""
        for record in self:
            score = 0
            risk_by_type = {'view': 5, 'download': 30, 'print': 40, 'edit': 60, 'delete': 80, 'move': 70, 'retrieve': 50, 'destroy': 90}
            score += risk_by_type.get(record.access_type, 10)

            risk_by_security = {'low': 0, 'medium': 10, 'high': 40, 'vault': 60}
            score += risk_by_security.get(record.security_level, 0)

            if record.access_result == 'denied':
                score += 20
            elif record.access_result == 'error':
                score += 15

            if record.access_date and (record.access_date.hour < 6 or record.access_date.hour > 22):
                score += 25

            record.risk_score = min(score, 100)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_reviewed(self):
        self.ensure_one()
        self.write({'state': 'reviewed'})
        self.message_post(body=_("Access log marked as reviewed by %s") % self.env.user.name)

    def action_flag_suspicious(self):
        self.ensure_one()
        for record in self:
            record.write({'state': 'suspicious'})
            record.message_post(body=_("Access flagged as suspicious for investigation."))
            try:
                activity_type_id = self.env.ref('mail.mail_activity_data_call').id
                manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
                user_id = manager_group.users[0].id if manager_group and manager_group.users else self.env.user.id

                self.env['mail.activity'].create({
                    'activity_type_id': activity_type_id,
                    'summary': _("Investigate Suspicious Access: %s") % record.name,
                    'note': _("Please investigate this access log flagged as suspicious."),
                    'res_id': record.id,
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'user_id': user_id,
                })
            except Exception as e:
                _logger.warning(_("Could not schedule suspicious access activity: %s"), e)

    def action_create_audit_trail(self):
        self.ensure_one()
        if self.audit_trail_id:
            raise UserError(_("An audit trail already exists for this log."))
        try:
            risk_level = "low"
            if self.risk_score > 70:
                risk_level = "high"
            elif self.risk_score > 40:
                risk_level = "medium"

            audit_vals = {
                "event_type": "document_access",
                "description": _("Manual audit trail for access log %s") % self.name,
                "user_id": self.user_id.id,
                "container_id": self.container_id.id,
                "access_log_id": self.id,
                "risk_level": risk_level,
            }

            audit_log = self.env["naid.audit.log"].create(audit_vals)
            self.write({"audit_trail_id": audit_log.id})
            self.message_post(body=_("Audit trail created: %s") % audit_log.name)
        except Exception as e:
            raise UserError(_("Could not create audit trail entry: %s") % e) from e

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
                record.message_post(
                    body=_("Warning: Unusually long access duration detected: %s seconds") % record.duration_seconds
                )


    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = _("%(name)s (%(container)s) - %(access_type)s by %(user)s") % {
                'name': record.name,
                'container': record.container_id.name or _('N/A'),
                'access_type': record.access_type.title() if record.access_type else '',
                'user': record.user_id.name
            }
            result.append((record.id, name))
        return result

    @api.model
    def _search_by_name_document_user(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, document, or user"""
        args = args or []
        domain = []

        if name:
            domain = [
                "|", "|",
                ("name", operator, name),
                ("container_id.name", operator, name),
                ("user_id.name", operator, name),
            ]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_access_statistics(self, domain=None, group_by="access_type"):
        """Get access statistics for reporting"""
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
        return {
            (item[group_by][1] if isinstance(item[group_by], tuple) else item[group_by] or 'N/A'):
            item["%s_count" % group_by]
            for item in grouped_data
        }


    def cleanup_old_logs(self, days=365):
        """Clean up old access logs based on retention policy"""
        _logger.info(_("Starting cleanup of old access logs older than %d days"), days)
        # The actual cleanup logic should be implemented here.
        # For example:
        # cutoff_date = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        # self.search([('access_date', '<', cutoff_date)]).unlink() # Unlink is blocked, so maybe archive.
        # self.search([('access_date', '<', cutoff_date)]).write({'active': False})

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

        return {
            'period': {'from': date_from, 'to': date_to},
            'summary': {
                'total_accesses': total_accesses,
                'successful_accesses': successful_accesses,
                'denied_accesses': denied_accesses,
                'high_risk_accesses': high_risk_accesses,
                'success_rate': (successful_accesses / total_accesses * 100) if total_accesses > 0 else 0,
            },
            'user_statistics': user_stats,
            'access_logs': access_logs.ids,
        }


    def action_export_audit_data(self):
        """Export audit data for compliance reporting"""
        self.ensure_one()

        export_data = {
            'log_reference': self.name,
            'container_name': self.container_id.name,
            'container_barcode': self.container_id.barcode,
            'access_user': self.user_id.name,
            'access_date': self.access_date.isoformat() if self.access_date else None,
            'access_type': self.access_type,
            'access_method': self.access_method,
            'access_result': self.access_result,
            'risk_score': self.risk_score,
            'compliance_required': self.compliance_required,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'business_justification': self.business_justification,
            'audit_trail_reference': self.audit_trail_id.name if self.audit_trail_id else None,
        }

        return export_data


    def get_security_dashboard_data(self):
        """Get data for security monitoring dashboard"""
        self.ensure_one()
        return {
            'access_date': self.access_date,
            'user_id': self.user_id.id,
            'access_type': self.access_type,
            'access_result': self.access_result,
            'risk_score': self.risk_score,
            'compliance_required': self.compliance_required,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
        }
