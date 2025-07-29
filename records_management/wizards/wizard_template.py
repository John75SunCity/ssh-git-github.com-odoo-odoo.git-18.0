# -*- coding: utf-8 -*-
"""
Records Management Wizard Template
This is a template for creating new wizards in the Records Management module.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsWizardTemplate(models.TransientModel):
    """
    Template wizard for Records Management operations.
    Copy this template to create new wizards.
    """
    _name = 'records.wizard.template'
    _description = 'Records Management Wizard Template'

    # Basic wizard fields
    name = fields.Char(string='Operation Name', required=True)
    description = fields.Text(string='Description')
    
    # Selection fields for wizard types
    operation_type = fields.Selection([
        ('bulk_update', 'Bulk Update'),
        ('report_generation', 'Report Generation'),
        ('data_import', 'Data Import'),
        ('automated_process', 'Automated Process'),
    ], string='Operation Type', required=True, default='bulk_update')
    
    # Date fields for operations
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    
    # Partner selection for customer-specific operations
    partner_ids = fields.Many2many('res.partner', string='Customers')
    all_customers = fields.Boolean(string='All Customers', default=False)
    
    # Progress tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], string='Status', default='draft')
    
    progress = fields.Float(string='Progress (%)', default=0.0)
    result_message = fields.Html(string='Results')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.date_from and wizard.date_to:
                if wizard.date_from > wizard.date_to:
                    raise ValidationError(_("From Date cannot be after To Date"))

    def action_execute(self):
        """
        Main execution method for the wizard.
        Override this method in specific wizard implementations.
        """
        self.ensure_one()
        
        try:
            self.state = 'running'
            self.progress = 0.0
            
            # Example implementation - replace with actual wizard logic
            self._execute_operation()
            
            self.state = 'done'
            self.progress = 100.0
            self.result_message = _('<p>Operation completed successfully!</p>')
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_state': 'done'}
            }
            
        except Exception as e:
            self.state = 'error'
            self.result_message = _('<p style="color: red;">Error: %s</p>') % str(e)
            raise UserError(_('Operation failed: %s') % str(e))

    def _execute_operation(self):
        """
        Protected method to implement specific wizard logic.
        Override this in concrete wizard implementations.
        """
        # Template implementation
        for i in range(10):
            # Simulate processing steps
            self.progress = (i + 1) * 10
            # Add actual operation logic here
            pass

    def action_reset(self):
        """Reset the wizard to draft state"""
        self.write({
            'state': 'draft',
            'progress': 0.0,
            'result_message': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_close(self):
        """Close the wizard"""
        return {'type': 'ir.actions.act_window_close'}


class RecordsBulkOperationWizard(models.TransientModel):
    """
    Wizard for bulk operations on records.
    This is an example of how to extend the template.
    """
    _name = 'records.bulk.operation.wizard'
    _description = 'Bulk Operations Wizard'
    _inherit = 'records.wizard.template'

    # Additional fields specific to bulk operations
    record_model = fields.Selection([
        ('records.container', 'Records Containers'),
        ('records.document', 'Documents'),
        ('pickup.request', 'Pickup Requests'),
    ], string='Target Model', required=True)
    
    record_ids = fields.Many2many('records.container', string='Selected Records')
    operation = fields.Selection([
        ('update_status', 'Update Status'),
        ('update_location', 'Update Location'),
        ('generate_labels', 'Generate Labels'),
        ('archive', 'Archive Records'),
    ], string='Bulk Operation', required=True)
    
    # Operation-specific fields
    new_status = fields.Char(string='New Status')
    new_location_id = fields.Many2one('records.location', string='New Location')

    def _execute_operation(self):
        """Implement bulk operation logic"""
        if self.operation == 'update_status' and self.new_status:
            # Example: Update status for selected records
            total_records = len(self.record_ids)
            for i, record in enumerate(self.record_ids):
                # Update record status (example)
                # record.status = self.new_status
                self.progress = ((i + 1) / total_records) * 100
                
        elif self.operation == 'update_location' and self.new_location_id:
            # Example: Update location for selected records
            total_records = len(self.record_ids)
            for i, record in enumerate(self.record_ids):
                # Update record location (example)
                # record.location_id = self.new_location_id.id
                self.progress = ((i + 1) / total_records) * 100
