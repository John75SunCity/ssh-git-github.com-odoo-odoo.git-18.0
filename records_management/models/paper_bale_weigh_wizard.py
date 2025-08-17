from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError


class GeneratedModel(models.Model):
    _name = 'paper.bale.weigh.wizard'
    _description = 'Paper Bale Weighing Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    bale_id = fields.Many2one('paper.bale', string='Paper Bale')
    measured_weight = fields.Float()
    weighing_date = fields.Datetime()
    scale_used = fields.Char(string='Scale Used')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_record_weight(self):
            self.ensure_one()
            if self.measured_weight <= 0:
                raise UserError(_("Measured weight must be positive."))
            self.bale_id.write()
                {}
                    "weight": self.measured_weight,
                    "last_weighed_date": self.weighing_date,


            return {"type": "ir.actions.act_window_close"}
