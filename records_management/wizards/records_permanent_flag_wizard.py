# -*- coding: utf-8 -*-
"""
Records Permanent Flag Wizard
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    # ============================================================================
    # WIZARD CONFIGURATION
    # ============================================================================
    state = fields.Selection(
        [
            ("selection", "Selection"),
            ("confirmation", "Confirmation"),
            ("done", "Done"),
        ],
        default="selection",
        string="State",
    )

    operation_type = fields.Selection(
        [("set", "Set Permanent Flag"), ("remove", "Remove Permanent Flag")],
        string="Operation",
        required=True,
        default="set",
    )

    # ============================================================================
    # SELECTION CRITERIA
    # ============================================================================
    container_ids = fields.Many2many("records.container", string="Containers")
    document_ids = fields.Many2many("records.document", string="Selected Documents")
    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count"
    )

    # ============================================================================
    # JUSTIFICATION & AUDITING
    # ============================================================================
    confirm = fields.Boolean(string="Confirm Change", required=True, help="Check this box to confirm you want to apply this change.")
    reason = fields.Text(string="Reason for Change (Optional)", help="Provide an optional justification for this operation. This will be logged for audit purposes.")
    user_password = fields.Char(string="Your Password (Optional)", help="If you enter a password, it will be validated to confirm the operation.")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        for wizard in self:
            wizard.document_count = len(wizard.document_ids)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("container_ids")
    def _onchange_container_ids(self):
        """When containers are selected, find all their associated documents."""
        if self.container_ids:
            documents = self.env["records.document"].search(
                [("container_id", "in", self.container_ids.ids)]
            )
            self.document_ids = [(6, 0, documents.ids)]
        else:
            self.document_ids = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_selection(self):
        """Move to the confirmation step after selecting documents."""
        self.ensure_one()
        if not self.document_ids:
            raise UserError(
                _("You must select at least one document or container to proceed.")
            )
        self.state = "confirmation"
        return self._reopen_wizard()

    def action_apply_changes(self):
        """Final step to apply the permanent flag changes to the documents."""
        self.ensure_one()

        if not self.confirm:
            raise UserError(_("You must check the confirmation box to apply the changes."))

        # Optional password validation
        if self.user_password:
            if not self.env.user.check_credentials(self.user_password):
                raise UserError(_("Invalid password. The operation has been cancelled."))

        is_setting_flag = self.operation_type == 'set'

        log_message = _("Permanent flag set by %s.") % self.env.user.name
        if self.reason:
            log_message += _(" Reason: %s") % self.reason

        if not is_setting_flag:
            log_message = _("Permanent flag removed by %s.") % self.env.user.name
            if self.reason:
                log_message += _(" Reason: %s") % self.reason

        # Apply changes and log the action on each document
        for doc in self.document_ids:
            doc.write(
                {
                    "is_permanent": is_setting_flag,
                    "permanent_reason": self.reason,
                }
            )
            doc.message_post(body=log_message)

        self.state = "done"
        return self._reopen_wizard()

    def action_cancel(self):
        """Close the wizard."""
        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _reopen_wizard(self):
        """Helper to return the action to reopen the wizard window."""
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
