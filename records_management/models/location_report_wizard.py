from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LocationReport(models.AbstractModel):
    """
    Abstract model to prepare data for the Location Utilization QWeb report.
    """
    _name = 'report.records_management.report_location_utilization'
    _description = 'Location Utilization Report'
    _inherit = ['mail.thread']

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        This method is called by the Odoo reporting engine to gather the data
        for the PDF report.
        """
        locations = self.env['records.location'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'records.location',
            'docs': locations,
            'data': data,
        }


class LocationReportWizard(models.TransientModel):
    """
    Wizard to generate a report on location utilization.
    """
    _name = 'location.report.wizard'
    _description = 'Location Report Wizard'
    _inherit = ['mail.thread']

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    location_id = fields.Many2one(
        'records.location',
        string='Parent Location',
        help="Select a parent location to report on. Leave empty to report on all root locations."
    )
    include_child_locations = fields.Boolean(
        string='Include Child Locations',
        default=True,
        help="If checked, the report will include all sub-locations of the selected parent."
    )
    report_date = fields.Date(
        string='Report Date',
        default=fields.Date.context_today,
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_print_report(self):
        """
        Gathers the locations based on wizard criteria and triggers the PDF report.
        """
        self.ensure_one()

        domain = [('company_id', '=', self.company_id.id)]
        if self.location_id:
            if self.include_child_locations:
                # Find the selected location and all of its children
                domain.append(('parent_path', '=like', self.location_id.parent_path + '%'))
            else:
                # Only find the selected location
                domain.append(('id', '=', self.location_id.id))

        locations = self.env['records.location'].search(domain)

        if not locations:
            raise UserError(_("No locations found for the selected criteria."))

        # Trigger the QWeb report action
        return self.env.ref('records_management.action_report_location_utilization').report_action(locations)
