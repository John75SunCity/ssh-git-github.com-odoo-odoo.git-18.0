# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMoveSMSValidation(models.Model):
    """SMS validation for stock movements"""
    _name = 'stock.move.sms.validation'
    _description = 'Stock Move SMS Validation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _('New'))
    stock_move_id = fields.Many2one(comodel_name='stock.move', string="Stock Move", required=True)
    partner_id = fields.Many2one(related='stock_move_id.partner_id', string="Customer", readonly=True)

    # SMS fields
    phone_number = fields.Char(string="Phone Number", required=True)
    sms_message = fields.Text(string="SMS Message", required=True)
    sms_sent_date = fields.Datetime(string="SMS Sent Date", readonly=True)

    # Validation fields
    is_validated = fields.Boolean(string="Validated", default=False, tracking=True)
    validation_code = fields.Char(string="Validation Code", readonly=True)
    validation_date = fields.Datetime(string="Validation Date", readonly=True)
    validated_by_id = fields.Many2one(comodel_name='res.users', string="Validated By", readonly=True)

    # State management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'SMS Sent'),
        ('validated', 'Validated'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.move.sms.validation') or _('New')
        return super().create(vals_list)

    def action_send_sms(self):
        """Send SMS validation message"""
        self.ensure_one()

        if not self.phone_number:
            raise UserError(_("Phone number is required to send SMS."))

        if self.state != 'draft':
            raise UserError(_("SMS can only be sent from draft state."))

        # Generate validation code
        import random
        import string
        self.validation_code = ''.join(random.choices(string.digits, k=6))

        # Prepare SMS message with validation code
        message = _("Your validation code for stock movement %s is: %s") % (self.stock_move_id.name, self.validation_code)

        # Send SMS (integrate with SMS provider)
        try:
            self.env['sms.sms'].create({
                'number': self.phone_number,
                'body': message,
                'partner_id': self.partner_id.id,
            })

            self.write({
                'state': 'sent',
                'sms_sent_date': fields.Datetime.now(),
                'sms_message': message,
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('SMS Sent'),
                    'message': _('Validation SMS sent to %s') % self.phone_number,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_("Failed to send SMS: %s") % str(e))

    def action_validate_code(self, entered_code):
        """Validate the entered code"""
        self.ensure_one()

        if self.state != 'sent':
            raise UserError(_("Validation can only be done after SMS is sent."))

        if entered_code == self.validation_code:
            self.write({
                'is_validated': True,
                'state': 'validated',
                'validation_date': fields.Datetime.now(),
                'validated_by_id': self.env.user.id,
            })

            # Also update the stock move
            self.stock_move_id.write({'sms_validated': True})

            return True
        else:
            return False

    def action_cancel(self):
        """Cancel SMS validation"""
        self.ensure_one()
        self.state = 'cancelled'
