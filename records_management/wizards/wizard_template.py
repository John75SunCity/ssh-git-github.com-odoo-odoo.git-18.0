from odoo import models, fields, _
from odoo.exceptions import UserError


class WizardTemplate(models.TransientModel):
    """
    This is a template for creating new wizards. Wizards are temporary models
    used for interactive user dialogs. They do not store data permanently.

    To use this template:
    1. Copy this file to a new file in the 'wizards' directory (e.g., my_wizard.py).
    2. Rename the class (e.g., MyWizard).
    3. Change the _name (e.g., 'my.wizard').
    4. Add the necessary fields for your wizard's logic.
    5. Implement the logic in the action method.
    6. Create a corresponding view file in 'views/' (e.g., my_wizard_views.xml).
    7. Create an action to launch the wizard, often from a button on another model.
    """
    _name = 'wizard.template'
    _description = 'Wizard Template'

    # ============================================================================
    # FIELDS
    # ============================================================================

    # A note or description to display to the user in the wizard.
    note = fields.Text(string="Notes", readonly=True,
                       default="This is a template wizard. Replace this text and fields with your own logic.")

    # A field to capture a reason or comment from the user.
    reason = fields.Text(string="Reason", required=True)

    # A boolean field for a simple yes/no question.
    confirm_action = fields.Boolean(string="Confirm Action", default=True)

    # It's common to link a wizard to the record that opened it.
    # This is typically handled via context in the action that launches the wizard.
    # For example: context="{'default_related_record_id': active_id}"
    # related_record_id = fields.Many2one(comodel_name='source.model', string="Related Record")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_apply(self):
        """
        This is the main action method for the wizard. It is called when the
        user clicks the primary button (e.g., "Apply", "Confirm").
        """
        self.ensure_one()

        # Add your business logic here. For example, you might update the
        # record that launched the wizard.
        # active_id = self.env.context.get('active_id')
        # if active_id:
        #     record = self.env['source.model'].browse(active_id)
        #     record.write({'state': 'processed', 'notes': self.reason})

        if not self.confirm_action:
            raise UserError(_("You must confirm the action to proceed."))

        # Post a message to the chatter of the related record, if applicable.
        # record.message_post(body=_("Action performed with reason: %s", self.reason))

        # Wizards typically close themselves after the action is complete.
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """
        This action is typically linked to a "Cancel" button and simply
        closes the wizard without performing any action.
        """
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
