from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError
import base64
import csv
import io


class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Customer Department for Records Management'
    _rec_name = 'name'
    _order = 'company_id, name'

    name = fields.Char(string='Department Name', required=True)
    code = fields.Char(string='Department Code', size=10, required=True)
    company_id = fields.Many2one(
        'res.partner', string='Company', required=True,
        domain=[('is_company', '=', True)])
    
    # Department Admin
    admin_id = fields.Many2one(
        'res.partner', string='Department Admin',
        domain="[('parent_id', '=', company_id), ('is_company', '=', False)]")
    
    # Contact Information
    email = fields.Char(string='Department Email')
    phone = fields.Char(string='Department Phone')
    
    # Status and Settings
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    
    # Billing and Budget
    budget_limit = fields.Float(string='Monthly Budget Limit')
    billing_contact_id = fields.Many2one(
        'res.partner', string='Billing Contact',
        domain="[('parent_id', '=', company_id), ('is_company', '=', False)]")
    
    # Related Records
    user_ids = fields.One2many(
        'res.partner', 'department_id', string='Department Users')
    box_ids = fields.One2many(
        'records.box', 'department_id', string='Department Boxes')
    
    # Computed Fields
    total_users = fields.Integer(
        string='Total Users', compute='_compute_totals', store=True)
    total_boxes = fields.Integer(
        string='Total Boxes', compute='_compute_totals', store=True)
    monthly_cost = fields.Float(
        string='Monthly Cost', compute='_compute_monthly_cost', store=True)
    
    @api.depends('user_ids', 'box_ids')
    def _compute_totals(self):
        for dept in self:
            dept.total_users = len(dept.user_ids)
            dept.total_boxes = len(dept.box_ids.filtered(
                lambda b: b.state != 'destroyed'))
    
    @api.depends('box_ids', 'box_ids.monthly_storage_cost')
    def _compute_monthly_cost(self):
        for dept in self:
            # Assuming records.box has a monthly_storage_cost field
            boxes = dept.box_ids.filtered(lambda b: b.state == 'stored')
            dept.monthly_cost = len(boxes) * 25.0  # Default $25 per box
    
    @api.constrains('admin_id', 'company_id')
    def _check_admin_company(self):
        for dept in self:
            if dept.admin_id and dept.admin_id.parent_id != dept.company_id:
                raise ValidationError(
                    'Department admin must belong to the same company.')
    
    def name_get(self):
        result = []
        for dept in self:
            name = f"[{dept.code}] {dept.name}"
            if dept.company_id:
                name = f"{dept.company_id.name} - {name}"
            result.append((dept.id, name))
        return result


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Existing fields
    document_ids = fields.One2many(
        'records.document', 'partner_id', string='Related Documents')
    document_count = fields.Integer(compute='_compute_document_count')
    
    # Department and Role Management
    department_id = fields.Many2one(
        'records.department', string='Department')
    records_role = fields.Selection([
        ('company_admin', 'Company Admin'),
        ('dept_admin', 'Department Admin'),
        ('dept_user', 'Department User'),
        ('read_only', 'Read Only User')
    ], string='Records Access Level', default='read_only')
    
    # Company Admin fields
    is_records_company_admin = fields.Boolean(
        string='Is Records Company Admin', default=False)
    managed_departments = fields.One2many(
        'records.department', 'admin_id', string='Managed Departments')
    
    # Portal Access Control
    portal_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read_only', 'View Only'),
        ('user', 'User Access'),
        ('admin', 'Admin Access'),
        ('company_admin', 'Company Admin')
    ], string='Portal Access Level', default='none')
    
    # User Invitation and Management
    invitation_token = fields.Char(string='Invitation Token', copy=False)
    invitation_sent_date = fields.Datetime(string='Invitation Sent')
    invitation_accepted_date = fields.Datetime(string='Invitation Accepted')
    invitation_status = fields.Selection([
        ('draft', 'Draft'),
        ('invited', 'Invited'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired')
    ], string='Invitation Status', default='draft')
    
    # Employee Management (for bulk import)
    employee_id = fields.Char(string='Employee ID')
    job_title = fields.Char(string='Job Title')
    direct_manager_id = fields.Many2one(
        'res.partner', string='Direct Manager',
        domain="[('parent_id', '=', parent_id), ('is_company', '=', False)]")
    
    # Access Permissions
    can_add_inventory = fields.Boolean(
        string='Can Add Inventory', compute='_compute_permissions')
    can_edit_inventory = fields.Boolean(
        string='Can Edit Inventory', compute='_compute_permissions')
    can_delete_inventory = fields.Boolean(
        string='Can Delete Inventory', compute='_compute_permissions')
    can_approve_deletions = fields.Boolean(
        string='Can Approve Deletions', compute='_compute_permissions')
    can_manage_users = fields.Boolean(
        string='Can Manage Users', compute='_compute_permissions')
    can_view_billing = fields.Boolean(
        string='Can View Billing', compute='_compute_permissions')
    
    # Computed fields for dashboard
    dept_boxes_count = fields.Integer(
        string='Department Boxes', compute='_compute_dept_stats')
    dept_monthly_cost = fields.Float(
        string='Department Monthly Cost', compute='_compute_dept_stats')
    total_company_cost = fields.Float(
        string='Total Company Cost', compute='_compute_company_stats')
    pending_approvals_count = fields.Integer(
        string='Pending Approvals', compute='_compute_approval_stats')
    
    @api.depends('records_role', 'portal_access_level')
    def _compute_permissions(self):
        for partner in self:
            role = partner.records_role
            
            # Default permissions
            partner.can_add_inventory = False
            partner.can_edit_inventory = False
            partner.can_delete_inventory = False
            partner.can_approve_deletions = False
            partner.can_manage_users = False
            partner.can_view_billing = False
            
            if role == 'company_admin':
                partner.can_add_inventory = True
                partner.can_edit_inventory = True
                partner.can_delete_inventory = True
                partner.can_approve_deletions = True
                partner.can_manage_users = True
                partner.can_view_billing = True
            elif role == 'dept_admin':
                partner.can_add_inventory = True
                partner.can_edit_inventory = True
                partner.can_delete_inventory = True
                partner.can_approve_deletions = True
                partner.can_manage_users = True
                partner.can_view_billing = True  # Department billing only
            elif role == 'dept_user':
                partner.can_add_inventory = True
                partner.can_edit_inventory = True
                partner.can_delete_inventory = False  # Needs approval
                partner.can_approve_deletions = False
                partner.can_manage_users = False
                partner.can_view_billing = False
            elif role == 'read_only':
                # All permissions already False
                pass
    
    @api.depends('department_id', 'records_role')
    def _compute_approval_stats(self):
        for partner in self:
            if partner.records_role in ('company_admin', 'dept_admin'):
                # Count pending deletion requests that need approval
                DeletionRequest = self.env['records.deletion.request']
                domain = []
                if partner.records_role == 'dept_admin':
                    domain = [('department_id', '=', partner.department_id.id)]
                elif partner.records_role == 'company_admin':
                    domain = [('company_id', '=', partner.id)]
                
                # Add approval status filter
                domain.append(('state', 'in', ['pending', 'dept_approved']))
                count = DeletionRequest.search_count(domain)
                partner.pending_approvals_count = count
            else:
                partner.pending_approvals_count = 0

    @api.depends('department_id', 'department_id.box_ids')
    def _compute_dept_stats(self):
        for partner in self:
            if partner.department_id:
                boxes = partner.department_id.box_ids.filtered(
                    lambda b: b.state != 'destroyed')
                partner.dept_boxes_count = len(boxes)
                partner.dept_monthly_cost = len(boxes) * 25.0
            else:
                partner.dept_boxes_count = 0
                partner.dept_monthly_cost = 0.0
    
    @api.depends('is_records_company_admin', 'child_ids.department_id')
    def _compute_company_stats(self):
        for partner in self:
            if partner.is_records_company_admin and partner.is_company:
                # Get all departments for this company
                departments = self.env['records.department'].search([
                    ('company_id', '=', partner.id)
                ])
                partner.total_company_cost = sum(departments.mapped(
                    'monthly_cost'))
            else:
                partner.total_company_cost = 0.0

    def _compute_document_count(self):
        for partner in self:
            partner.document_count = len(partner.document_ids)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    
    # User Management Methods
    def action_invite_user(self):
        """Invite a new user to the portal"""
        self.ensure_one()
        if not self.can_manage_users:
            raise AccessError(_("You don't have permission to invite users."))
        
        # Generate invitation token
        import secrets
        token = secrets.token_urlsafe(32)
        self.write({
            'invitation_token': token,
            'invitation_sent_date': fields.Datetime.now(),
            'invitation_status': 'invited'
        })
        
        # Send invitation email
        self._send_invitation_email()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Invitation sent successfully.'),
                'type': 'success',
            }
        }
    
    def action_bulk_invite_users(self):
        """Open wizard for bulk user invitation"""
        self.ensure_one()
        if not self.can_manage_users:
            raise AccessError(_("You don't have permission to invite users."))
        
        return {
            'name': _('Bulk User Invitation'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.user.invitation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.id if self.is_company else self.parent_id.id,
                'default_department_id': self.department_id.id if self.department_id else False,
            }
        }
    
    def action_view_pending_approvals(self):
        """View pending deletion approval requests"""
        self.ensure_one()
        domain = []
        if self.records_role == 'dept_admin':
            domain = [('department_id', '=', self.department_id.id)]
        elif self.records_role == 'company_admin':
            domain = [('company_id', '=', self.id)]
        domain.append(('state', 'in', ['pending', 'dept_approved']))
        
        return {
            'name': _('Pending Approvals'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.deletion.request',
            'view_mode': 'tree,form',
            'domain': domain,
        }
    
    def action_view_department_billing(self):
        """View department billing breakdown"""
        self.ensure_one()
        if not self.can_view_billing:
            raise AccessError(_("You don't have permission to view billing."))
        
        return {
            'name': _('Billing Breakdown'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing.report',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
        }
    
    def action_view_company_billing(self):
        """View company-wide billing breakdown"""
        self.ensure_one()
        if self.records_role != 'company_admin':
            raise AccessError(_("Only company admins can view company billing."))
        
        return {
            'name': _('Company Billing'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing.report',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('company_id', '=', self.id)],
            'context': {'default_company_id': self.id},
        }
    
    def _send_invitation_email(self):
        """Send invitation email to user"""
        template = self.env.ref(
            'records_management.email_template_user_invitation', 
            raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
    
    @api.model
    def accept_invitation(self, token):
        """Accept user invitation and activate portal access"""
        partner = self.search([('invitation_token', '=', token)], limit=1)
        if not partner:
            raise UserError(_('Invalid invitation token.'))
        
        if partner.invitation_status != 'invited':
            raise UserError(_('This invitation has already been used or expired.'))
        
        # Check if invitation is not expired (valid for 7 days)
        import datetime
        sent_date = fields.Datetime.from_string(partner.invitation_sent_date)
        if sent_date + datetime.timedelta(days=7) < datetime.datetime.now():
            partner.invitation_status = 'expired'
            raise UserError(_('This invitation has expired.'))
        
        # Activate portal access
        partner.write({
            'invitation_status': 'accepted',
            'invitation_accepted_date': fields.Datetime.now(),
            'portal_access_level': 'user' if partner.records_role == 'dept_user' else 'admin'
        })
        
        return True


class RecordsDeletionRequest(models.Model):
    _name = 'records.deletion.request'
    _description = 'Records Deletion Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='Request Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('New'))
    
    # Request Details
    company_id = fields.Many2one(
        'res.partner', string='Company', required=True,
        domain=[('is_company', '=', True)])
    department_id = fields.Many2one(
        'records.department', string='Department', required=True)
    requester_id = fields.Many2one(
        'res.partner', string='Requester', required=True,
        default=lambda self: self.env.user.partner_id)
    
    # Items to Delete
    box_ids = fields.Many2many(
        'records.box', string='Boxes to Delete')
    document_ids = fields.Many2many(
        'records.document', string='Documents to Delete')
    
    # Request Information
    reason = fields.Text(string='Reason for Deletion', required=True)
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Urgency', default='medium')
    
    # Dates
    requested_date = fields.Date(
        string='Requested Deletion Date', 
        default=fields.Date.today)
    approved_date = fields.Datetime(string='Approved Date')
    executed_date = fields.Datetime(string='Executed Date')
    
    # Approval Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('dept_approved', 'Department Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Approvals
    dept_admin_approval_id = fields.Many2one(
        'res.partner', string='Department Admin Approval')
    dept_admin_approval_date = fields.Datetime(
        string='Department Approval Date')
    company_admin_approval_id = fields.Many2one(
        'res.partner', string='Company Admin Approval')
    company_admin_approval_date = fields.Datetime(
        string='Company Approval Date')
    
    # Billing and Cost
    estimated_cost = fields.Float(
        string='Estimated Destruction Cost', 
        compute='_compute_estimated_cost')
    actual_cost = fields.Float(string='Actual Cost')
    billable_to = fields.Selection([
        ('company', 'Company'),
        ('department', 'Department')
    ], string='Bill To', default='department')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'records.deletion.request') or _('New')
        return super().create(vals)
    
    @api.depends('box_ids', 'document_ids')
    def _compute_estimated_cost(self):
        for request in self:
            # Calculate based on shredding service rates
            box_cost = len(request.box_ids) * 15.0  # $15 per box
            doc_cost = len(request.document_ids) * 2.0  # $2 per document
            request.estimated_cost = box_cost + doc_cost
    
    def action_submit_for_approval(self):
        """Submit request for approval"""
        self.ensure_one()
        if not (self.box_ids or self.document_ids):
            raise UserError(_('Please select items to delete.'))
        
        if not self.reason:
            raise UserError(_('Please provide a reason for deletion.'))
        
        self.write({'state': 'pending'})
        
        self.message_post(
            body=_('Deletion request submitted for approval.'),
            message_type='notification')
    
    def action_dept_approve(self):
        """Department admin approval"""
        self.ensure_one()
        current_user = self.env.user.partner_id
        
        # Check if user is department admin
        if (current_user.records_role != 'dept_admin' or 
            current_user.department_id != self.department_id):
            raise UserError(_(
                'Only department admins can approve this request.'))
        
        self.write({
            'state': 'dept_approved',
            'dept_admin_approval_id': current_user.id,
            'dept_admin_approval_date': fields.Datetime.now(),
        })
        
        self.message_post(
            body=_('Request approved by department admin.'),
            message_type='notification')
    
    def action_company_approve(self):
        """Company admin final approval"""
        self.ensure_one()
        current_user = self.env.user.partner_id
        
        # Check if user is company admin
        if current_user.records_role != 'company_admin':
            raise UserError(_(
                'Only company admins can give final approval.'))
        
        self.write({
            'state': 'approved',
            'company_admin_approval_id': current_user.id,
            'company_admin_approval_date': fields.Datetime.now(),
            'approved_date': fields.Datetime.now(),
        })
        
        self.message_post(
            body=_('Request approved by company admin.'),
            message_type='notification')


class RecordsUserInvitationWizard(models.TransientModel):
    _name = 'records.user.invitation.wizard'
    _description = 'User Invitation Wizard'

    company_id = fields.Many2one(
        'res.partner', string='Company', required=True,
        domain=[('is_company', '=', True)])
    department_id = fields.Many2one(
        'records.department', string='Department')
    
    # Single User Invitation
    name = fields.Char(string='Full Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    job_title = fields.Char(string='Job Title')
    employee_id = fields.Char(string='Employee ID')
    records_role = fields.Selection([
        ('dept_admin', 'Department Admin'),
        ('dept_user', 'Department User'),
        ('read_only', 'Read Only User')
    ], string='Access Level', default='dept_user')
    
    # Bulk Import
    user_file = fields.Binary(string='User File (CSV)')
    file_name = fields.Char(string='File Name')
    
    # Options
    send_invitation = fields.Boolean(
        string='Send Invitation Email', default=True)
    invitation_method = fields.Selection([
        ('single', 'Single User'),
        ('bulk', 'Bulk Import (CSV)')
    ], string='Method', default='single')
    
    def action_invite_single_user(self):
        """Invite a single user"""
        if not all([self.name, self.email]):
            raise UserError(_('Name and email are required.'))
        
        # Check if user already exists
        existing = self.env['res.partner'].search([
            ('email', '=', self.email),
            ('parent_id', '=', self.company_id.id)
        ])
        
        if existing:
            raise UserError(_('User with this email already exists.'))
        
        # Create new user
        user_vals = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'parent_id': self.company_id.id,
            'is_company': False,
            'customer_rank': 1,
            'supplier_rank': 0,
            'department_id': self.department_id.id,
            'records_role': self.records_role,
            'job_title': self.job_title,
            'employee_id': self.employee_id,
            'portal_access_level': 'none',
            'invitation_status': 'draft',
        }
        
        new_user = self.env['res.partner'].create(user_vals)
        
        # Send invitation if requested
        if self.send_invitation:
            new_user.action_invite_user()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('User invited successfully.'),
                'type': 'success',
            }
        }
    
    def action_bulk_import_users(self):
        """Import users from CSV file"""
        if not self.user_file:
            raise UserError(_('Please upload a CSV file.'))
        
        # Decode file content
        file_content = base64.b64decode(self.user_file).decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        created_users = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                if not all([row.get('name'), row.get('email')]):
                    errors.append(f'Row {row_num}: Name and email required')
                    continue
                
                # Check if user exists
                existing = self.env['res.partner'].search([
                    ('email', '=', row['email']),
                    ('parent_id', '=', self.company_id.id)
                ])
                
                if existing:
                    errors.append(f'Row {row_num}: User {row["email"]} exists')
                    continue
                
                # Create user
                user_vals = {
                    'name': row['name'],
                    'email': row['email'],
                    'phone': row.get('phone', ''),
                    'parent_id': self.company_id.id,
                    'is_company': False,
                    'customer_rank': 1,
                    'supplier_rank': 0,
                    'department_id': self.department_id.id,
                    'records_role': row.get('role', 'dept_user'),
                    'job_title': row.get('job_title', ''),
                    'employee_id': row.get('employee_id', ''),
                    'portal_access_level': 'none',
                    'invitation_status': 'draft',
                }
                
                new_user = self.env['res.partner'].create(user_vals)
                created_users.append(new_user)
                
                # Send invitation if requested
                if self.send_invitation:
                    new_user.action_invite_user()
                    
            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')
        
        # Show results
        message = f'Successfully created {len(created_users)} users.'
        if errors:
            message += f'\n{len(errors)} errors occurred:\n' + '\n'.join(errors[:5])
            if len(errors) > 5:
                message += f'\n... and {len(errors) - 5} more errors.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success' if not errors else 'warning',
            }
        }
