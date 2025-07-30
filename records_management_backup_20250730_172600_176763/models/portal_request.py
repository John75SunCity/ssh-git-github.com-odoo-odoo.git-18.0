# -*- coding: utf-8 -*-
""",
Portal Request Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PortalRequest(models.Model):
    """,
    Portal Request Management
    Customer requests submitted through the portal
    """

    _name = "portal.request",
    _description = "Portal Request",
    _inherit = ["mail.thread", "mail.activity.mixin"],
    _order = "request_date desc, name",
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields."state": "submitted"("state": "submitted")
                                            self.message_post(body=_("Request submitted"))

        # Create activity for staff to acknowledge:
                                            self.activity_schedule()
                                            "mail.mail_activity_data_call",
                                            summary="New Portal Request",
                                            note=f"New (self.request_type) request from (self.customer_id.name)",
                                            user_id=self.user_id.id

def action_acknowledge(self):
                                                """Acknowledge the request""",
                                                self.ensure_one()
if self.state != "submitted":
                                                    raise UserError(_("Only submitted requests can be acknowledged"))

                                                    self.write()
                                                    ()
                                                    "state": "acknowledged",
                                                    "acknowledged_date": fields.Date.today(),
                                                    "acknowledged_by": self.env.user.id,
                                                    
                                                    
                                                    self.message_post(body=_("Request acknowledged"))

def action_start_progress(self):
                                                        """Start working on the request""",
                                                        self.ensure_one()
if self.state != "acknowledged":
                                                            raise UserError(_("Only acknowledged requests can be started"))

                                                            self.write(("state": "in_progress"))
                                                            self.message_post(body=_("Started working on request"))

def action_complete(self):
                                                                """Complete the request""",
                                                                self.ensure_one()
if self.state != "in_progress":
                                                                    raise UserError(_("Only in-progress requests can be completed"))

                                                                    self.write()
                                                                    ("state": "completed", "actual_completion_date": fields.Date.today())
                                                                    
                                                                    self.message_post(body=_("Request completed"))

def action_cancel(self):
                                                                        """Cancel the request""",
                                                                        self.ensure_one()
if self.state in ["completed", "cancelled"]:
                                                                            raise UserError(_("Cannot cancel completed or already cancelled requests"))

                                                                            self.write(("state": "cancelled"))
                                                                            self.message_post(body=_("Request cancelled"))

                                                                            @api.model_create_multi
def create(self, vals_list):
                                                                                """Override create to set sequence number""",
for vals in vals_list:
    pass
if vals.get("name", _("New") == _("New"):)
                                                                                        vals["name"] = self.env["ir.sequence"].next_by_code()
                                                                                        "portal.request"
                                                                                        ) or _("New",
                                                                                        return super().create(vals_list)
