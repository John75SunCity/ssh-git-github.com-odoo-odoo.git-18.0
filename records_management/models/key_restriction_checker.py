from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class KeyRestrictionChecker(models.Model):
    _name = 'key.restriction.checker'
    _description = 'Key Restriction Checker Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Check Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Checked By', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)

    restriction_type = fields.Selection([
        ('none', 'None'),
        ('blacklist', 'Blacklisted'),
        ('whitelist', 'Whitelisted'),
        ('limited', 'Limited Access')
    ], string='Restriction Type', default='none', tracking=True)

    access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read-Only'),
        ('full', 'Full Access')
    ], string='Access Level', default='none', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked', 'Checked'),
        ('violation', 'Violation Detected'),
        ('resolved', 'Resolved')
    ], string='Status', default='draft', tracking=True)

    bin_number = fields.Char(string='Bin Number', tracking=True)
    key_allowed = fields.Boolean(string='Key Allowed', readonly=True)
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', readonly=True)
    authorization_bypass_used = fields.Boolean(string='Bypass Used', readonly=True)
    override_reason = fields.Text(string='Override Reason', readonly=True)
    security_violation_detected = fields.Boolean(string='Violation Detected', readonly=True)

    expiration_date = fields.Date(string='Restriction Expiry Date')
    last_check_date = fields.Datetime(string='Last Check Time', readonly=True)

    notes = fields.Text(string='Check Notes')
    restriction_reason = fields.Text(string='Reason for Restriction')

    is_expired = fields.Boolean(string="Is Expired", compute='_compute_expiration_status')
    days_until_expiration = fields.Integer(string="Days to Expire", compute='_compute_expiration_status')

    # Essential fields for key restriction functionality
    related_user_id = fields.Many2one('res.users', string='Related User')
    related_partner_id = fields.Many2one('res.partner', string='Related Customer')
    related_bin_id = fields.Many2one('shred.bin', string='Related Bin')
    related_container_id = fields.Many2one('records.container', string='Related Container')

    # Optional fields for extended functionality (only if modules are installed)
    related_project_task_id = fields.Many2one('project.task', string='Related Project Task')
    related_sale_order_id = fields.Many2one('sale.order', string='Related Sale Order')
    related_invoice_id = fields.Many2one('account.move', string='Related Invoice')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('key.restriction.checker') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track updates and log messages."""
        if any(key in self for key in ('state', 'restriction_type', 'access_level')):
            self.message_post(body=_("Restriction details updated."))
        return super().write(vals)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('expiration_date')
    def _compute_expiration_status(self):
        """Compute if the restriction has expired and days remaining."""
        for record in self:
            if record.expiration_date:
                today = date.today()
                delta = record.expiration_date - today
                record.is_expired = delta.days < 0
                record.days_until_expiration = delta.days if delta.days >= 0 else 0
            else:
                record.is_expired = False
                record.days_until_expiration = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def _check_restrictions(self):
        """Check customer and bin restrictions."""
        self.ensure_one()
        # Placeholder for actual restriction checking logic
        # This would query other models based on self.partner_id and self.bin_number
        self.write({
            'state': 'checked',
            'key_allowed': True, # Default to allowed, logic would change this
            'last_check_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Restriction check performed."))

    def action_reset(self):
        """Reset checker to initial state."""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'key_allowed': False,
            'security_violation_detected': False,
            'override_reason': False,
        })

    def action_escalate_violation(self):
        """Escalate security violation to management."""
        self.ensure_one()
        if not self.security_violation_detected:
            raise UserError(_("There is no security violation to escalate."))
        # Logic to create an activity for a security manager
        self.message_post(body=_("Security violation has been escalated."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('restriction_type', 'access_level')
    def _check_access_consistency(self):
        """Validate access level is consistent with restriction type."""
        for record in self:
            if record.restriction_type == "blacklist" and record.access_level == "full":
                raise ValidationError(_("Blacklisted entries cannot have full access level."))
