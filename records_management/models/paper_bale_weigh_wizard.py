# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PaperBaleWeighWizard(models.TransientModel):
    """
    A wizard to facilitate weighing paper bales and updating their weight information.
    This model is transient, meaning its records are temporary and are automatically
    cleaned up by the system. It serves as an intermediary to gather weight input
    before updating the persistent bale record.
    """
    _name = 'paper.bale.weigh.wizard'
    _description = 'Wizard: Weigh Paper Bale'

    # ============================================================================
    # FIELDS
    # ============================================================================

    # Link to the bale being weighed. The active_id from the context is used
    # to default this value when the wizard is opened from a paper.bale form.
    bale_id = fields.Many2one(
        'paper.bale',
        string='Paper Bale',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )

    # Display current weight for reference
    current_weight = fields.Float(
        string='Current Weight (kg)',
        related='bale_id.weight',
        readonly=True
    )

    # New weight to be recorded
    new_weight = fields.Float(
        string='New Weight (kg)',
        required=True,
        help="Enter the measured weight of the bale"
    )

    # Optional weigh date (defaults to now)
    weigh_date = fields.Datetime(
        string='Weigh Date',
        default=fields.Datetime.now,
        required=True
    )

    # Notes about the weighing process
    notes = fields.Text(string='Weighing Notes')

    # Show reference information
    name = fields.Char(
        string='Bale Reference',
        related='bale_id.name',
        readonly=True
    )

    bale_number = fields.Char(
        string='Bale Number',
        related='bale_id.bale_number',
        readonly=True
    )

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_confirm_weight(self):
        """
        Updates the paper bale with the new weight and creates a movement record.
        This method is triggered by a button on the wizard form.
        """
        self.ensure_one()

        # Validate the weight input
        if self.new_weight <= 0:
            raise UserError(_("Weight must be greater than zero."))

        # Update the bale with the new weight
        self.bale_id.write({
            'weight': self.new_weight,
            'weigh_date': self.weigh_date,
            'state': 'weighed' if self.bale_id.state == 'draft' else self.bale_id.state
        })

        # Create a movement record for tracking
        if 'paper.bale.movement' in self.env:
            movement_vals = {
                'bale_id': self.bale_id.id,
                'movement_type': 'weigh',
                'movement_date': self.weigh_date,
                'weight_before': self.current_weight,
                'weight_after': self.new_weight,
                'notes': self.notes or _("Bale weighed via wizard"),
                'responsible_user_id': self.env.user.id,
            }
            self.env['paper.bale.movement'].create(movement_vals)

        # Log the weight change in the chatter
        message_body = "Bale weighed: %s kg (was %s kg). Notes: %s" % (
            self.new_weight, self.current_weight or 0, self.notes or "No notes"
        )
        self.bale_id.message_post(body=message_body)

        # Close the wizard and show success message
        notification_message = "Bale %s has been weighed: %s kg" % (
            self.bale_id.name, self.new_weight
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Weight Updated"),
                'message': notification_message,
                'type': 'success',
                'sticky': False,
            }
        }    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================

    @api.onchange('bale_id')
    def _onchange_bale_id(self):
        """
        Updates related fields when the bale is changed.
        """
        if self.bale_id:
            # Pre-fill with current weight if available
            if self.bale_id.weight:
                self.new_weight = self.bale_id.weight

    @api.constrains('new_weight')
    def _check_weight_positive(self):
        """
        Ensures the weight is positive.
        """
        for record in self:
            if record.new_weight <= 0:
                raise ValidationError(_("Weight must be greater than zero."))
