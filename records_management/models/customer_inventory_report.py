from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import timedelta


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


class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Customer Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'company_id, name'

    name = fields.Char(string='Department Name', required=True, tracking=True)
    code = fields.Char(string='Department Code', size=10)
    company_id = fields.Many2one(
        'res.partner', string='Company', required=True,
        domain=[('is_company', '=', True)], tracking=True)
    
    # Department Admin
    admin_id = fields.Many2one(
        'res.partner', string='Department Admin',
        domain="[('parent_id', '=', company_id), ('is_company', '=', False)]")
    
    # Statistics
    total_boxes = fields.Integer(
        string='Total Boxes', compute='_compute_department_stats', store=True)
    total_documents = fields.Integer(
        string='Total Documents', compute='_compute_department_stats', 
        store=True)
    monthly_cost = fields.Float(
        string='Monthly Cost', compute='_compute_department_stats', store=True)
    
    # Users and Access
    user_ids = fields.One2many(
        'records.department.user', 'department_id', string='Department Users')
    active_users_count = fields.Integer(
        string='Active Users', compute='_compute_user_stats')
    
    # Related Records
    box_ids = fields.One2many(
        'records.box', 'department_id', string='Department Boxes')
    document_ids = fields.One2many(
        'records.document', 'department_id', string='Department Documents')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    @api.depends('box_ids', 'box_ids.state', 'document_ids')
    def _compute_department_stats(self):
        for dept in self:
            # Count active boxes
            dept.total_boxes = len(dept.box_ids.filtered(
                lambda x: x.state != 'destroyed'))
            
            # Count documents
            dept.total_documents = len(dept.document_ids)
            
            # Calculate monthly storage cost (placeholder - adjust pricing)
            dept.monthly_cost = dept.total_boxes * 15.0  # $15 per box/month
    
    @api.depends('user_ids', 'user_ids.active')
    def _compute_user_stats(self):
        for dept in self:
            dept.active_users_count = len(dept.user_ids.filtered('active'))
    
    def action_invite_user(self):
        """Open wizard to invite new user to department"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invite User to Department',
            'res_model': 'records.user.invitation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_department_id': self.id}
        }


class RecordsDepartmentUser(models.Model):
    _name = 'records.department.user'
    _description = 'Department User Access'
    _rec_name = 'user_id'

    department_id = fields.Many2one(
        'records.department', string='Department', required=True, 
        ondelete='cascade')
    user_id = fields.Many2one(
        'res.partner', string='User', required=True,
        domain="[('is_company', '=', False)]")
    email = fields.Char(related='user_id.email', readonly=True)
    
    # Access Levels
    access_level = fields.Selection([
        ('viewer', 'Viewer - View Only + Basic Services'),
        ('user', 'User - View + Add/Edit + Request Services'),
        ('dept_admin', 'Department Admin - Full Department Access'),
        ('company_admin', 'Company Admin - Full Company Access')
    ], string='Access Level', required=True, default='viewer')
    
    # Permissions
    can_view_inventory = fields.Boolean(string='View Inventory', default=True)
    can_add_boxes = fields.Boolean(string='Add Boxes/Documents')
    can_request_services = fields.Boolean(string='Request Services',
                                          default=True)
    can_request_deletion = fields.Boolean(string='Request Deletion')
    can_approve_deletion = fields.Boolean(string='Approve Deletion')
    can_view_billing = fields.Boolean(string='View Department Billing')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    invited_date = fields.Datetime(string='Invited Date',
                                   default=fields.Datetime.now)
    last_login = fields.Datetime(string='Last Login')
    
    @api.onchange('access_level')
    def _onchange_access_level(self):
        """Set permissions based on access level"""
        if self.access_level == 'viewer':
            self.can_view_inventory = True
            self.can_add_boxes = False
            self.can_request_services = True  # Basic services only
            self.can_request_deletion = False
            self.can_approve_deletion = False
            self.can_view_billing = False
        elif self.access_level == 'user':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = False
            self.can_view_billing = False
        elif self.access_level == 'dept_admin':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = True  # Can approve for department
            self.can_view_billing = True  # Department billing only
        elif self.access_level == 'company_admin':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = True  # Can approve for company
            self.can_view_billing = True  # Full company billing


class RecordsUserInvitationWizard(models.TransientModel):
    _name = 'records.user.invitation.wizard'
    _description = 'User Invitation Wizard'

    department_id = fields.Many2one(
        'records.department', string='Department', required=True)
    
    # User Information
    name = fields.Char(string='Full Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    job_title = fields.Char(string='Job Title')
    
    # Access Level
    access_level = fields.Selection([
        ('viewer', 'Viewer - View Only'),
        ('user', 'User - View + Request Services'),
        ('admin', 'Admin - Full Department Access')
    ], string='Access Level', required=True, default='viewer')
    
    # Message
    invitation_message = fields.Text(
        string='Invitation Message',
        default="You have been invited to access our Records Management "
                "portal.")
    
    def action_send_invitation(self):
        """Send invitation email and create user"""
        # Create or find the user
        user = self.env['res.partner'].search([
            ('email', '=', self.email),
            ('parent_id', '=', self.department_id.company_id.id)
        ], limit=1)
        
        if not user:
            user = self.env['res.partner'].create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'function': self.job_title,
                'parent_id': self.department_id.company_id.id,
                'is_company': False,
                'customer_rank': 1,
            })
        
        # Create department user record
        self.env['records.department.user'].create({
            'department_id': self.department_id.id,
            'user_id': user.id,
            'access_level': self.access_level,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Invitation sent to {self.email}',
                'type': 'success',
                'sticky': False,
            }
        }


class RecordsServiceRequest(models.Model):
    _name = 'records.service.request'
    _description = 'Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', required=True, copy=False,
                       readonly=True, default=lambda self: 'New')
    
    # Request Details - Enhanced with O'Neil Stratus service types
    service_type = fields.Selection([
        # Access Services
        ('access', 'Access - Retrieve file/folder from container'),
        ('access_box', 'Access - Retrieve entire box'),
        ('access_rush', 'Access - Rush retrieval service'),
        ('access_emergency', 'Access - Emergency retrieval service'),
        
        # Add Services
        ('add', 'Add - Add new container/box to storage'),
        ('add_box', 'Add - New Box Setup'),
        ('add_file', 'Add - Add file/folder to existing container'),
        ('add_pallet', 'Add - Add pallet to storage'),
        
        # Content Validation
        ('content_val', 'Content Validation - Verify container contents'),
        ('content_inventory', 'Content Inventory - Complete container audit'),
        
        # Delivery Services
        ('delivery', 'Delivery - Standard delivery service'),
        ('delivery_rush', 'Delivery - Rush delivery service'),
        ('delivery_same_day', 'Delivery - Same day delivery'),
        ('delivery_emergency', 'Delivery - Emergency delivery'),
        
        # Destruction Services
        ('destroy', 'Destroy - Secure destruction of records'),
        ('destroy_box', 'Destroy - Shred entire box'),
        ('destroy_file', 'Destroy - Shred specific files'),
        ('destroy_hard_drive', 'Destroy - Hard drive destruction'),
        ('destroy_uniform', 'Destroy - Uniform destruction'),
        
        # Imaging Services
        ('image', 'Image - Scan/photograph documents'),
        ('image_box', 'Image - Scan entire box contents'),
        ('image_file', 'Image - Scan specific files'),
        
        # Inventory Services
        ('inventory', 'Inventory - Physical inventory check'),
        ('inventory_full', 'Inventory - Complete facility inventory'),
        ('inventory_partial', 'Inventory - Partial inventory by criteria'),
        
        # Pending Services
        ('pending', 'Pending - Hold for further action'),
        ('pending_approval', 'Pending - Awaiting approval'),
        ('pending_destruction', 'Pending - Scheduled for destruction'),
        
        # Permanent Out
        ('permanent_out', 'Permanent Out - Remove from active storage'),
        ('permanent_checkout', 'Permanent Out - Permanent checkout'),
        
        # Pickup Services
        ('pickup', 'Pickup - Standard pickup service'),
        ('pickup_rush', 'Pickup - Rush pickup service'),
        ('pickup_scheduled', 'Pickup - Scheduled pickup'),
        
        # Pull Services
        ('pull', 'Pull - Remove from storage temporarily'),
        ('pull_box', 'Pull - Remove entire box'),
        ('pull_file', 'Pull - Remove specific files'),
        
        # Receive Services
        ('receive', 'Receive - Process incoming materials'),
        ('receive_box', 'Receive - Process new box'),
        ('receive_pallet', 'Receive - Process pallet'),
        
        # Refile Services
        ('refile', 'Refile - Return items to storage'),
        ('refile_box', 'Refile - Return box to storage'),
        ('refile_file', 'Refile - Return file/folder to container'),
        
        # Storage Services
        ('store_box', 'Storage - Standard box storage'),
        ('store_map', 'Storage - Map box storage'),
        ('store_pallet', 'Storage - Pallet storage'),
        ('store_specialty', 'Storage - Specialty box storage'),
        
        # Transportation Services
        ('transport', 'Transport - General transportation'),
        ('trip_charge', 'Transport - Trip charge'),
        
        # Shred Bin Services
        ('shred_bin_32', 'Shred Bin - 32 Gallon service'),
        ('shred_bin_64', 'Shred Bin - 64 Gallon service'),
        ('shred_bin_96', 'Shred Bin - 96 Gallon service'),
        ('shred_bin_console', 'Shred Bin - Console service'),
        ('shred_bin_mobile_32', 'Shred Bin - 32 Gallon mobile'),
        ('shred_bin_mobile_64', 'Shred Bin - 64 Gallon mobile'),
        ('shred_bin_mobile_96', 'Shred Bin - 96 Gallon mobile'),
        ('shredinator_23', 'Shredinator - 23 Gallon service'),
        
        # One-Time Services
        ('one_time_64g_bin', 'One Time - 64G Bin service'),
        ('one_time_96g_bin', 'One Time - 96G Bin service'),
        
        # Product Sales
        ('sell_boxes', 'Product - New boxes (10 pack) with delivery'),
        ('sell_supplies', 'Product - Office supplies'),
        
        # Special Services
        ('labor', 'Special - Labor service'),
        ('indexing', 'Special - Indexing per box'),
        ('file_not_found', 'Special - File not found research'),
        ('unlock_bin', 'Special - Unlock shred bin'),
        ('key_delivery', 'Special - Key delivery'),
        ('shred_a_thon', 'Special - Shred-A-Thon event'),
        ('damaged_bin', 'Special - Damaged property - bin'),
        
        # Other
        ('other', 'Other - Custom service type')
    ], string='Service Type', required=True, tracking=True)
    
    # Enhanced action codes from O'Neil Stratus
    action_code = fields.Char('Action Code', 
                             help="Action code for billing/tracking")
    object_code = fields.Char('Object Code',
                             help="Object code for billing/tracking")
    
    # Work order vs invoice distinction
    transaction_type = fields.Selection([
        ('workorder', 'Work Order'),
        ('invoice', 'Invoice')
    ], string='Transaction Type', default='workorder', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    # Customer/Department Info
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]", tracking=True)
    department_id = fields.Many2one(
        'records.department', string='Department', tracking=True)
    requested_by = fields.Many2one(
        'res.partner', string='Requested By', required=True, tracking=True)
    
    # Service Details
    description = fields.Html(string='Description', required=True)
    box_ids = fields.Many2many(
        'records.box', string='Related Boxes',
        help="Boxes related to this service request")
    quantity = fields.Integer(string='Quantity', default=1)
    special_instructions = fields.Text(string='Special Instructions')
    
    # Scheduling
    requested_date = fields.Datetime(
        string='Requested Date', default=fields.Datetime.now, tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    completed_date = fields.Datetime(string='Completed Date', tracking=True)
    
    # Status and Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
     # Costs and Billing - Enhanced with O'Neil Stratus features
    estimated_cost = fields.Float(string='Estimated Cost')
    actual_cost = fields.Float(string='Actual Cost')
    
    # Enhanced billing fields from O'Neil Stratus
    base_rate = fields.Float(string='Base Rate',
                             help="Base rate for this service")
    additional_amount = fields.Float(string='Additional Amount',
                                     help="Additional charges")
    discount_rate = fields.Float(string='Discount Rate %',
                                 help="Discount percentage applied")
    discount_amount = fields.Float(string='Discount Amount',
                                   compute='_compute_discount_amount',
                                   store=True)
    
    # Quantity break support
    quantity_break_target = fields.Integer(
        string='Quantity Break Target',
        help="Target qty for quantity break")
    quantity_break_rate = fields.Float(
        string='Quantity Break Rate',
        help="Rate when quantity break achieved")
    
    # Final calculated amounts
    line_total = fields.Float(string='Line Total',
                              compute='_compute_line_total',
                              store=True)
    
    billing_notes = fields.Text(string='Billing Notes')
    
    # Approval
    approved_by = fields.Many2one('res.partner', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    approval_notes = fields.Text(string='Approval Notes')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'records.service.request') or 'New')
        return super().create(vals_list)
    
    def action_submit(self):
        """Submit service request for approval"""
        self.state = 'submitted'
    
    def action_approve(self):
        """Approve service request"""
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.partner_id.id,
            'approval_date': fields.Datetime.now()
        })
    
    def action_schedule(self):
        """Schedule the service"""
        self.state = 'scheduled'
    
    def action_start(self):
        """Start service execution"""
        self.state = 'in_progress'
    
    def action_complete(self):
        """Mark service as completed"""
        self.write({
            'state': 'completed',
            'completed_date': fields.Datetime.now()
        })
    
    def action_cancel(self):
        """Cancel service request"""
        self.state = 'cancelled'


class RecordsDeletionRequest(models.Model):
    _name = 'records.deletion.request'
    _description = 'Deletion Request with Approval Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Deletion Reference', required=True, copy=False,
                       readonly=True, default=lambda self: 'New')
    
    # Request Details
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]", tracking=True)
    department_id = fields.Many2one(
        'records.department', string='Department', required=True,
        tracking=True)
    requested_by = fields.Many2one(
        'res.partner', string='Requested By', required=True, tracking=True)
    
    # Items to Delete
    box_ids = fields.Many2many(
        'records.box', string='Boxes to Delete', required=True)
    document_ids = fields.Many2many(
        'records.document', string='Documents to Delete')
    
    # Justification and Details
    deletion_reason = fields.Selection([
        ('retention_expired', 'Retention Period Expired'),
        ('customer_request', 'Customer Request'),
        ('legal_requirement', 'Legal Requirement'),
        ('space_optimization', 'Space Optimization'),
        ('other', 'Other')
    ], string='Deletion Reason', required=True, tracking=True)
    justification = fields.Html(
        string='Justification', required=True,
        help="Detailed justification for the deletion request")
    
    # Approval Workflow - Requires BOTH department and company admin approval
    dept_admin_approval = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Department Admin Approval', default='pending', tracking=True)
    dept_admin_approved_by = fields.Many2one(
        'res.partner', string='Dept Admin Approved By')
    dept_admin_approval_date = fields.Datetime(
        string='Dept Admin Approval Date')
    dept_admin_signature = fields.Binary(string='Dept Admin Signature')
    dept_admin_notes = fields.Text(string='Department Admin Notes')
    
    company_admin_approval = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Company Admin Approval', default='pending', tracking=True)
    company_admin_approved_by = fields.Many2one(
        'res.partner', string='Company Admin Approved By')
    company_admin_approval_date = fields.Datetime(
        string='Company Admin Approval Date')
    company_admin_signature = fields.Binary(string='Company Admin Signature')
    company_admin_notes = fields.Text(string='Company Admin Notes')
    
    # Overall Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Awaiting Approval'),
        ('dept_approved', 'Department Approved'),
        ('fully_approved', 'Fully Approved'),
        ('rejected', 'Rejected'),
        ('executed', 'Deletion Executed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True,
       compute='_compute_state', store=True)
    
    # Billing and Execution
    deletion_cost = fields.Float(string='Deletion Cost')
    billing_date = fields.Date(string='Billing Date')
    execution_date = fields.Date(string='Execution Date')
    executed_by = fields.Many2one('res.users', string='Executed By')
    execution_notes = fields.Text(string='Execution Notes')
    
    @api.depends('dept_admin_approval', 'company_admin_approval')
    def _compute_state(self):
        for record in self:
            if record.dept_admin_approval == 'rejected' or \
               record.company_admin_approval == 'rejected':
                record.state = 'rejected'
            elif (record.dept_admin_approval == 'approved' and 
                  record.company_admin_approval == 'approved'):
                if record.execution_date:
                    record.state = 'executed'
                else:
                    record.state = 'fully_approved'
            elif record.dept_admin_approval == 'approved':
                record.state = 'dept_approved'
            elif (record.dept_admin_approval == 'pending' and 
                  record.company_admin_approval == 'pending'):
                if record.name != 'New':
                    record.state = 'submitted'
                else:
                    record.state = 'draft'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'records.deletion.request') or 'New')
        return super().create(vals_list)
    
    def action_submit_for_approval(self):
        """Submit deletion request for approval"""
        self.state = 'submitted'
    
    def action_dept_admin_approve(self):
        """Department admin approves deletion"""
        self.write({
            'dept_admin_approval': 'approved',
            'dept_admin_approved_by': self.env.user.partner_id.id,
            'dept_admin_approval_date': fields.Datetime.now()
        })
    
    def action_dept_admin_reject(self):
        """Department admin rejects deletion"""
        self.dept_admin_approval = 'rejected'
    
    def action_company_admin_approve(self):
        """Company admin approves deletion"""
        self.write({
            'company_admin_approval': 'approved',
            'company_admin_approved_by': self.env.user.partner_id.id,
            'company_admin_approval_date': fields.Datetime.now()
        })
    
    def action_company_admin_reject(self):
        """Company admin rejects deletion"""
        self.company_admin_approval = 'rejected'
    
    def action_execute_deletion(self):
        """Execute the approved deletion and bill immediately"""
        if self.state != 'fully_approved':
            raise ValidationError(
                "Deletion can only be executed after full approval")
        
        # Mark boxes as destroyed
        self.box_ids.write({
            'state': 'destroyed',
            'destruction_date': fields.Date.today()
        })
        
        # Mark documents as destroyed
        self.document_ids.write({'state': 'destroyed'})
        
        # Update deletion record
        self.write({
            'execution_date': fields.Date.today(),
            'executed_by': self.env.user.id,
            'billing_date': fields.Date.today(),
            'state': 'executed'
        })
        
        # TODO: Trigger billing process here
        return True


class RecordsBulkUserImport(models.TransientModel):
    _name = 'records.bulk.user.import'
    _description = 'Bulk User Import Wizard'

    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]")
    department_id = fields.Many2one(
        'records.department', string='Department',
        help="Leave empty to assign users to company level")
    
    # CSV Upload
    csv_file = fields.Binary(string='CSV File', required=True)
    csv_filename = fields.Char(string='Filename')
    
    # Default Settings
    default_access_level = fields.Selection([
        ('viewer', 'Viewer - View Only + Basic Services'),
        ('user', 'User - View + Add/Edit + Request Services'),
        ('dept_admin', 'Department Admin - Full Department Access'),
        ('company_admin', 'Company Admin - Full Company Access')
    ], string='Default Access Level', default='viewer')
    
    # Preview and Results
    preview_data = fields.Text(string='Preview Data', readonly=True)
    import_results = fields.Text(string='Import Results', readonly=True)
    
    def action_preview_import(self):
        """Preview the CSV data before importing"""
        # TODO: Implement CSV parsing and preview
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'records.bulk.user.import',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_import_users(self):
        """Import users from CSV file"""
        # TODO: Implement actual CSV import logic
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Users imported successfully',
                'type': 'success',
                'sticky': False,
            }
        }


class RecordsBillingConfig(models.Model):
    _name = 'records.billing.config'
    _description = 'Billing Configuration for Records Management'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    
    # Storage Pricing (Monthly Recurring)
    storage_rate_per_box = fields.Float(
        string='Box Storage Rate (Monthly)',
        default=0.32, digits=(12, 4),
        help="Monthly storage fee per standard box")
    map_box_storage_rate = fields.Float(
        string='Map Box Storage Rate (Monthly)',
        default=0.45, digits=(12, 4),
        help="Monthly storage fee per map box")
    pallet_storage_rate = fields.Float(
        string='Pallet Storage Rate (Monthly)', 
        default=2.50, digits=(12, 4),
        help="Monthly storage fee per pallet")
    specialty_box_storage_rate = fields.Float(
        string='Specialty Box Storage Rate (Monthly)',
        default=0.50, digits=(12, 4),
        help="Monthly storage fee per specialty box")
    monthly_minimum_fee = fields.Float(
        string='Monthly Minimum Storage Fee',
        default=45.00, digits=(12, 2),
        help="Minimum monthly storage charge")
    
    # Transportation & Delivery
    pickup_base_fee = fields.Float(
        string='Pickup Base Fee', default=25.00, digits=(12, 2))
    delivery_base_fee = fields.Float(
        string='Delivery Base Fee', default=25.00, digits=(12, 2))
    trip_charge = fields.Float(
        string='Trip Charge', default=15.00, digits=(12, 2))
    transportation_rate_per_mile = fields.Float(
        string='Transportation Rate per Mile', default=0.75, digits=(12, 2))
    
    # Box Management Services
    new_box_fee = fields.Float(
        string='New Box Setup Fee', default=2.50, digits=(12, 2))
    refile_box_fee = fields.Float(
        string='Refile Box Fee', default=3.00, digits=(12, 2))
    refile_filefolder_fee = fields.Float(
        string='Refile File/Folder Fee', default=1.50, digits=(12, 2))
    permanent_removal_fee = fields.Float(
        string='Permanent Removal Fee', default=2.00, digits=(12, 2))
    
    # Destruction Services
    shredding_per_box_fee = fields.Float(
        string='Shredding per Box Fee', default=3.50, digits=(12, 2))
    hard_drive_destruction_fee = fields.Float(
        string='Hard Drive Destruction Fee', default=15.00, digits=(12, 2))
    uniform_destruction_fee = fields.Float(
        string='Uniform Destruction Fee', default=25.00, digits=(12, 2))
    
    # Retrieval Services - Regular
    regular_retrieval_box_fee = fields.Float(
        string='Regular Retrieval - Box', default=8.50, digits=(12, 2))
    regular_retrieval_file_fee = fields.Float(
        string='Regular Retrieval - File', default=3.50, digits=(12, 2))
    
    # Retrieval Services - Rush (4 hour)
    rush_retrieval_box_fee = fields.Float(
        string='Rush Retrieval - Box (4hr)', default=15.00, digits=(12, 2))
    rush_retrieval_file_fee = fields.Float(
        string='Rush Retrieval - File (4hr)', default=8.50, digits=(12, 2))
    rush_service_4hr_fee = fields.Float(
        string='Rush Service 4HR Fee', default=25.00, digits=(12, 2))
    
    # Retrieval Services - Emergency (1 hour)
    emergency_retrieval_box_fee = fields.Float(
        string='Emergency Retrieval - Box (1hr)', default=25.00, digits=(12, 2))
    emergency_retrieval_file_fee = fields.Float(
        string='Emergency Retrieval - File (1hr)', default=15.00, digits=(12, 2))
    emergency_service_1hr_fee = fields.Float(
        string='Emergency Service 1HR Fee', default=50.00, digits=(12, 2))
    same_day_service_fee = fields.Float(
        string='Same Day Service Fee', default=35.00, digits=(12, 2))
    
    # Shred Bin Services - Container Sizes
    shred_bin_32_gallon_fee = fields.Float(
        string='32 Gallon Bin Service', default=25.00, digits=(12, 2))
    shred_bin_64_gallon_fee = fields.Float(
        string='64 Gallon Bin Service', default=35.00, digits=(12, 2))
    shred_bin_96_gallon_fee = fields.Float(
        string='96 Gallon Bin Service', default=45.00, digits=(12, 2))
    shred_bin_console_fee = fields.Float(
        string='Shred Console Service', default=30.00, digits=(12, 2))
    shred_bin_mobile_fee = fields.Float(
        string='Mobile Bin Service', default=40.00, digits=(12, 2))
    shredinator_23_gallon_fee = fields.Float(
        string='23 Gallon Shredinator', default=20.00, digits=(12, 2))
    
    # Shred Box Services
    shred_box_standard_fee = fields.Float(
        string='Shred Box - Standard Size', default=15.00, digits=(12, 2))
    shred_box_double_fee = fields.Float(
        string='Shred Box - Double Size', default=25.00, digits=(12, 2))
    shred_box_large_fee = fields.Float(
        string='Shred Box - Odd/Large', default=35.00, digits=(12, 2))
    
    # One-Time Bin Services
    one_time_64g_bin_fee = fields.Float(
        string='One Time 64G Bin Service', default=45.00, digits=(12, 2))
    one_time_96g_bin_fee = fields.Float(
        string='One Time 96G Bin Service', default=55.00, digits=(12, 2))
    
    # Special Services
    labor_hourly_rate = fields.Float(
        string='Labor Hourly Rate', default=35.00, digits=(12, 2))
    indexing_per_box_fee = fields.Float(
        string='Indexing per Box Fee', default=12.50, digits=(12, 2))
    file_not_found_fee = fields.Float(
        string='File Not Found Fee', default=5.00, digits=(12, 2))
    unlock_shred_bin_fee = fields.Float(
        string='Unlock Shred Bin Fee', default=15.00, digits=(12, 2))
    key_delivery_fee = fields.Float(
        string='Key Delivery Fee', default=10.00, digits=(12, 2))
    shred_a_thon_fee = fields.Float(
        string='Shred-A-Thon Fee', default=250.00, digits=(12, 2))
    damaged_property_bin_fee = fields.Float(
        string='Damaged Property - Bin Fee', default=75.00, digits=(12, 2))
    
    # Product Sales
    file_box_10_pack_price = fields.Float(
        string='File Box 10-Pack Price (with delivery)', default=45.00, digits=(12, 2))
    
    active = fields.Boolean(string='Active', default=True)


class RecordsBillingPeriod(models.Model):
    _name = 'records.billing.period'
    _description = 'Monthly Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'period_start desc'

    name = fields.Char(string='Period Name', required=True)
    period_start = fields.Date(string='Period Start', required=True)
    period_end = fields.Date(string='Period End', required=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculating', 'Calculating'),
        ('ready', 'Ready for Review'),
        ('approved', 'Approved'),
        ('invoiced', 'Invoiced'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)
    
    # Billing Lines
    billing_line_ids = fields.One2many(
        'records.billing.line', 'billing_period_id',
        string='Billing Lines')
    
    # Totals
    total_storage_boxes = fields.Integer(
        string='Total Storage Boxes', compute='_compute_totals', store=True)
    total_storage_amount = fields.Float(
        string='Total Storage Amount', compute='_compute_totals', store=True)
    total_services_amount = fields.Float(
        string='Total Services Amount', compute='_compute_totals', store=True)
    total_products_amount = fields.Float(
        string='Total Products Amount', compute='_compute_totals', store=True)
    total_amount = fields.Float(
        string='Total Amount', compute='_compute_totals', store=True)
    
    # Invoice Integration
    invoice_ids = fields.One2many(
        'account.move', 'billing_period_id', string='Generated Invoices')
    invoice_count = fields.Integer(
        string='Invoice Count', compute='_compute_invoice_count')
    
    @api.depends('billing_line_ids', 'billing_line_ids.amount')
    def _compute_totals(self):
        for period in self:
            storage_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'storage')
            service_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'service')
            product_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'product')
            
            period.total_storage_boxes = sum(storage_lines.mapped('quantity'))
            period.total_storage_amount = sum(storage_lines.mapped('amount'))
            period.total_services_amount = sum(service_lines.mapped('amount'))
            period.total_products_amount = sum(product_lines.mapped('amount'))
            period.total_amount = (period.total_storage_amount + 
                                   period.total_services_amount + 
                                   period.total_products_amount)
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for period in self:
            period.invoice_count = len(period.invoice_ids)
    
    def action_calculate_billing(self):
        """Calculate billing for all customers for this period"""
        self.ensure_one()
        self.state = 'calculating'
        
        # Clear existing billing lines
        self.billing_line_ids.unlink()
        
        billing_config = self.env['records.billing.config'].search([
            ('active', '=', True)
        ], limit=1)
        
        if not billing_config:
            raise ValidationError("No active billing configuration found.")
        
        # Get all customers with boxes during this period
        customers_with_boxes = self.env['records.box'].search([
            ('customer_id', '!=', False),
            ('state', '!=', 'destroyed')
        ]).mapped('customer_id')
        
        for customer in customers_with_boxes:
            self._calculate_customer_billing(customer, billing_config)
        
        # Calculate service billing
        self._calculate_service_billing(billing_config)
        
        self.state = 'ready'
    
    def _calculate_customer_billing(self, customer, config):
        """Calculate storage billing for a specific customer"""
        # Count different types of storage containers for this customer
        boxes = self.env['records.box'].search([
            ('customer_id', '=', customer.id),
            ('state', '!=', 'destroyed'),
        ])
        
        # Group boxes by department for department-level billing
        departments = boxes.mapped('department_id')
        if not departments:
            # Customer has no departments, bill at company level
            self._calculate_company_level_billing(customer, boxes, config)
        else:
            # Customer has departments, calculate billing per department
            self._calculate_department_level_billing(customer, departments, config)
    
    def _calculate_company_level_billing(self, customer, boxes, config):
        """Calculate billing for company without departments"""
        # Group boxes by storage type (you may need to add storage_type field to records.box)
        storage_types = {
            'standard': boxes.filtered(lambda b: not hasattr(b, 'storage_type') or b.storage_type == 'standard'),
            'map': boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'map'),
            'specialty': boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'specialty'),
        }
        
        # Count pallets (you may need to add pallet tracking)
        pallet_count = 0  # TODO: Implement pallet counting logic
        
        total_storage_cost = 0.0
        billing_lines = []
        
        # Calculate storage for each type
        for storage_type, box_list in storage_types.items():
            if not box_list:
                continue
                
            box_count = len(box_list)
            if storage_type == 'standard':
                rate = config.storage_rate_per_box
                description = f'Storage for {box_count} standard boxes'
            elif storage_type == 'map':
                rate = config.map_box_storage_rate
                description = f'Storage for {box_count} map boxes'
            elif storage_type == 'specialty':
                rate = config.specialty_box_storage_rate
                description = f'Storage for {box_count} specialty boxes'
            
            storage_amount = box_count * rate
            total_storage_cost += storage_amount
            
            # Create billing line for this storage type
            billing_lines.append({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': description,
                'quantity': box_count,
                'unit_price': rate,
                'amount': storage_amount,
            })
        
        # Add pallet storage if any
        if pallet_count > 0:
            pallet_amount = pallet_count * config.pallet_storage_rate
            total_storage_cost += pallet_amount
            billing_lines.append({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': f'Pallet storage for {pallet_count} pallets',
                'quantity': pallet_count,
                'unit_price': config.pallet_storage_rate,
                'amount': pallet_amount,
            })
        
        # Create all storage billing lines
        for line_data in billing_lines:
            self.env['records.billing.line'].create(line_data)
        
        # Check if monthly minimum applies
        if total_storage_cost > 0 and total_storage_cost < config.monthly_minimum_fee:
            minimum_adjustment = config.monthly_minimum_fee - total_storage_cost
            self.env['records.billing.line'].create({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': 'Monthly Storage Minimum Fee',
                'quantity': 1,
                'unit_price': minimum_adjustment,
                'amount': minimum_adjustment,
            })
            
        return True
    
    def _calculate_department_level_billing(self, customer, departments, config):
        """Calculate billing broken down by department"""
        customer_total = 0.0
        department_totals = {}
        
        for department in departments:
            dept_boxes = self.env['records.box'].search([
                ('customer_id', '=', customer.id),
                ('department_id', '=', department.id),
                ('state', '!=', 'destroyed'),
            ])
            
            # Group boxes by storage type for this department
            storage_types = {
                'standard': dept_boxes.filtered(lambda b: not hasattr(b, 'storage_type') or b.storage_type == 'standard'),
                'map': dept_boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'map'),
                'specialty': dept_boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'specialty'),
            }
            
            dept_total = 0.0
            
            # Calculate storage for each type in this department
            for storage_type, box_list in storage_types.items():
                if not box_list:
                    continue
                    
                box_count = len(box_list)
                if storage_type == 'standard':
                    rate = config.storage_rate_per_box
                    description = f'{department.name} - Storage for {box_count} standard boxes'
                elif storage_type == 'map':
                    rate = config.map_box_storage_rate
                    description = f'{department.name} - Storage for {box_count} map boxes'
                elif storage_type == 'specialty':
                    rate = config.specialty_box_storage_rate
                    description = f'{department.name} - Storage for {box_count} specialty boxes'
                
                storage_amount = box_count * rate
                dept_total += storage_amount
                
                # Create billing line for this department's storage
                self.env['records.billing.line'].create({
                    'billing_period_id': self.id,
                    'customer_id': customer.id,
                    'department_id': department.id,
                    'line_type': 'storage',
                    'description': description,
                    'quantity': box_count,
                    'unit_price': rate,
                    'amount': storage_amount,
                })
            
            department_totals[department.id] = dept_total
            customer_total += dept_total
        
        # Handle minimum fee logic - check customer's billing preference
        billing_preference = customer.billing_preference or 'consolidated'
        minimum_fee_per_dept = customer.minimum_fee_per_department or False
        
        if minimum_fee_per_dept:
            # Apply minimum fee per department
            for department in departments:
                dept_total = department_totals.get(department.id, 0.0)
                if dept_total > 0 and dept_total < config.monthly_minimum_fee:
                    minimum_adjustment = config.monthly_minimum_fee - dept_total
                    self.env['records.billing.line'].create({
                        'billing_period_id': self.id,
                        'customer_id': customer.id,
                        'department_id': department.id,
                        'line_type': 'storage',
                        'description': f'{department.name} - Monthly Storage Minimum Fee',
                        'quantity': 1,
                        'unit_price': minimum_adjustment,
                        'amount': minimum_adjustment,
                    })
        else:
            # Apply minimum fee at company level, distribute proportionally
            if customer_total > 0 and customer_total < config.monthly_minimum_fee:
                minimum_adjustment = config.monthly_minimum_fee - customer_total
                
                # Distribute minimum fee proportionally across departments
                for department in departments:
                    dept_total = department_totals.get(department.id, 0.0)
                    if dept_total > 0:
                        dept_proportion = dept_total / customer_total
                        dept_minimum = minimum_adjustment * dept_proportion
                        
                        self.env['records.billing.line'].create({
                            'billing_period_id': self.id,
                            'customer_id': customer.id,
                            'department_id': department.id,
                            'line_type': 'storage',
                            'description': f'{department.name} - Monthly Minimum Fee (Proportional)',
                            'quantity': 1,
                            'unit_price': dept_minimum,
                            'amount': dept_minimum,
                        })
        
        return True
    
    def _calculate_service_billing(self, config):
        """Calculate billing for services completed during this period"""
        # Get completed service requests during this period
        service_requests = self.env['records.service.request'].search([
            ('state', '=', 'completed'),
            ('completion_date', '>=', self.period_start),
            ('completion_date', '<=', self.period_end),
        ])
        
        for service in service_requests:
            if service.actual_cost > 0:
                self.env['records.billing.line'].create({
                    'billing_period_id': self.id,
                    'customer_id': service.customer_id.id,
                    'service_request_id': service.id,
                    'line_type': 'service',
                    'description': service.name,
                    'quantity': 1,
                    'unit_price': service.actual_cost,
                    'amount': service.actual_cost,
                })
    
    def action_generate_invoices(self):
        """Generate invoices based on customer billing preferences"""
        if self.state != 'approved':
            raise UserError("Only approved billing periods can generate invoices")
        
        # Get all customers with billing lines
        customers = self.billing_line_ids.mapped('customer_id')
        
        for customer in customers:
            self._generate_customer_invoices(customer)
        
        self.state = 'invoiced'
        return True
    
    def _generate_customer_invoices(self, customer):
        """Generate invoices for a customer based on their billing preference"""
        billing_preference = customer.billing_preference or 'consolidated'
        customer_lines = self.billing_line_ids.filtered(
            lambda l: l.customer_id.id == customer.id)
        
        if billing_preference == 'consolidated':
            self._generate_consolidated_invoice(customer, customer_lines)
        elif billing_preference == 'separate':
            self._generate_separate_invoices(customer, customer_lines)
        elif billing_preference == 'hybrid':
            self._generate_hybrid_invoices(customer, customer_lines)
    
    def _generate_consolidated_invoice(self, customer, billing_lines):
        """Generate one invoice with department breakdown"""
        if not billing_lines:
            return
        
        # Create invoice header
        invoice_vals = {
            'partner_id': customer.id,
            'move_type': 'out_invoice',
            'invoice_date': self.period_end,
            'billing_period_id': self.id,
            'narration': f'Records Management Services for {self.name}',
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Group lines by department for better organization
        departments = billing_lines.mapped('department_id')
        
        if departments:
            # Customer has departments - group by department
            for department in departments:
                dept_lines = billing_lines.filtered(
                    lambda l: l.department_id.id == department.id)
                if dept_lines:
                    self._add_department_section_to_invoice(
                        invoice, department, dept_lines)
            
            # Add lines without department (company-level charges)
            company_lines = billing_lines.filtered(lambda l: not l.department_id)
            if company_lines:
                self._add_department_section_to_invoice(
                    invoice, None, company_lines)
        else:
            # Customer has no departments - add all lines directly
            self._add_billing_lines_to_invoice(invoice, billing_lines)
        
        # Finalize the invoice
        invoice.action_post()
        return invoice
    
    def _generate_separate_invoices(self, customer, billing_lines):
        """Generate separate invoices per department"""
        departments = billing_lines.mapped('department_id')
        invoices = []
        
        for department in departments:
            dept_lines = billing_lines.filtered(
                lambda l: l.department_id.id == department.id)
            if not dept_lines:
                continue
            
            # Get department billing contact if configured
            dept_billing = customer.department_billing_contact_ids.filtered(
                lambda dbc: dbc.department_id.id == department.id)
            
            billing_partner = (dept_billing.billing_contact_id.id 
                             if dept_billing else customer.id)
            
            # Create separate invoice for this department
            invoice_vals = {
                'partner_id': billing_partner,
                'move_type': 'out_invoice',
                'invoice_date': self.period_end,
                'billing_period_id': self.id,
                'narration': f'Records Management Services for '
                           f'{department.name} - {self.name}',
            }
            
            # Add PO number if configured
            if dept_billing and dept_billing.default_po_number:
                invoice_vals['ref'] = dept_billing.default_po_number
            
            invoice = self.env['account.move'].create(invoice_vals)
            self._add_billing_lines_to_invoice(invoice, dept_lines)
            invoice.action_post()
            invoices.append(invoice)
        
        # Handle company-level charges (lines without department)
        company_lines = billing_lines.filtered(lambda l: not l.department_id)
        if company_lines:
            invoice_vals = {
                'partner_id': customer.id,
                'move_type': 'out_invoice',
                'invoice_date': self.period_end,
                'billing_period_id': self.id,
                'narration': f'Records Management Services (Company) - '
                           f'{self.name}',
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            self._add_billing_lines_to_invoice(invoice, company_lines)
            invoice.action_post()
            invoices.append(invoice)
        
        return invoices
    
    def _generate_hybrid_invoices(self, customer, billing_lines):
        """Generate consolidated storage, separate service invoices"""
        storage_lines = billing_lines.filtered(
            lambda l: l.line_type == 'storage')
        service_lines = billing_lines.filtered(
            lambda l: l.line_type in ['service', 'product'])
        
        invoices = []
        
        # Consolidated storage invoice
        if storage_lines:
            invoices.append(
                self._generate_consolidated_invoice(customer, storage_lines))
        
        # Separate service invoices by department
        if service_lines:
            invoices.extend(
                self._generate_separate_invoices(customer, service_lines))
        
        return invoices
    
    def _add_department_section_to_invoice(self, invoice, department, lines):
        """Add a department section with subtotal to invoice"""
        if department:
            # Add department header as a display line
            self.env['account.move.line'].create({
                'move_id': invoice.id,
                'name': f'\n=== {department.name} ===',
                'display_type': 'line_section',
            })
        
        # Add the actual billing lines
        self._add_billing_lines_to_invoice(invoice, lines)
        
        # Add department subtotal if there are multiple departments
        if department and len(lines.mapped('department_id')) > 1:
            dept_total = sum(lines.mapped('amount'))
            self.env['account.move.line'].create({
                'move_id': invoice.id,
                'name': f'{department.name} Subtotal: ${dept_total:,.2f}',
                'display_type': 'line_note',
            })
    
    def _add_billing_lines_to_invoice(self, invoice, billing_lines):
        """Add billing lines to invoice as invoice lines"""
        # Get default product and account (you may need to configure these)
        default_product = self.env['product.product'].search([
            ('name', '=', 'Records Management Services')], limit=1)
        
        if not default_product:
            # Create default product if it doesn't exist
            default_product = self.env['product.product'].create({
                'name': 'Records Management Services',
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
            })
        
        for line in billing_lines:
            invoice_line_vals = {
                'move_id': invoice.id,
                'product_id': default_product.id,
                'name': line.description,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': default_product.property_account_income_id.id or
                            default_product.categ_id.property_account_income_categ_id.id,
            }
            
            self.env['account.move.line'].create(invoice_line_vals)
        

class RecordsBillingLine(models.Model):
    _name = 'records.billing.line'
    _description = 'Billing Line Item'
    _rec_name = 'description'

    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period', 
        required=True, ondelete='cascade')
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True)
    department_id = fields.Many2one(
        'records.department', string='Department')
    service_request_id = fields.Many2one(
        'records.service.request', string='Service Request')
    
    line_type = fields.Selection([
        ('storage', 'Storage Fee'),
        ('service', 'Service Fee'),
        ('product', 'Product Sale'),
        ('adjustment', 'Adjustment')
    ], string='Line Type', required=True)
    
    description = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, digits=(12, 2))
    unit_price = fields.Float(string='Unit Price', digits=(12, 4))
    amount = fields.Float(
        string='Amount', compute='_compute_amount', store=True, 
        digits=(12, 2))
    
    # Additional Information
    notes = fields.Text(string='Notes')
    
    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price


class RecordsServicePricing(models.Model):
    _name = 'records.service.pricing'
    _description = 'Comprehensive Service Pricing Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Service Name', required=True)
    service_code = fields.Char(string='Service Code', required=True)
    action_code = fields.Char(string='Action Code', help="STORE, SELL, ADD, etc.")
    object_code = fields.Char(string='Object Code', help="01, BX, CONTAINER, etc.")
    
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('product', 'Product Sales'),
        ('box_management', 'Box Management'),
        ('transportation', 'Transportation & Delivery'),
        ('destruction', 'Destruction Services'),
        ('retrieval', 'Retrieval Services'),
        ('shred_bin', 'Shred Bin Services'),
        ('special', 'Special Services')
    ], string='Service Category', required=True)
    
    # Pricing
    base_price = fields.Float(string='Base Price', digits=(12, 2))
    per_unit_price = fields.Float(
        string='Per Unit Price', digits=(12, 4),
        help="Additional cost per unit/box/mile etc.")
    minimum_charge = fields.Float(
        string='Minimum Charge', digits=(12, 2))
    
    # Billing Type
    billing_type = fields.Selection([
        ('invoice', 'Direct Invoice'),
        ('workorder', 'Workorder Required'),
        ('recurring', 'Recurring Monthly')
    ], string='Billing Type', default='invoice')
    
    requires_approval = fields.Boolean(string='Requires Approval', default=False)
    accumulate = fields.Boolean(string='Accumulate Charges', default=False)
    
    # Quantity Breaks
    quantity_breaks = fields.One2many(
        'records.service.pricing.break', 'pricing_id', 
        string='Quantity Breaks')
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class RecordsServicePricingBreak(models.Model):
    _name = 'records.service.pricing.break'
    _description = 'Service Pricing Quantity Breaks'
    _rec_name = 'min_quantity'

    pricing_id = fields.Many2one(
        'records.service.pricing', string='Pricing', 
        required=True, ondelete='cascade')
    min_quantity = fields.Float(string='Minimum Quantity', required=True)
    max_quantity = fields.Float(string='Maximum Quantity')
    unit_price = fields.Float(string='Unit Price', digits=(12, 4))
    discount_percent = fields.Float(string='Discount %', digits=(5, 2))


# Add billing period reference to account.move (invoices)
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period',
        help="The billing period this invoice was generated from")


# Enhanced the existing RecordsServiceRequest model
class RecordsServiceRequestEnhanced(models.Model):
    _inherit = 'records.service.request'

    # Enhanced pricing fields
    actual_cost = fields.Float(
        string='Actual Cost', digits=(12, 2),
        help="Final billed amount for this service")
    cost_breakdown = fields.Text(
        string='Cost Breakdown',
        help="Detailed breakdown of how the cost was calculated")
    
    # Billing integration
    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period')
    billing_line_id = fields.Many2one(
        'records.billing.line', string='Billing Line')
    invoiced = fields.Boolean(string='Invoiced', default=False)
    completion_date = fields.Datetime(string='Completion Date')
    
    # Additional service details for pricing
    distance_miles = fields.Float(
        string='Distance (Miles)', digits=(8, 2),
        help="Distance for transportation cost calculation")
    boxes_count = fields.Integer(
        string='Number of Boxes', default=1)
    hard_drives_count = fields.Integer(
        string='Number of Hard Drives', default=0)

    @api.depends('base_rate', 'discount_rate', 'quantity')
    def _compute_discount_amount(self):
        """Calculate discount amount based on base rate and discount rate"""
        for record in self:
            if record.base_rate and record.discount_rate:
                record.discount_amount = (
                    record.base_rate * record.quantity *
                    (record.discount_rate / 100))
            else:
                record.discount_amount = 0.0
    
    @api.depends('base_rate', 'quantity', 'discount_amount',
                 'additional_amount', 'quantity_break_target',
                 'quantity_break_rate')
    def _compute_line_total(self):
        """Calculate line total with quantity breaks and discounts"""
        for record in self:
            # Determine rate (base or quantity break)
            rate = record.base_rate
            if (record.quantity_break_target and record.quantity_break_rate and
                    record.quantity >= record.quantity_break_target):
                rate = record.quantity_break_rate
            
            # Calculate subtotal
            subtotal = rate * record.quantity
            
            # Apply discount and add additional charges
            total = subtotal - record.discount_amount + record.additional_amount
            record.line_total = max(0, total)  # Ensure non-negative


class RecordsBarcodeConfig(models.Model):
    _name = 'records.barcode.config'
    _description = 'Barcode Configuration'
    _rec_name = 'barcode_type'
    _order = 'barcode_type'

    barcode_type = fields.Selection([
        ('box', 'Box Barcode'),
        ('document', 'Document Barcode'),
        ('location', 'Location Barcode'),
        ('pallet', 'Pallet Barcode'),
        ('bin', 'Bin Barcode'),
        ('other', 'Other')
    ], string='Barcode Type', required=True)
    
    # Barcode format configuration
    barcode_format = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('ean8', 'EAN-8'),
        ('qr', 'QR Code'),
        ('datamatrix', 'Data Matrix'),
        ('other', 'Other')
    ], string='Barcode Format', default='code128', required=True)
    
    # Length configuration
    min_length = fields.Integer(string='Minimum Length', default=6)
    max_length = fields.Integer(string='Maximum Length', default=20)
    fixed_length = fields.Boolean(string='Fixed Length', default=False,
                                  help="Enforce exact length")
    exact_length = fields.Integer(string='Exact Length', default=12,
                                  help="Required length when fixed length enabled")
    
    # Prefix/suffix configuration
    prefix = fields.Char(string='Prefix', size=10,
                         help="Fixed prefix for barcodes")
    suffix = fields.Char(string='Suffix', size=10,
                         help="Fixed suffix for barcodes")
    
    # Validation rules
    allow_letters = fields.Boolean(string='Allow Letters', default=True)
    allow_numbers = fields.Boolean(string='Allow Numbers', default=True)
    allow_special = fields.Boolean(string='Allow Special Characters',
                                   default=False)
    special_chars = fields.Char(string='Allowed Special Characters', size=20,
                               help="Specific special characters allowed")
    
    # Check digit configuration
    use_check_digit = fields.Boolean(string='Use Check Digit', default=False)
    check_digit_algorithm = fields.Selection([
        ('mod10', 'Modulo 10'),
        ('mod11', 'Modulo 11'),
        ('mod43', 'Modulo 43'),
        ('custom', 'Custom Algorithm')
    ], string='Check Digit Algorithm', default='mod10')
    
    # Usage settings
    active = fields.Boolean(string='Active', default=True)
    auto_generate = fields.Boolean(string='Auto Generate', default=False,
                                   help="Automatically generate barcodes")
    sequence_id = fields.Many2one('ir.sequence', string='Sequence',
                                  help="Sequence for auto-generated barcodes")
    
    # Description and notes
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    
    @api.constrains('min_length', 'max_length', 'exact_length')
    def _check_length_constraints(self):
        """Validate length constraints"""
        for config in self:
            if config.min_length <= 0:
                raise ValidationError(_("Minimum length must be > 0"))
            if config.max_length <= 0:
                raise ValidationError(_("Maximum length must be > 0"))
            if config.min_length > config.max_length:
                raise ValidationError(
                    _("Minimum length cannot be greater than maximum length"))
            if config.fixed_length and config.exact_length <= 0:
                raise ValidationError(
                    _("Exact length must be > 0 when fixed length enabled"))
            if (config.fixed_length and 
                (config.exact_length < config.min_length or 
                 config.exact_length > config.max_length)):
                raise ValidationError(
                    _("Exact length must be between minimum and maximum"))
    
    @api.constrains('allow_letters', 'allow_numbers')
    def _check_character_types(self):
        """Ensure at least one character type is allowed"""
        for config in self:
            if not config.allow_letters and not config.allow_numbers:
                raise ValidationError(
                    _("At least letters or numbers must be allowed"))
    
    def validate_barcode(self, barcode):
        """Validate a barcode against this configuration"""
        if not barcode:
            return False, _("Barcode cannot be empty")
        
        # Check length
        if self.fixed_length:
            if len(barcode) != self.exact_length:
                return False, _("Barcode must be exactly %d characters") % \
                       self.exact_length
        else:
            if len(barcode) < self.min_length:
                return False, _("Barcode must be at least %d characters") % \
                       self.min_length
            if len(barcode) > self.max_length:
                return False, _("Barcode must be at most %d characters") % \
                       self.max_length
        
        # Check prefix/suffix
        if self.prefix and not barcode.startswith(self.prefix):
            return False, _("Barcode must start with '%s'") % self.prefix
        if self.suffix and not barcode.endswith(self.suffix):
            return False, _("Barcode must end with '%s'") % self.suffix
        
        # Check character types
        for char in barcode:
            if char.isalpha() and not self.allow_letters:
                return False, _("Letters are not allowed in barcode")
            if char.isdigit() and not self.allow_numbers:
                return False, _("Numbers are not allowed in barcode")
            if not char.isalnum():
                if not self.allow_special:
                    return False, _("Special characters not allowed")
                if self.special_chars and char not in self.special_chars:
                    return False, _("Character '%s' is not allowed") % char
        
        return True, _("Barcode is valid")
    
    def generate_barcode(self):
        """Generate a new barcode based on configuration"""
        if not self.auto_generate or not self.sequence_id:
            return False
        
        # Generate base code from sequence
        base_code = self.sequence_id.next_by_id()
        
        # Add prefix/suffix
        if self.prefix:
            base_code = self.prefix + base_code
        if self.suffix:
            base_code = base_code + self.suffix
        
        # Pad to exact length if needed
        if self.fixed_length:
            if len(base_code) < self.exact_length:
                # Pad with zeros after prefix but before suffix
                padding_needed = self.exact_length - len(base_code)
                if self.suffix:
                    base_code = (base_code[:-len(self.suffix)] + 
                                '0' * padding_needed + self.suffix)
                else:
                    base_code = base_code + '0' * padding_needed
            elif len(base_code) > self.exact_length:
                # Truncate if too long
                base_code = base_code[:self.exact_length]
        
        return base_code


class RecordsBarcodeHistory(models.Model):
    _name = 'records.barcode.history'
    _description = 'Barcode History'
    _order = 'create_date desc'
    
    barcode = fields.Char(string='Barcode', required=True)
    barcode_config_id = fields.Many2one('records.barcode.config', 
                                       string='Barcode Configuration')
    
    # Related object
    model_name = fields.Char(string='Model Name', required=True)
    res_id = fields.Integer(string='Record ID', required=True)
    res_name = fields.Char(string='Record Name')
    
    # Tracking
    action = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('scanned', 'Scanned'),
        ('printed', 'Printed'),
        ('deleted', 'Deleted')
    ], string='Action', required=True)
    
    user_id = fields.Many2one('res.users', string='User', 
                             default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Date/Time', readonly=True)
    
    notes = fields.Text(string='Notes')


class RecordsProduct(models.Model):
    _name = 'records.product'
    _description = 'Records Management Products'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Product Name', required=True)
    code = fields.Char(string='Product Code', required=True)
    
    # Product details
    product_type = fields.Selection([
        ('box', 'Storage Box'),
        ('supplies', 'Office Supplies'),
        ('equipment', 'Equipment'),
        ('service', 'Service Item'),
        ('other', 'Other')
    ], string='Product Type', required=True, default='box')
    
    description = fields.Text(string='Description')
    
    # Pricing
    list_price = fields.Float(string='List Price', digits=(12, 2), required=True)
    cost_price = fields.Float(string='Cost Price', digits=(12, 2))
    
    # Inventory
    qty_available = fields.Integer(string='Quantity Available', default=0)
    qty_reserved = fields.Integer(string='Quantity Reserved', default=0)
    reorder_point = fields.Integer(string='Reorder Point', default=0)
    
    # Billing
    taxable = fields.Boolean(string='Taxable', default=True)
    tax_category = fields.Char(string='Tax Category')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    # Tracking
    create_date = fields.Datetime(string='Created On', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    write_date = fields.Datetime(string='Last Modified On', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Modified By', readonly=True)
    
    @api.constrains('list_price', 'cost_price')
    def _check_prices(self):
        """Validate prices are not negative"""
        for product in self:
            if product.list_price < 0:
                raise ValidationError(_("List price cannot be negative"))
            if product.cost_price < 0:
                raise ValidationError(_("Cost price cannot be negative"))


class RecordsBillingAutomation(models.Model):
    _name = 'records.billing.automation'
    _description = 'Billing Automation Rules'
    _rec_name = 'name'
    _order = 'sequence, name'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Trigger conditions
    trigger_type = fields.Selection([
        ('monthly', 'Monthly Recurring'),
        ('service_complete', 'Service Completion'),
        ('box_added', 'Box Added'),
        ('box_removed', 'Box Removed'),
        ('manual', 'Manual Trigger')
    ], string='Trigger Type', required=True)
    
    # Billing configuration
    billing_config_id = fields.Many2one(
        'records.billing.config', string='Billing Configuration', required=True)
    
    # Conditions
    customer_ids = fields.Many2many(
        'res.partner', string='Customers',
        domain="[('is_company', '=', True)]",
        help="Leave empty to apply to all customers")
    department_ids = fields.Many2many(
        'records.department', string='Departments',
        help="Leave empty to apply to all departments")
    
    # Service type conditions
    service_types = fields.Text(
        string='Service Types',
        help="Comma-separated list of service types to trigger billing")
    
    # Timing
    day_of_month = fields.Integer(
        string='Day of Month', default=1,
        help="For monthly triggers, which day to generate billing")
    
    # Processing
    auto_approve = fields.Boolean(
        string='Auto Approve', default=False,
        help="Automatically approve generated billing")
    auto_invoice = fields.Boolean(
        string='Auto Invoice', default=False,
        help="Automatically create invoices")
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    # Tracking
    last_run_date = fields.Datetime(string='Last Run Date', readonly=True)
    next_run_date = fields.Datetime(string='Next Run Date')
    run_count = fields.Integer(string='Run Count', default=0, readonly=True)
    
    # Notifications
    notify_users = fields.Many2many(
        'res.users', string='Notify Users',
        help="Users to notify when billing is generated")
    
    # Rules and logic
    notes = fields.Text(string='Notes')
    
    @api.constrains('day_of_month')
    def _check_day_of_month(self):
        """Validate day of month is valid"""
        for rule in self:
            if rule.day_of_month < 1 or rule.day_of_month > 31:
                raise ValidationError(_("Day of month must be between 1 and 31"))
    
    def execute_billing_rule(self):
        """Execute this billing automation rule"""
        self.ensure_one()
        
        if not self.active:
            return False
            
        # Log the execution
        self.write({
            'last_run_date': fields.Datetime.now(),
            'run_count': self.run_count + 1
        })
        
        # TODO: Implement actual billing logic based on trigger_type
        if self.trigger_type == 'monthly':
            return self._process_monthly_billing()
        elif self.trigger_type == 'service_complete':
            return self._process_service_billing()
        
        return True
    
    def _process_monthly_billing(self):
        """Process monthly recurring billing"""
        # TODO: Implement monthly billing logic
        return True
    
    def _process_service_billing(self):
        """Process service completion billing"""
        # TODO: Implement service billing logic
        return True