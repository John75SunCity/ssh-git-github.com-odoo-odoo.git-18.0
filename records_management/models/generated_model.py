from odoo import models, fields, _
from odoo.exceptions import UserError


class GeneratedModel(models.Model):
    """
    This model represents a wizard for recording the weight of paper bales.
    It allows users to input the measured weight, the date of weighing, and the scale used.
    The recorded weight is then updated in the associated paper bale record.
    """
    _name = 'paper.bale.weigh.wizard'
    _description = 'Paper Bale Weighing Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    bale_id = fields.Many2one('paper.bale', string='Paper Bale')
    """Reference to the paper bale being weighed."""

    measured_weight = fields.Float()
    """The measured weight of the paper bale."""

    weighing_date = fields.Datetime()
    """The date and time when the weighing was performed."""

    scale_used = fields.Char(string='Scale Used')
    """The name or identifier of the scale used for weighing."""

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_record_weight(self):
        """
        Records the measured weight of the paper bale.

        This method ensures that the measured weight is positive and updates the
        associated paper bale record with the new weight and weighing date.

        Raises:
            UserError: If the measured weight is not positive.

        Returns:
            dict: An action to close the wizard window.
        """
        self.ensure_one()
        if self.measured_weight <= 0:
            raise UserError(_("Measured weight must be positive."))
        self.bale_id.write({
            "weight": self.measured_weight,
            "last_weighed_date": self.weighing_date,
        })
        return {"type": "ir.actions.act_window_close"}
