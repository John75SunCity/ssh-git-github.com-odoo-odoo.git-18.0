import random
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMoveSMSValidation(models.Model):
    _name = 'stock.move.sms.validation'
    _description = 'Stock Move SMS Validation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    move_id = fields.Many2one('stock.move', string="Stock Move", required=True, readonly=True, ondelete='cascade')
    picking_id = fields.Many2one(related='move_id.picking_id', string="Transfer", store=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible User", required=True, readonly=True, help="User who must validate this move.")
    sms_code = fields.Char(string="SMS Code", readonly=True, copy=False)
    is_validated = fields.Boolean(string="Validated", default=False, readonly=True, copy=False)
    validation_date = fields.Datetime(string="Validation Date", readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence for name and a random SMS code."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.move.sms.validation') or _('New')
            vals['sms_code'] = self._generate_sms_code()
        return super().create(vals_list)

    def unlink(self):
        """Prevent deletion of non-validated or recent validation records."""
        for record in self:
            if record.is_validated:
                raise UserError(_("Cannot delete a validation record that has already been used."))
        return super().unlink()

    # ============================================================================
    # BUSINESS & HELPER METHODS
    # ============================================================================
    def _generate_sms_code(self, length=6):
        """Generate a random numeric code."""
        return ''.join(random.choices(string.digits, k=length))

    def action_send_sms(self):
        """Sends the validation code via SMS to the responsible user."""
        self.ensure_one()
        if not self.user_id.mobile:
            raise UserError(_("The responsible user (%s) does not have a mobile number configured.") % self.user_id.name)

        # This assumes the 'sms' module is installed and configured.
        body = _("Your validation code for transfer %s is: %s") % (self.picking_id.name, self.sms_code)
        self.env['sms.api']._send_sms([self.user_id.mobile], body)
        self.message_post(body=_("Validation SMS sent to %s.") % self.user_id.name)
        return True

    def action_validate(self, provided_code):
        """Validates the provided code and marks the record as validated."""
        self.ensure_one()
        if self.is_validated:
            raise UserError(_("This move has already been validated."))

        if self.sms_code == provided_code:
            self.write({
                'is_validated': True,
                'validation_date': fields.Datetime.now(),
            })
            self.message_post(body=_("Successfully validated by %s.") % self.env.user.name)
            return True
        else:
            self.message_post(body=_("Failed validation attempt by %s.") % self.env.user.name)
            raise UserError(_("The provided validation code is incorrect."))
