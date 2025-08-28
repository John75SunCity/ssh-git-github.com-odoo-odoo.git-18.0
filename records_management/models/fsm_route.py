from odoo import fields, models

class FsmRoute(models.Model):
    _name = 'fsm.route'
    _description = 'FSM Route'

    name = fields.Char(string='Name', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")  # Use standard fleet.vehicle
    is_naid_compliant = fields.Boolean(string='NAID Compliant')
