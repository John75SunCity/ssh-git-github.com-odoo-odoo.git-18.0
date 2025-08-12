# -*- coding: utf-8 -*-
"""
Records Deletion Request
"""

from odoo import models, fields, api, _

from odoo.exceptions import UserError



class RecordsDeletionRequest(models.Model):
    """
    Records Deletion Request
    """

    _name = "records.deletion.request.enhanced"
    _description = "Records Deletion Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    # Add computed field that uses @api.depends    @api.depends("name", "date", "state")
    def _compute_display_name(self):
        """Compute display name with date and state info"""
        for record in self:
            if record.date:
                record.display_name = (
                    _("%s (%s) - %s", record.name, record.state, record.date.strftime("%Y-%m-%d"))
                )
            else:
                record.display_name = _("%s - %s", record.name, record.state)

    @api.constrains("date")
    def _check_date(self):
        """Validate deletion request date"""
        for record in self:
            if record.date and record.date < fields.Date.today():
                raise UserError(_("Deletion request date cannot be in the past"))

    def action_confirm(self):
        """Confirm the record"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft requests can be confirmed"))
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""

        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed requests can be marked as done"))
        self.write({"state": "done"})

    def name_get(self):
        """Custom name display using computed display_name"""
        result = []
        for record in self:
            name = record.display_name or record.name
            result.append((record.id, name))
        return result
