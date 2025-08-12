# -*- coding: utf-8 -*-
from odoo import models, fields, _


class TempInventoryRejectWizard(models.TransientModel):
    _name = "temp.inventory.reject.wizard"
    _description = "Temporary Inventory Reject Wizard"

    inventory_id = fields.Many2one(
        "temp.inventory", string="Inventory", required=True
    )
    rejection_reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm_rejection(self):
        self.ensure_one()
        self.inventory_id.write(
            {
                "state": "cancelled",
                "rejection_reason": self.rejection_reason,
            }
        )
        self.inventory_id.message_post(
            body=_("Inventory rejected. Reason: %s", self.rejection_reason)
        )
        return {"type": "ir.actions.act_window_close"}
