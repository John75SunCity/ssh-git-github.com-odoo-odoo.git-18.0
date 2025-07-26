# -*- coding: utf-8 -*-
"""
Records Location Inspection Model
Tracks regular inspections of storage locations
"""

from odoo import models, fields, api, _

class RecordsLocationInspection(models.Model):
    """
    Location Inspection Model
    Tracks regular inspections and maintenance of storage locations
    """
    _name = 'records.location.inspection'
    _description = 'Records Location Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc'
    _rec_name = 'name'

    # Basic inspection information
    name = fields.Char(
        string='Inspection Reference',
        required=True,
        default='New'
    
    inspection_date = fields.Date(
        string='Inspection Date',
        default=fields.Date.context_today,
        required=True
    
    inspection_type = fields.Selection([
        ('routine', 'Routine Inspection'),
        ('maintenance', 'Maintenance Inspection'),
        ('emergency', 'Emergency Inspection'),
        ('compliance', 'Compliance Inspection'),
        ('security', 'Security Inspection')
    
    # Related location
    location_id = fields.Many2one(
        'records.location',
        string='Location',
        required=True
    
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        default=lambda self: self.env.user,
        required=True
    
    # Inspection status and results
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    
    result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('needs_attention', 'Needs Attention'),
        ('unsatisfactory', 'Unsatisfactory'),
        ('critical', 'Critical Issues Found')
    
    # Inspection areas
    structural_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    
    environmental_controls = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    
    security_systems = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    
    cleanliness = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    
    organization = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    
    # Detailed findings
    observations = fields.Text(
        string='Observations',
        help='Detailed observations from the inspection'
    
    issues_found = fields.Text(
        string='Issues Found',
        help='List of issues identified during inspection'
    
    recommendations = fields.Text(
        string='Recommendations',
        help='Recommendations for improvement'
    
    corrective_actions = fields.Text(
        string='Corrective Actions Required',
        help='Required corrective actions'
    
    # Follow-up information
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        compute='_compute_follow_up_required',
        store=True
    
    follow_up_date = fields.Date(
        string='Follow-up Date'
    
    next_inspection_date = fields.Date(
        string='Next Inspection Date',
        compute='_compute_next_inspection_date',
        store=True
    
    # Evidence and documentation
    photo_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Photos',
        help='Photos taken during inspection'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('records.location.inspection') or 'LI-' + str(self.env['ir.sequence'].next_by_code('records.location.inspection.simple') or '001')
        return super().create(vals_list)
    
    @api.depends('result')
    def _compute_follow_up_required(self):
        """Determine if follow-up is required based on inspection result"""
        for inspection in self:
            inspection.follow_up_required = inspection.result in ['needs_attention', 'unsatisfactory', 'critical']
    
    @api.depends('inspection_date', 'inspection_type')
    def _compute_next_inspection_date(self):
        """Compute next inspection date based on type and current date"""
        for inspection in self:
            if inspection.inspection_date:
                # Standard inspection intervals
                intervals = {
                    'routine': 30,       # Monthly
                    'maintenance': 90,   # Quarterly
                    'emergency': 7,      # Weekly follow-up
                    'compliance': 180,   # Semi-annually
                    'security': 60       # Bi-monthly
                }
                
                days_to_add = intervals.get(inspection.inspection_type, 30)
                inspection.next_inspection_date = inspection.inspection_date + fields.Date.from_string('1970-01-01').replace(day=days_to_add)
            else:
                inspection.next_inspection_date = False
    
    def action_start_inspection(self):
        """Start the location inspection"""
        self.ensure_one()
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Location inspection started by %s') % self.env.user.name)
    
    def action_complete_inspection(self):
        """Complete the location inspection"""
        self.ensure_one()
        self.write({'status': 'completed'})
        self.message_post(body=_('Location inspection completed by %s') % self.env.user.name)
    
    def action_schedule_follow_up(self):
        """Schedule follow-up inspection"""
        self.ensure_one()
        return {
            'name': _('Schedule Follow-up Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.location.inspection',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_inspection_type': 'routine',
                'default_location_id': self.location_id.id,
                'default_follow_up_date': self.follow_up_date,
            },
        }
    
    def action_view_photos(self):
        """View inspection photos"""
        self.ensure_one()
        return {
            'name': _('Inspection Photos'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.photo_attachment_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }
