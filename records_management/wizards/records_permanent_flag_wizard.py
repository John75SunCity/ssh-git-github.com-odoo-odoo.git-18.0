# -*- coding: utf-8 -*-
"""
Records Permanent Flag Wizard
"""

from odoo import models, fields, api, _




class RecordsPermanentFlagWizard(models.TransientModel):
    """
    Records Permanent Flag Wizard
    """

    _name = "records.permanent.flag.wizard"
    _description = "Records Permanent Flag Wizard"

    # Core fields
    name = fields.Char(string="Flag Name", default="Permanent Flag Wizard")
    record_ids = fields.Many2many("records.container", string="Records to Flag")
    permanent_flag = fields.Boolean(string="Mark as Permanent", default=True)
    reason = fields.Text(string="Reason for Change", required=True)

    def action_apply_flag(self):
        """Apply the permanent flag to selected records"""

        self.ensure_one()
        for record in self.record_ids:
            record.write(
                {"permanent_flag": self.permanent_flag, "permanent_reason": self.reason}
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": f"Updated permanent flag for {len(self.record_ids)} records",
                "type": "success",
            },
        }
