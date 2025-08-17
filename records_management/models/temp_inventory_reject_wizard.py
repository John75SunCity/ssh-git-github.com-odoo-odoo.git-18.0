from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, _


class GeneratedModel(models.Model):
    _name = 'temp.inventory.reject.wizard'
    _description = 'Temporary Inventory Reject Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    inventory_id = fields.Many2one()
    rejection_reason = fields.Text(string='Rejection Reason')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_confirm_rejection(self):
            self.ensure_one()
            self.inventory_id.write()
                {}
                    "state": "cancelled",
                    "rejection_reason": self.rejection_reason,


            self.inventory_id.message_post()
                body=_("Inventory rejected. Reason: %s", self.rejection_reason)

            return {"type": "ir.actions.act_window_close"}
