from odoo import fields, models

class FsmRoute(models.Model):
    _name = 'fsm.route'
    _description = 'FSM Route'

    name = fields.Char(string='Name', required=True)
    is_naid_compliant = fields.Boolean(string='NAID Compliant')
