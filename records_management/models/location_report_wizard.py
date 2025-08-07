# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class LocationReportWizard(models.Model):
    _name = "location.report.wizard"
    _description = "Location Report Wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Standard message/activity fields
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", auto_join=True
    )        "mail.followers", "res_id", string="Followers", auto_join=True
    )
    action_export_csv = fields.Char(string="Action Export Csv")
    action_generate_report = fields.Char(string="Action Generate Report")
    action_print_report = fields.Char(string="Action Print Report")

    # Report Parameters
    location_id = fields.Many2one(
        "records.location",
        string="Location",
        required=True,
        help="Select the primary location for the report.",
    )
    include_child_locations = fields.Boolean(
        string="Include Child Locations",
        default=True,
        help="Include all sub-locations in the report.",
    )
    report_date = fields.Date(
        string="Report Date",
        default=fields.Date.context_today,
        required=True,
        help="Date for which the report is generated.",
    )

    # Computed Report Data
    location_name = fields.Char(
        related="location_id.name", string="Location Name", store=True, readonly=True
    )
    total_capacity = fields.Float(
        string="Total Capacity",
        compute="_compute_report_data",
        store=True,
        help="Total capacity of the selected location(s).",
    )
    current_utilization = fields.Float(
        string="Current Utilization",
        compute="_compute_report_data",
        store=True,
        help="Current utilization of the location(s).",
    )
    utilization_percentage = fields.Float(
        string="Utilization Percentage",
        compute="_compute_report_data",
        store=True,
        help="Percentage of utilization.",
    )

    @api.depends("location_id", "include_child_locations", "report_date")
    def _compute_report_data(self):
        """Computes the report data based on selected parameters."""
        for wizard in self:
            locations = wizard.location_id
            if wizard.include_child_locations:
                locations |= wizard.location_id.search(
                    [("id", "child_of", wizard.location_id.id)]
                )

            total_capacity = sum(locations.mapped("total_capacity"))
            current_utilization = sum(locations.mapped("current_utilization"))

            wizard.total_capacity = total_capacity
            wizard.current_utilization = current_utilization
            if total_capacity > 0:
                wizard.utilization_percentage = (
                    current_utilization / total_capacity
                ) * 100
            else:
                wizard.utilization_percentage = 0.0

    def action_generate_report(self):
        """Generates the report data."""
        self.ensure_one()
        self._compute_report_data()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_print_report(self):
        """Prints the report."""
        self.ensure_one()
        # This would typically return a QWeb report action
        return self.env.ref(
            "records_management.action_report_location_utilization"
        ).report_action(self)

    def action_export_csv(self):
        """Exports the report data to CSV."""
        self.ensure_one()
        # Implementation for CSV export
        raise UserError(_("CSV export is not yet implemented."))
