from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class KeyRestrictionManagementWizard(models.TransientModel):
    """Partner-centric wizard to manage key issuance restrictions.

    This wizard is opened from `res.partner` actions to either place a
    restriction (block key issuance) or allow keys again. It writes
    `res.partner.key.restriction` records and provides basic impact stats.
    """

    _name = 'key.restriction.management.wizard'
    _description = 'Key Restriction Management Wizard'

    # Context
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer/Contact',
        required=True,
        help='Target partner for key issuance policy.'
    )
    action = fields.Selection(
        selection=[('restrict', 'Restrict Key Issuance'), ('allow', 'Allow Key Issuance')],
        string='Action',
        required=True,
        default='restrict',
        help='Choose whether to restrict or allow key issuance.'
    )

    # Current status snapshot
    current_status = fields.Selection(
        selection=[('allowed', 'Allowed'), ('restricted', 'Restricted')],
        string='Current Status',
        compute='_compute_current_status',
        store=False,
    )

    # Restrict fields
    restriction_reason = fields.Selection([
        ('policy', 'Company Policy'),
        ('security', 'Security Requirements'),
        ('compliance', 'Compliance Requirements'),
        ('contract', 'Contract Terms'),
        ('risk', 'Risk Assessment'),
        ('other', 'Other'),
    ], string='Restriction Reason')
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today)
    restriction_notes = fields.Text(string='Restriction Notes')
    restriction_notes_placeholder = fields.Char(string='Notes Placeholder')

    # Allow fields
    allow_reason = fields.Text(string='Reason for Allowing Keys')
    notify_customer = fields.Boolean(string='Notify Customer of Change', default=False)

    # Impact analysis (computed, read-only)
    unlock_services_count = fields.Integer(string='Unlock Services (All Time)', compute='_compute_stats')
    active_keys_count = fields.Integer(string='Active Keys', compute='_compute_stats')
    pending_requests_count = fields.Integer(string='Pending Unlock Requests', compute='_compute_stats')
    recent_unlock_services_count = fields.Integer(string='Unlocks (Last 30 Days)', compute='_compute_stats')

    @api.depends('partner_id')
    def _compute_current_status(self):
        for wiz in self:
            if wiz.partner_id:
                # Mirror partner badge for clarity
                wiz.current_status = wiz.partner_id.key_restriction_status or 'allowed'
            else:
                wiz.current_status = False

    @api.depends('partner_id')
    def _compute_stats(self):
        for wiz in self:
            if not wiz.partner_id:
                wiz.unlock_services_count = 0
                wiz.active_keys_count = 0
                wiz.pending_requests_count = 0
                wiz.recent_unlock_services_count = 0
                continue

            partner = wiz.partner_id

            # Total unlock services (completed or invoiced as historical baseline)
            total_rows = partner.env['bin.unlock.service']._read_group(
                [('partner_id', '=', partner.id)], ['partner_id'], ['__count']
            )
            wiz.unlock_services_count = total_rows[0]['__count'] if total_rows else 0

            # Active keys – reuse partner computed stat when available
            wiz.active_keys_count = partner.active_bin_key_count if hasattr(partner, 'active_bin_key_count') else 0

            # Pending unlock-related requests (draft/scheduled/in progress)
            pending_rows = partner.env['bin.unlock.service']._read_group(
                [('partner_id', '=', partner.id), ('state', 'in', ['draft', 'scheduled', 'in_progress'])],
                ['partner_id'], ['__count']
            )
            wiz.pending_requests_count = pending_rows[0]['__count'] if pending_rows else 0

            # Recent unlock services in last 30 days
            today = fields.Date.context_today(wiz)
            # Convert to datetime filter via >= date; model uses date fields
            recent_rows = partner.env['bin.unlock.service']._read_group(
                [('partner_id', '=', partner.id), ('request_date', '>=', today - timedelta(days=30))],
                ['partner_id'], ['__count']
            )
            wiz.recent_unlock_services_count = recent_rows[0]['__count'] if recent_rows else 0

    def action_confirm(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('Please select a partner before confirming.'))

        if self.action == 'restrict':
            if not self.restriction_reason:
                raise UserError(_('Please select a restriction reason.'))
            vals = {
                'partner_id': self.partner_id.id,
                'key_issuance_allowed': False,
                'restriction_reason': dict(self._fields['restriction_reason'].selection).get(self.restriction_reason, self.restriction_reason),
                'effective_date': self.effective_date,
                'notes': self.restriction_notes,
                'state': 'draft',
            }
            restr = self.env['res.partner.key.restriction'].create(vals)
            # Immediately activate to reflect policy change
            if hasattr(restr, 'action_activate'):
                restr.action_activate()
            msg = _('Key issuance has been RESTRICTED for %s.') % (self.partner_id.display_name,)
            self.partner_id.message_post(body=msg)
        else:
            # Allow keys – either create an "allow" record (allowed=True) or revoke active restrictions
            # Strategy: create an explicit record marking allowed for audit trail
            vals = {
                'partner_id': self.partner_id.id,
                'key_issuance_allowed': True,
                'restriction_reason': self.allow_reason or _('Restriction removed by %s') % (self.env.user.display_name,),
                'effective_date': fields.Date.context_today(self),
                'notes': self.allow_reason,
                'state': 'draft',
            }
            record = self.env['res.partner.key.restriction'].create(vals)
            if hasattr(record, 'action_activate'):
                record.action_activate()
            # Optionally notify
            if self.notify_customer and hasattr(self.partner_id, 'message_post'):
                note = _('Key issuance has been ALLOWED for %s.') % (self.partner_id.display_name,)
                self.partner_id.message_post(body=note)

        # Close wizard
        return {'type': 'ir.actions.act_window_close'}
