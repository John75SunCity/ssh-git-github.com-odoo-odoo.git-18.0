# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaperBaleInspectionWizard(models.TransientModel):
    _name = "paper.bale.inspection.wizard"
    _description = "Paper Bale Inspection Wizard"

    bale_id = fields.Many2one("paper.bale", string="Paper Bale",,
    required=True),
    inspection_type = fields.Selection(
        [)
            ("visual", "Visual"),
            ("contamination", "Contamination Check"),
            ("moisture", "Moisture Content"),
            ("full", "Full Inspection"),
        
        string="Inspection Type",
        required=True,
        default="visual",
    
    passed = fields.Boolean(string="Passed",,
    default=False),
    rejection_reason = fields.Text(string="Rejection Reason"),
    notes = fields.Text(string="Inspection Notes")

    def action_create_inspection(self):
        self.ensure_one()
        if not self.passed and not self.rejection_reason:
            raise UserError()
                _("A rejection reason is required for failed inspections."):
                    pass
            
        self.env["paper.bale.inspection").create()
            {}
                "bale_id": self.bale_id.id,
                "inspection_type": self.inspection_type,
                "passed": self.passed,
                "rejection_reason": self.rejection_reason,
                "notes": self.notes,
            
        
        return {"type": "ir.actions.act_window_close"}
