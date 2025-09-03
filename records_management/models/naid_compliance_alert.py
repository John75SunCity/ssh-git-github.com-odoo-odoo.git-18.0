from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class NaidComplianceAlert(models.Model):
    _name = 'naid.compliance.alert'
    _description = 'NAID Compliance Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'alert_date desc, severity desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string='Title', required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    active = fields.Boolean(string='Active', default=True, help="The active field is used to hide the alert without deleting it.")

    # Polymorphic relationship to link alert to any record
    res_model = fields.Char(string='Related Model', readonly=True)
    res_id = fields.Integer(string='Related Record ID', readonly=True)
    res_name = fields.Char(string='Related Record', compute='_compute_res_name')

    alert_date = fields.Datetime(string='Alert Date', default=fields.Datetime.now, readonly=True)
    alert_type = fields.Selection([
        ('security', 'Security'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
        ('system', 'System'),
    ], string='Alert Type', required=True, readonly=True)

    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', default='medium', required=True, tracking=True)

    description = fields.Text(string='Alert Description', required=True, readonly=True)
    status = fields.Selection([
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], string='Status', default='new', readonly=True, tracking=True)

    resolved_date = fields.Datetime(string='Resolved Date', readonly=True)
    resolved_by_id = fields.Many2one('res.users', string='Resolved By', readonly=True)
    resolution_notes = fields.Text(string='Resolution Notes')

    escalated_to_id = fields.Many2one('res.users', string='Escalated To', readonly=True)
    escalation_date = fields.Datetime(string='Last Escalation Date', readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for alert in self:
            if alert.res_model and alert.res_id:
                try:
                    record = self.env[alert.res_model].browse(alert.res_id).exists()
                    alert.res_name = record.display_name if record else _('N/A')
                except (KeyError, AttributeError):
                    alert.res_name = f"{alert.res_model}/{alert.res_id}"
            else:
                alert.res_name = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_acknowledge(self):
        self.ensure_one()
        if self.status != 'new':
            raise UserError(_("Only new alerts can be acknowledged."))
        self.write({'status': 'acknowledged'})
        self.message_post(body=_("Alert acknowledged by %s.", self.env.user.name))

    def action_resolve(self):
        self.ensure_one()
        if not self.resolution_notes:
            raise UserError(_("Resolution notes are required to resolve an alert."))
        self.write({
            'status': 'resolved',
            'resolved_by_id': self.env.user.id,
            'resolved_date': fields.Datetime.now(),
            'active': False,
        })
        self.message_post(body=_("Alert resolved by %s.", self.env.user.name))

    def action_dismiss(self):
        self.ensure_one()
        if not self.resolution_notes:
            raise UserError(_("Notes are required to dismiss an alert."))
        self.write({
            'status': 'dismissed',
            'resolved_by_id': self.env.user.id,
            'resolved_date': fields.Datetime.now(),
            'active': False,
        })
        self.message_post(body=_("Alert dismissed by %s.", self.env.user.name))

    def action_escalate(self):
        self.ensure_one()
        manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
        if not manager_group:
            raise UserError(_("The 'Records Manager' security group could not be found."))

        # Find a manager who is not the current user
        manager_users = manager_group.users.filtered(lambda u: u.id != self.env.user.id)
        if not manager_users:
            raise UserError(_("No other managers available to escalate to."))

        target_user = manager_users[0]
        self.write({
            'escalated_to_id': target_user.id,
            'escalation_date': fields.Datetime.now(),
        })
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Escalated Alert: %s", self.title),
            note=_("A compliance alert has been escalated for your review."),
            user_id=target_user.id,
        )
        self.message_post(body=_("Alert escalated to %s.", target_user.name))

    # ============================================================================
    # AUTOMATION
    # ============================================================================
    @api.model
    def _check_alert_escalation(self):
        """Cron job to automatically escalate overdue critical alerts."""
        critical_alerts = self.search([
            ('status', 'in', ('new', 'acknowledged')),
            ('severity', '=', 'critical'),
            ('alert_date', '<=', fields.Datetime.now() - timedelta(hours=24))
        ])
        for alert in critical_alerts:
            alert.action_escalate()

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('naid.compliance.alert') or _('New')
        alerts = super().create(vals_list)

        # Notify managers for critical alerts
        manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
        for alert in alerts.filtered(lambda a: a.severity == 'critical'):
            alert.message_post(
                body=_("A new critical compliance alert has been created: %s", alert.title),
                partner_ids=manager_group.users.partner_id.ids if manager_group else [],
            )
        return alerts
