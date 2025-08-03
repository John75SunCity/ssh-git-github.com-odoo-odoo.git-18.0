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
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'Draft'), ('processing', 'Processing'), ('completed', 'Completed')], string='State', default='draft')
    notes = fields.Text(string='Notes')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    sequence = fields.Integer(string='Sequence', default=10)
    updated_date = fields.Datetime(string='Updated Date')
    # Records Permanent Flag Wizard Fields
    action_type = fields.Selection([('flag', 'Flag as Permanent'), ('unflag', 'Remove Permanent Flag')], default='flag')
    box_id = fields.Many2one('records.box', 'Box')
    customer_id = fields.Many2one('res.partner', 'Customer')
    document_count = fields.Integer('Document Count', default=0)
    permanent_flag = fields.Boolean('Permanent Flag', default=True)
    approval_required = fields.Boolean('Approval Required', default=True)
    justification_notes = fields.Text('Justification Notes')
    legal_basis = fields.Selection([('regulatory', 'Regulatory'), ('litigation', 'Litigation'), ('historical', 'Historical')], default='regulatory')
    notification_sent = fields.Boolean('Notification Sent', default=False)


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
