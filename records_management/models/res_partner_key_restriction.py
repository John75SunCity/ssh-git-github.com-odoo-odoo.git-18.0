from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ResPartnerKeyRestriction(models.Model):
    _name = 'res.partner.key.restriction'
    _description = 'Partner Key Access Restriction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'effective_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Restriction Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Customer/Contact", required=True, ondelete='cascade', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # ============================================================================
    # RESTRICTION DETAILS & LIFECYCLE
    # ============================================================================
    key_issuance_allowed = fields.Boolean(
        string="Key Issuance Allowed",
        default=False,
        help="Check this box if the partner is allowed to be issued physical keys. Uncheck to restrict access."
    )
    restriction_reason = fields.Text(string="Reason for Restriction", help="Explain why key issuance is restricted for this partner.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # DATES & RESPONSIBILITY
    # ============================================================================
    effective_date = fields.Date(string="Effective Date", default=fields.Date.context_today, required=True, tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, tracking=True)
    notes = fields.Text(string='Internal Notes')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                partner = self.env['res.partner'].browse(vals.get('partner_id'))
                vals['name'] = self.env['ir.sequence'].next_by_code('res.partner.key.restriction') or _('New')
                if partner:
                    vals['name'] = f"{partner.name} - {vals['name']}"
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft restrictions can be activated."))
        self.write({'state': 'active'})
        self.message_post(body=_("Key restriction has been activated."))

    def action_revoke(self):
        self.ensure_one()
        if self.state not in ('active', 'expired'):
            raise UserError(_("Only active or expired restrictions can be revoked."))
        self.write({'state': 'revoked'})
        self.message_post(body=_("Key restriction has been revoked."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Restriction reset to draft."))

    # ============================================================================
    # AUTOMATED ACTIONS (CRON)
    # ============================================================================
    @api.model
    def _cron_expire_restrictions(self):
        """
        Scheduled action to automatically expire restrictions where the expiry date has passed.
        """
        today = date.today()
        expired_restrictions = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today)
        ])
        if expired_restrictions:
            expired_restrictions.write({'state': 'expired'})
            for restriction in expired_restrictions:
                restriction.message_post(body=_("This key restriction has automatically expired."))
