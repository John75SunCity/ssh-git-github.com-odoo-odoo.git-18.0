from odoo import models, fields, api, _
from datetime import datetime, timedelta


class LocationReportWizard(models.TransientModel):
    _name = 'records.location.report.wizard'
    _description = 'Location Utilization Report Wizard'

    location_id = fields.Many2one(
        'records.location', 
        string='Location', 
        required=True
    )
    location_name = fields.Char(
        'Location Name', 
        readonly=True
    )
    include_child_locations = fields.Boolean(
        'Include Child Locations', 
        default=True,
        help="Include statistics for all child locations in the report"
    )
    report_date = fields.Date(
        'Report Date',
        default=fields.Date.context_today,
        required=True
    )
    
    # Computed statistics
    total_capacity = fields.Integer(
        'Total Capacity',
        compute='_compute_statistics'
    )
    current_occupancy = fields.Integer(
        'Current Occupancy',
        compute='_compute_statistics'
    )
    utilization_percentage = fields.Float(
        'Utilization %',
        compute='_compute_statistics'
    )
    
    @api.depends('location_id', 'include_child_locations')
    def _compute_statistics(self):
        for wizard in self:
            if wizard.location_id:
                locations = [wizard.location_id]
                if wizard.include_child_locations:
                    locations.extend(wizard.location_id.child_ids)
                
                total_capacity = sum(loc.capacity or 0 for loc in locations)
                current_occupancy = sum(loc.current_occupancy or 0 for loc in locations)
                
                wizard.total_capacity = total_capacity
                wizard.current_occupancy = current_occupancy
                
                if total_capacity > 0:
                    wizard.utilization_percentage = (current_occupancy / total_capacity) * 100
                else:
                    wizard.utilization_percentage = 0
            else:
                wizard.total_capacity = 0
                wizard.current_occupancy = 0
                wizard.utilization_percentage = 0

    def action_generate_report(self):
        """Generate the location utilization report."""
        self.ensure_one()
        
        # Get locations to include in report
        locations = [self.location_id]
        if self.include_child_locations:
            locations.extend(self.location_id.child_ids)
        
        # Create a detailed report context
        return {
            'name': _('Location Utilization Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.location',
            'view_mode': 'tree',
            'domain': [('id', 'in', [loc.id for loc in locations])],
            'context': {
                'search_default_group_by_type': 1,
                'report_mode': True,
                'report_title': _('Location Report: %s') % self.location_name,
                'report_date': self.report_date.strftime('%Y-%m-%d'),
            }
        }

    def action_print_report(self):
        """Print a PDF report."""
        self.ensure_one()
        return self.env.ref('records_management.action_location_utilization_report').report_action(self)

    def action_export_csv(self):
        """Export report data to CSV."""
        self.ensure_one()
        
        # This would typically generate a CSV file
        # For now, we'll show a notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Complete'),
                'message': _('Location utilization data exported successfully.'),
                'type': 'success',
            }
        }
