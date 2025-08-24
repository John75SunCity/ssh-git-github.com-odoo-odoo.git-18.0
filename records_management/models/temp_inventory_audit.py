import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TempInventoryAudit(models.Model):
    _name = 'temp.inventory.audit'
    _description = 'Temporary Inventory Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    inventory_id = fields.Many2one(
        'customer.inventory',
        string="Inventory Record",
        required=True,
        ondelete='cascade'
    )
    date = fields.Datetime(string="Date", default=fields.Datetime.now, readonly=True)
    event_type = fields.Selection([
        ('create', 'Created'),
        ('write', 'Modified'),
        ('unlink', 'Deleted'),
        ('move', 'Moved'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string="Event Type", required=True)

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user, readonly=True)
    details = fields.Text(string="Details")
    ip_address = fields.Char(string='IP Address', readonly=True)
    active = fields.Boolean(default=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('event_type', 'user_id', 'date')
    def _compute_display_name(self):
        """Compute a descriptive display name for the audit log."""
        for record in self:
            event_label = dict(record._fields['event_type'].selection).get(record.event_type, record.event_type)
            user_name = record.user_id.name if record.user_id else _("Unknown User")
            record.display_name = _("%s by %s on %s", event_label, user_name, fields.Datetime.to_string(record.date))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically capture the IP address from the request context."""
        ip_address = self.env.context.get('ip_address') or (self.env.cr.transaction.ip if hasattr(self.env.cr, 'transaction') else 'N/A')
        for vals in vals_list:
            if 'ip_address' not in vals:
                vals['ip_address'] = ip_address
        return super(TempInventoryAudit, self).create(vals_list)

    # ============================================================================
    # Business Logic Methods
    # ============================================================================
    def get_audit_summary(self):
        """Get audit summary for reporting"""
        return {
            'total_events': self.search_count([]),
            'events_by_type': self._get_events_by_type(),
            'recent_activity': self.search([], limit=10, order='date desc')
        }

    def _get_events_by_type(self):
        """Helper method to get event counts by type"""
        result = {}
        for event_type, label in self._fields['event_type'].selection:
            count = self.search_count([('event_type', '=', event_type)])
            result[event_type] = {'label': label, 'count': count}
        return result

    @api.model
    def create_audit_log(self, inventory_id, event_type, details=None, ip_address=None):
        """Create an audit log entry"""
        vals = {
            'inventory_id': inventory_id,
            'event_type': event_type,
            'details': details,
        }
        if ip_address:
            vals['ip_address'] = ip_address
        return self.create(vals)

    def get_user_activity(self, user_id=None, date_from=None, date_to=None):
        """Get user activity for specified period"""
        domain = []
        if user_id:
            domain.append(('user_id', '=', user_id))
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        return self.search(domain, order='date desc')

    def get_inventory_audit_trail(self, inventory_id):
        """Get complete audit trail for specific inventory"""
        return self.search([("inventory_id", "=", inventory_id)], order="date desc")

    def cleanup_old_audit_logs(self, days_to_keep=365):
        """Cleanup old audit logs (automated method)"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        old_logs = self.search([("date", "<", cutoff_date)])
        if old_logs:
            _logger.info(f"Cleaning up {len(old_logs)} old audit logs older than {days_to_keep} days")
            old_logs.unlink()
        return len(old_logs)
