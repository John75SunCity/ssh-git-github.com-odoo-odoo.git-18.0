# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PaperBaleInspectionWizard(models.TransientModel):
    """
    A wizard to facilitate the creation of a new paper bale inspection record.
    This model is transient, meaning its records are temporary and are automatically
    cleaned up by the system. It serves as an intermediary to gather user input
    before creating the persistent inspection record.
    """
    _name = 'paper.bale.inspection.wizard'
    _description = 'Wizard: Create Paper Bale Inspection'

    # ============================================================================
    # FIELDS
    # ============================================================================

    # Link to the bale being inspected. The active_id from the context is used
    # to default this value when the wizard is opened from a paper.bale form.
    bale_id = fields.Many2one(
        'paper.bale',
        string='Paper Bale',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )

    inspection_type = fields.Selection([
        ('moisture', 'Moisture Content'),
        ('contamination', 'Contamination Check'),
        ('grade', 'Grade Verification'),
        ('visual', 'Visual Inspection'),
        ('other', 'Other'),
    ], string="Inspection Type", required=True, default='visual')

    passed = fields.Boolean(string='Inspection Passed', default=True)

    # The rejection reason is only required if the inspection did not pass.
    rejection_reason = fields.Text(string='Rejection Reason')

    notes = fields.Text(string='Inspection Notes')

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_create_inspection(self):
        """
        Creates a new 'paper.bale.inspection' record based on the wizard's data.
        This method is triggered by a button on the wizard form.
        """
        self.ensure_one()

        # Validate that a rejection reason is provided for failed inspections.
        if not self.passed and not self.rejection_reason:
            raise UserError(_("A rejection reason is required for failed inspections."))

        # Prepare the values for the new inspection record.
        inspection_vals = {
            'bale_id': self.bale_id.id,
            'inspection_type': self.inspection_type,
            'passed': self.passed,
            'rejection_reason': self.rejection_reason,
            'notes': self.notes,
            # The inspector is the user who is currently running the wizard.
            'inspector_id': self.env.user.id,
        }

        # Create the persistent inspection record.
        self.env['paper.bale.inspection'].create(inspection_vals)

        # Close the wizard and refresh the view of the parent record.
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================

    @api.onchange('passed')
    def _onchange_passed(self):
        """
        Clears the rejection reason if the inspection is marked as passed.
        This provides a better user experience by removing irrelevant data automatically.
        """
        if self.passed:
            self.rejection_reason = False


