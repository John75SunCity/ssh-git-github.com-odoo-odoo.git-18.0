from odoo import models, fields, api

class RecordsBoxMovement(models.Model):
    _name = 'records.box.movement'
    _description = 'Box Movement History'
    _order = 'movement_date desc'

    box_id = fields.Many2one('records.box', string='Box', required=True, ondelete='cascade')
    movement_date = fields.Datetime('Movement Date', required=True, default=fields.Datetime.now)
    from_location_id = fields.Many2one('records.location', string='From Location')
    to_location_id = fields.Many2one('records.location', string='To Location', required=True)
    movement_type = fields.Selection([
        ('storage', 'Initial Storage'),
        ('transfer', 'Transfer'),
        ('retrieval', 'Retrieval'),
        ('return', 'Return'),
        ('relocation', 'Relocation'),
        ('destruction', 'To Destruction')
    ], string='Movement Type', required=True)
    
    responsible_user_id = fields.Many2one('res.users', string='Responsible User', 
                                        default=lambda self: self.env.user, required=True)
    notes = fields.Text('Notes')
    reference = fields.Char('Reference Number')
    
    # Tracking fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    created_on = fields.Datetime('Created On', default=fields.Datetime.now, readonly=True)

class RecordsServiceRequest(models.Model):
    _name = 'records.service.request'
    _description = 'Records Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc'

    name = fields.Char('Request Reference', required=True, default='New')
    box_id = fields.Many2one('records.box', string='Box')
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                domain="[('is_company', '=', True)]", required=True)
    
    service_type = fields.Selection([
        ('retrieval', 'Document Retrieval'),
        ('delivery', 'Document Delivery'),
        ('scanning', 'Document Scanning'),
        ('destruction', 'Document Destruction'),
        ('relocation', 'Box Relocation'),
        ('inventory', 'Inventory Check'),
        ('other', 'Other Service')
    ], string='Service Type', required=True, tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    requested_date = fields.Datetime('Requested Date', required=True, default=fields.Datetime.now)
    required_date = fields.Date('Required Date')
    completed_date = fields.Datetime('Completed Date')
    
    description = fields.Text('Description')
    notes = fields.Text('Internal Notes')
    
    # Assignment
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    
    # Tracking
    requestor_id = fields.Many2one('res.users', string='Requestor', 
                                 default=lambda self: self.env.user, required=True, tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('records.service.request') or 'New'
        return super().create(vals_list)
    
    def action_submit(self):
        self.state = 'submitted'
    
    def action_confirm(self):
        self.state = 'confirmed'
    
    def action_start(self):
        self.state = 'in_progress'
    
    def action_complete(self):
        self.state = 'completed'
        self.completed_date = fields.Datetime.now()
    
    def action_cancel(self):
        self.state = 'cancelled'
