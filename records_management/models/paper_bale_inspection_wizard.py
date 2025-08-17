from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError


class GeneratedModel(models.Model):
    _name = 'paper.bale.inspection.wizard'
    _description = 'Paper Bale Inspection Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    bale_id = fields.Many2one('paper.bale', string='Paper Bale')
    inspection_type = fields.Selection()
    passed = fields.Boolean(string='Passed')
    rejection_reason = fields.Text(string='Rejection Reason')
    notes = fields.Text(string='Inspection Notes')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_create_inspection(self):
            self.ensure_one()
            if not self.passed and not self.rejection_reason:
                raise UserError()
                    _("A rejection reason is required for failed inspections."):
                        pass

            self.env["paper.bale.inspection").create(]
                {}
                    "bale_id": self.bale_id.id,
                    "inspection_type": self.inspection_type,
                    "passed": self.passed,
                    "rejection_reason": self.rejection_reason,
                    "notes": self.notes,


            return {"type": "ir.actions.act_window_close"}

