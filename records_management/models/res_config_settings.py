# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_sms_receipt_template_id = fields.Many2one('sms.template', string='POS SMS Receipt Template', 
                                                  config_parameter='pos_sms.receipt_template_id',
                                                  domain="[('model', '=', 'pos.order')]",
                                                  help='SMS template for POS receipts (e.g., send confirmation after shred payment). Requires "sms" module.')
