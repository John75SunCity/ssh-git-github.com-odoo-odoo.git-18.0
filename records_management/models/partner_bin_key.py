from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class PartnerBinKey(models.Model):
    _name = 'partner.bin.key'
    _description = 'Partner Bin Key Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'key_number, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Key Reference', compute='_compute_name', store=True)
    key_number = fields.Char(string='Key Number', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    partner_id = fields.Many2one('res.partner', string='Assigned Customer', tracking=True)
    assigned_contact_id = fields.Many2one(
        "res.partner", string="Assigned Contact", domain="[('parent_id', '=', partner_id)]", tracking=True
    )

    status = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('lost', 'Lost'),
        ('returned', 'Returned'),
        ('decommissioned', 'Decommissioned'),
    ], string='Status', default='available', required=True, tracking=True)

    issue_date = fields.Date(string='Issue Date', tracking=True)
    return_date = fields.Date(string='Return Date', tracking=True)

    notes = fields.Text(string='Notes')

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('key_number', 'partner_id.name')
    def _compute_name(self):
        for key in self:
            if key.partner_id:
                key.name = _("Key %s (Assigned to %s)") % (key.key_number, key.partner_id.name)
            else:
                key.name = _("Key %s", key.key_number)

    @api.constrains("key_number", "company_id", "active")
    def _check_unique_key_number_active(self):
        for record in self:
            if record.active:
                domain = [
                    ("key_number", "=", record.key_number),
                    ("company_id", "=", record.company_id.id),
                    ("active", "=", True),
                    ("id", "!=", record.id),
                ]
                count = self.search_count(domain)
                if count > 0:
                    raise ValidationError(_("Key Number must be unique per company for active records."))

    @api.constrains('status', 'partner_id', 'assigned_contact_id', 'issue_date')
    def _check_assignment_consistency(self):
        for key in self:
            if key.status == 'assigned' and (not key.partner_id or not key.issue_date):
                raise ValidationError(_("Assigned keys must have a customer and an issue date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_report_lost(self):
        self.ensure_one()
        if self.status != 'assigned':
            raise UserError(_("Only an assigned key can be reported as lost."))
        self.write({
            'status': 'lost',
            'return_date': fields.Date.context_today(self),
        })
        self.message_post(body=_("Key reported as lost by %s.", self.env.user.name))

    def action_return_key(self):
        self.ensure_one()
        if self.status != 'assigned':
            raise UserError(_("Only an assigned key can be returned."))
        self.write({
            'status': 'returned',
            'return_date': fields.Date.context_today(self),
        })
        self.message_post(body=_("Key marked as returned by %s.", self.env.user.name))

    def action_make_available(self):
        self.ensure_one()
        if self.status not in ['returned', 'decommissioned']:
            raise UserError(_("Only returned or decommissioned keys can be made available again."))
        self.write({
            'status': 'available',
            'partner_id': False,
            'assigned_contact_id': False,
            'issue_date': False,
            'return_date': False,
        })
        self.message_post(body=_("Key is now available for assignment."))

    def action_decommission(self):
        self.ensure_one()
        self.write({
            'status': 'decommissioned',
            'active': False,
        })
        self.message_post(body=_("Key has been decommissioned."))
