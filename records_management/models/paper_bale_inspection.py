# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBaleInspection(models.Model):
    _name = "paper.bale.inspection"
    _description = "Paper Bale Inspection"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    )
    inspection_date = fields.Datetime(
        string="Inspection Date", required=True, default=fields.Datetime.now
    )
    inspector_id = fields.Many2one(
        "res.users", string="Inspector", default=lambda self: self.env.user
    )
    inspection_type = fields.Selection(
        [
            ("visual", "Visual"),
            ("contamination", "Contamination Check"),
            ("moisture", "Moisture Content"),
            ("full", "Full Inspection"),
        ],
        string="Inspection Type",
        required=True,
        default="visual",
    )
    passed = fields.Boolean(string="Passed", default=False)
    notes = fields.Text(string="Inspection Notes")
    rejection_reason = fields.Text(string="Rejection Reason")

    @api.constrains("passed", "rejection_reason")
    def _check_rejection_reason(self):
        for inspection in self:
            if not inspection.passed and not inspection.rejection_reason:
                raise ValidationError(
                    _("A rejection reason is required for failed inspections.")
                )

    def action_pass_inspection(self):
        self.ensure_one()
        self.write({"passed": True, "rejection_reason": ""})

    def action_fail_inspection(self, rejection_reason):
        self.ensure_one()
        if not rejection_reason:
            raise ValidationError(_("A rejection reason must be provided."))
        self.write({"passed": False, "rejection_reason": rejection_reason})
