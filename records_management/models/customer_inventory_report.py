from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class CustomerInventoryReport(models.Model):
    _name = 'customer.inventory.report'
    _description = 'Customer Inventory Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'report_date desc, customer_id'

    name = fields.Char(string='Report Name', required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain=[('is_company', '=', True)])
    report_date = fields.Date(
        string='Report Date', default=fields.Date.today, required=True)
    
    # Inventory Summary Fields
    total_boxes = fields.Integer(
        string='Total Boxes', compute='_compute_inventory_totals', store=True)
    total_documents = fields.Integer(
        string='Total Documents', compute='_compute_inventory_totals',
        store=True)
    active_locations = fields.Integer(
        string='Active Locations', compute='_compute_inventory_totals',
        store=True)
    
    # Related Records
    box_ids = fields.One2many(
        'records.box', 'customer_id', string='Customer Boxes', readonly=True)
    document_ids = fields.One2many(
        'records.document', 'customer_id', string='Customer Documents',
        readonly=True)
    
    # Status and Notes
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent to Customer')
    ], default='draft', string='Status')
    notes = fields.Text(string='Notes')
    
    @api.depends('customer_id')
    def _compute_inventory_totals(self):
        for record in self:
            if record.customer_id:
                # Count active boxes for this customer
                record.total_boxes = self.env['records.box'].search_count([
                    ('customer_id', '=', record.customer_id.id),
                    ('state', '!=', 'destroyed')
                ])
                
                # Count documents for this customer
                document_count = self.env['records.document'].search_count([
                    ('customer_id', '=', record.customer_id.id)
                ])
                record.total_documents = document_count
                
                # Count unique locations used by this customer
                locations = self.env['records.box'].search([
                    ('customer_id', '=', record.customer_id.id),
                    ('state', '!=', 'destroyed')
                ]).mapped('location_id')
                record.active_locations = len(locations)
            else:
                record.total_boxes = 0
                record.total_documents = 0
                record.active_locations = 0
    
    def action_confirm_report(self):
        """Confirm the inventory report"""
        self.status = 'confirmed'
    
    def action_send_to_customer(self):
        """Mark report as sent to customer"""
        self.status = 'sent'
    
    @api.model
    def generate_monthly_reports(self):
        """Generate monthly inventory reports for all customers"""
        customers_with_boxes = self.env['records.box'].search([
            ('state', '!=', 'destroyed')
        ]).mapped('customer_id')
        
        today = fields.Date.today()
        report_name = f"Monthly Inventory Report - {today.strftime('%B %Y')}"
        
        for customer in customers_with_boxes:
            # Check if report already exists for this month
            existing_report = self.search([
                ('customer_id', '=', customer.id),
                ('report_date', '>=', today.replace(day=1)),
                ('report_date', '<', (today.replace(day=1) +
                                      relativedelta(months=1)))
            ])
            
            if not existing_report:
                # Create new monthly report
                self.create({
                    'name': f"{report_name} - {customer.name}",
                    'customer_id': customer.id,
                    'report_date': today,
                    'status': 'draft',
                })
        
        return True
    
    def action_generate_pdf_report(self):
        """Generate PDF report for customer inventory"""
        report_ref = 'records_management.action_customer_inventory_report_pdf'
        return self.env.ref(report_ref).report_action(self)
