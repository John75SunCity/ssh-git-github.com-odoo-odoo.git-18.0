from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class RecordsTag(models.Model):
    _name = 'records.tag'
    _description = 'Records Management Tag'

    # Define all fields to ensure model is fully registered
    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    # Add this to ensure model is loaded
    @api.model_create_multi
    def create(self, vals_list):
        _logger.info('Creating records.tag with values: %s', vals_list)
        return super().create(vals_list)
        
    def write(self, vals):
        _logger.info('Writing to records.tag with values: %s', vals)
        return super().write(vals)
        
    def _register_hook(self):
        _logger.info('Registering records.tag model hook')
        return super()._register_hook()
