from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
import base64
import csv
import io
import json


class RecordsPortal(http.Controller):
    
    def _get_user_access_info(self, partner):
        """Get user's access level and permissions"""
        # Check if user is a department user
        dept_user = request.env['records.department.user'].search([
            ('user_id', '=', partner.id)
        ], limit=1)
        
        if dept_user:
            return {
                'access_level': dept_user.access_level,
                'department': dept_user.department_id,
                'customer': dept_user.department_id.company_id,
                'permissions': {
                    'can_view_inventory': dept_user.can_view_inventory,
                    'can_add_boxes': dept_user.can_add_boxes,
                    'can_request_services': dept_user.can_request_services,
                    'can_request_deletion': dept_user.can_request_deletion,
                    'can_approve_deletion': dept_user.can_approve_deletion,
                    'can_view_billing': dept_user.can_view_billing,
                }
            }
        
        # Check if user is company admin (parent company)
        if partner.is_company:
            return {
                'access_level': 'company_admin',
                'department': None,
                'customer': partner,
                'permissions': {
                    'can_view_inventory': True,
                    'can_add_boxes': True,
                    'can_request_services': True,
                    'can_request_deletion': True,
                    'can_approve_deletion': True,
                    'can_view_billing': True,
                }
            }
        
        # Default access for company contacts
        customer = partner.parent_id if partner.parent_id else partner
        return {
            'access_level': 'viewer',
            'department': None,
            'customer': customer,
            'permissions': {
                'can_view_inventory': True,
                'can_add_boxes': False,
                'can_request_services': False,
                'can_request_deletion': False,
                'can_approve_deletion': False,
                'can_view_billing': False,
            }
        }
    
    @http.route('/my/records', type='http', auth='user', website=True)
    def my_records_dashboard(self, **kw):
        """Main dashboard for records management portal"""
        partner = request.env.user.partner_id
        access_info = self._get_user_access_info(partner)
        
        # Get domain based on access level
        if access_info['access_level'] == 'company_admin':
            # Company admin sees all company data
            domain = [('customer_id', '=', access_info['customer'].id)]
        elif access_info['department']:
            # Department user sees only department data
            domain = [('department_id', '=', access_info['department'].id)]
        else:
            # Default to customer level
            domain = [('customer_id', '=', access_info['customer'].id)]
        
        # Get inventory data
        boxes = request.env['records.box'].search(domain)
        documents = request.env['records.document'].search(domain)        
        # Get service requests
        service_requests = request.env['records.service.request'].search([
            ('customer_id', '=', access_info['customer'].id),
            ('state', 'in', ['submitted', 'approved', 'scheduled', 'in_progress'])
        ])
        
        # Calculate statistics
        stats = {
            'boxes_count': len(boxes),
            'documents_count': len(documents),
            'locations_count': len(boxes.mapped('location_id')),
            'active_requests': len(service_requests),
        }
        
        # Get billing info if user has access
        billing_info = {}
        if access_info['permissions']['can_view_billing']:
            if access_info['access_level'] == 'company_admin':
                billing_info = self._get_company_billing(access_info['customer'])
            elif access_info['department']:
                billing_info = self._get_department_billing(access_info['department'])
        
        values = {
            'access_info': access_info,
            'stats': stats,
            'boxes': boxes[:10],  # Show first 10 for dashboard
            'recent_documents': documents.search(domain, 
                                               order='create_date desc', 
                                               limit=10),
            'service_requests': service_requests[:5],  # Recent 5
            'billing_info': billing_info,
        }
        
        return request.render('records_management.portal_records_dashboard', values)
    
    def _get_company_billing(self, customer):
        """Get billing information for entire company"""
        departments = request.env['records.department'].search([
            ('company_id', '=', customer.id)
        ])
        
        total_cost = sum(dept.monthly_cost for dept in departments)
        dept_breakdown = [
            {
                'name': dept.name,
                'boxes': dept.total_boxes,
                'cost': dept.monthly_cost
            }
            for dept in departments
        ]
        
        return {
            'total_monthly_cost': total_cost,
            'department_breakdown': dept_breakdown,
            'total_departments': len(departments)
        }
    
    def _get_department_billing(self, department):
        """Get billing information for specific department"""
        return {
            'monthly_cost': department.monthly_cost,
            'total_boxes': department.total_boxes,
            'total_documents': department.total_documents
        }
    
    # Legacy route for compatibility
    @http.route('/my/inventory', type='http', auth='user', website=True)
    def my_records_inventory_legacy(self, **kw):
        """Legacy route - redirect to new dashboard"""
        return request.redirect('/my/records')
    
    @http.route('/my/records/services/new', type='http', auth='user', 
                website=True, methods=['GET', 'POST'])
    def new_service_request(self, **kw):
        """Create new service request"""
        partner = request.env.user.partner_id
        access_info = self._get_user_access_info(partner)
        
        if not access_info['permissions']['can_request_services']:
            return request.redirect('/my/records?error=no_permission')
        
        if request.httprequest.method == 'POST':
            # Create service request
            vals = {
                'service_type': kw.get('service_type'),
                'customer_id': access_info['customer'].id,
                'department_id': (access_info['department'].id 
                                if access_info['department'] else False),
                'requested_by': partner.id,
                'description': kw.get('description'),
                'priority': kw.get('priority', 'normal'),
                'quantity': int(kw.get('quantity', 1)),
                'special_instructions': kw.get('special_instructions'),
            }
            
            # Handle box selection for certain service types
            if kw.get('service_type') in ['return', 'retrieval']:
                box_ids = [int(id) for id in kw.getlist('box_ids') if id]
                if box_ids:
                    vals['box_ids'] = [(6, 0, box_ids)]
            
            request.env['records.service.request'].create(vals)
            return request.redirect('/my/records?success=service_requested')
        
        # GET request - show form
        domain = []
        if access_info['department']:
            domain.append(('department_id', '=', access_info['department'].id))
        else:
            domain.append(('customer_id', '=', access_info['customer'].id))
        
        boxes = request.env['records.box'].search(
            domain + [('state', '=', 'active')])
        
        values = {
            'access_info': access_info,
            'boxes': boxes,
        }
        
        return request.render('records_management.portal_new_service_request', 
                            values)
    
    @http.route('/my/records/users/bulk_import', type='http', auth='user', 
                website=True, methods=['GET', 'POST'])
    def bulk_import_users(self, **kw):
        """Bulk import users from CSV"""
        partner = request.env.user.partner_id
        access_info = self._get_user_access_info(partner)
        
        if access_info['access_level'] not in ['dept_admin', 'company_admin']:
            return request.redirect('/my/records?error=no_permission')
        
        if request.httprequest.method == 'POST':
            # Handle CSV upload
            csv_file = request.httprequest.files.get('csv_file')
            if not csv_file:
                return request.redirect(
                    '/my/records/users/bulk_import?error=no_file')
            
            try:
                # Parse CSV
                csv_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                
                created_count = 0
                for row in csv_reader:
                    # Create or find user
                    user_vals = {
                        'name': row.get('name', ''),
                        'email': row.get('email', ''),
                        'phone': row.get('phone', ''),
                        'function': row.get('job_title', ''),
                        'parent_id': access_info['customer'].id,
                        'is_company': False,
                    }
                    
                    user = request.env['res.partner'].search([
                        ('email', '=', user_vals['email']),
                        ('parent_id', '=', access_info['customer'].id)
                    ], limit=1)
                    
                    if not user:
                        user = request.env['res.partner'].create(user_vals)
                    
                    # Create department user record
                    dept_id = int(row.get('department_id', 
                                        access_info['department'].id 
                                        if access_info['department'] else 0))
                    if dept_id:
                        request.env['records.department.user'].create({
                            'department_id': dept_id,
                            'user_id': user.id,
                            'access_level': row.get('access_level', 'viewer'),
                        })
                        created_count += 1
                
                return request.redirect(
                    f'/my/records?success=imported_{created_count}')
                
            except Exception:
                return request.redirect(
                    '/my/records/users/bulk_import?error=parse_error')
        
        # GET request - show form
        departments = []
        if access_info['access_level'] == 'company_admin':
            departments = request.env['records.department'].search([
                ('company_id', '=', access_info['customer'].id)
            ])
        elif access_info['department']:
            departments = [access_info['department']]
        
        values = {
            'access_info': access_info,
            'departments': departments,
        }
        
        return request.render('records_management.portal_bulk_import_users', 
                            values)
