# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsPermanentFlagWizard(models.TransientModel):
    _name = "records.permanent.flag.wizard"
    _description = "Records Permanent Flag Wizard"

    # Basic Information
    name = fields.Char(string="Flag Name", required=True, default="Permanent Flag")
    document_ids = fields.Many2many("records.document", string="Documents")
    reason = fields.Text(string="Reason")

    def action_confirm(self):
        """Apply permanent flag to documents."""
        self.ensure_one()

        for document in self.document_ids:
            document.write(
                {
                    "notes": (document.notes or "")
                    + _("\nMarked permanent via wizard on %s")
                    % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Flag Applied"),
                "message": _("Permanent flag has been applied to selected documents."),
                "type": "success",
                "sticky": False,
            },
        }
