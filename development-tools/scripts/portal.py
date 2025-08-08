# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.exceptions import AccessError
import csv
import io
import json
from datetime import datetime, timedelta


class CustomerPortalExtended(CustomerPortal):
    
    @http.route('/my/overview', type='http', auth='user', website=True)
    def portal_overview(self, **kw):
        """Enhanced portal overview with stats, features, and AI suggestions"""
        partner = request.env.user.partner_id
        
        # Gather statistics
        total_boxes = request.env['records.box'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '!=', 'destroyed')
        ])
        
        total_documents = request.env['records.document'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '!=', 'destroyed')
        ])
        
        pending_requests = request.env['portal.request'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['draft', 'submitted', 'in_progress'])
        ])
        
        certificates_issued = request.env['portal.request'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'completed'),
            ('request_type', '=', 'destruction')
        ])
        
        # Recent activities (last 10)
        recent_activities = []
        
        # Recent boxes/documents activity
        recent_boxes = request.env['records.box'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='write_date desc', limit=3)
        
        for box in recent_boxes:
            recent_activities.append({
                'icon': 'archive',
                'color': 'primary',
                'description': f'Box {box.name} updated',
                'date': box.write_date.strftime('%Y-%m-%d %H:%M')
            })
        
        # Recent requests
        recent_requests = request.env['portal.request'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=3)
        
        for req in recent_requests:
            color = 'success' if req.state == 'completed' else 'warning' if req.state == 'in_progress' else 'info'
            recent_activities.append({
                'icon': 'tasks',
                'color': color,
                'description': f'{req.request_type.title()} request {req.state.replace("_", " ")}',
                'date': req.create_date.strftime('%Y-%m-%d %H:%M')
            })
        
        # Sort activities by date
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        
        # AI-powered suggestions based on user patterns
        suggestions = []
        
        # Check for boxes approaching retention expiry
        expiring_soon = request.env['records.box'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('retention_date', '<=', fields.Date.add(fields.Date.today(), days=30)),
            ('state', '!=', 'destroyed')
        ])
        
        if expiring_soon > 0:
            suggestions.append({
                'title': 'Retention Review Needed',
                'description': f'{expiring_soon} boxes are approaching retention expiry',
                'action': 'window.location.href="/my/inventory?filter=expiring"'
            })
        
        # Check for pending signatures
        pending_signatures = request.env['portal.request'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('is_signed', '=', False),
            ('state', 'in', ['submitted', 'in_progress'])
        ])
        
        if pending_signatures > 0:
            suggestions.append({
                'title': 'Signatures Required',
                'description': f'{pending_signatures} requests need your signature',
                'action': 'window.location.href="/my/requests?filter=unsigned"'
            })
        
        # Check for billing optimization
        if total_boxes > 50:
            suggestions.append({
                'title': 'Storage Optimization',
                'description': 'Consider bulk actions to optimize storage costs',
                'action': 'window.location.href="/my/inventory?bulk_mode=1"'
            })
        
        values = {
            'total_boxes': total_boxes,
            'total_documents': total_documents,
            'pending_requests': pending_requests,
            'certificates_issued': certificates_issued,
            'recent_activities': recent_activities[:5],  # Limit to 5 most recent
            'suggestions': suggestions,
            'page_name': 'overview',
        }
        
        return request.render('records_management.portal_overview', values)
    
    @http.route(['/my/invoices/<int:invoice_id>/update_po'], type='http', auth="user", website=True)
    def portal_invoice_update_po(self, invoice_id, **kw):
        """Enhanced PO update with NAID audit logging"""
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        if invoice.partner_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')
        
        po_number = kw.get('po_number')
        if po_number:
            # Enhanced update with audit fields
            invoice.write({
                'ref': po_number,
                'x_updated_by_id': request.env.user.id,
                'x_update_date': fields.Datetime.now(),
            })
            
            # NAID audit logging with user initials
            user_initials = ''.join([name[0].upper() for name in request.env.user.name.split() if name])
            invoice.message_post(
                body=_('PO # updated to %s by %s (%s) - NAID Audit Log', 
                      po_number, request.env.user.name, user_initials),
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        
        return request.redirect(f'/my/invoices/{invoice_id}')

    @http.route('/my/feedback/submit', type='http', auth="user", website=True, methods=['POST'])
    def portal_feedback_submit(self, **kw):
        """Submit customer feedback using survey module with NAID audit logging"""
        try:
            partner = request.env.user.partner_id
            
            # Create survey user input for feedback
            survey = request.env.ref('records_management.survey_feedback_portal', raise_if_not_found=False)
            if not survey:
                # Fallback to creating a simple feedback record
                feedback_vals = {
                    'name': kw.get('subject', f'Feedback from {partner.name}'),
                    'partner_id': partner.id,
                    'feedback_type': kw.get('feedback_type', 'general'),
                    'rating': kw.get('rating', '3'),
                    'comments': kw.get('comments', ''),
                    'service_area': kw.get('service_area', 'portal'),
                    'submitted_date': fields.Datetime.now(),
                }
                feedback = request.env['customer.feedback'].sudo().create(feedback_vals)
                
                # NAID audit logging
                feedback.message_post(
                    body=_('Customer feedback submitted by %s (User ID: %s) - NAID Audit Log', 
                          request.env.user.name, request.env.user.id),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            else:
                # Use survey module for structured feedback
                survey_user = request.env['survey.user_input'].sudo().create({
                    'survey_id': survey.id,
                    'partner_id': partner.id,
                    'state': 'done',
                    'scoring_type': survey.scoring_type,
                })
                
                # Process survey answers from form data
                for question in survey.question_ids:
                    answer_value = kw.get(f'question_{question.id}')
                    if answer_value:
                        request.env['survey.user_input.line'].sudo().create({
                            'user_input_id': survey_user.id,
                            'question_id': question.id,
                            'answer_type': question.question_type,
                            'value_text': str(answer_value) if question.question_type == 'text_box' else None,
                            'value_numerical_box': float(answer_value) if question.question_type == 'numerical_box' else None,
                            'suggested_answer_id': int(answer_value) if question.question_type in ['simple_choice', 'multiple_choice'] else None,
                        })
                
                # NAID audit logging for survey submission
                survey_user.message_post(
                    body=_('Customer feedback survey submitted by %s (User ID: %s) - NAID Audit Log', 
                          request.env.user.name, request.env.user.id),
                    message_type='notification'
                )
            
            return request.redirect('/my/feedback?success=1')
            
        except Exception as e:
            return request.redirect('/my/feedback?error=submission_failed')

    @http.route('/my/documents/data', type='json', auth="user", website=True)
    def portal_documents_data(self, **kw):
        """Centralized document data fetching with granular access control and NAID audit logging"""
        try:
            partner = request.env.user.partner_id
            
            # Log document access for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'partner_id': partner.id,
                'action': 'document_access',
                'resource_type': 'portal_documents',
                'access_date': fields.Datetime.now(),
                'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
                'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
            })
            
            # Invoices - customer level access
            invoices = request.env['account.move'].sudo().search([
                ('partner_id', '=', partner.id), 
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')
            ])
            
            # Quotes - customer level access  
            quotes = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id), 
                ('state', 'in', ['draft', 'sent', 'sale'])
            ])
            
            # Certificates - from shredding services
            shredding_services = request.env['records_management.shredding_service'].sudo().search([
                ('partner_id', '=', partner.id), 
                ('state', '=', 'completed')
            ])
            certificates = shredding_services.mapped('certificate_id').filtered(lambda c: c)
            
            # B2B Communications - messages and attachments at partner level
            communications = request.env['mail.message'].sudo().search([
                ('partner_ids', 'in', [partner.id]),
                ('message_type', 'in', ['email', 'sms', 'notification']),
                ('model', '=', 'res.partner')
            ])
            
            # Format data for JSON response
            return {
                'success': True,
                'invoices': [{
                    'id': inv.id,
                    'name': inv.name,
                    'date': inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else '',
                    'amount': inv.amount_total,
                    'currency': inv.currency_id.name,
                    'pdf_url': f'/my/invoices/{inv.id}/pdf',
                    'linked_cert': inv.x_linked_certificate.name if hasattr(inv, 'x_linked_certificate') and inv.x_linked_certificate else '',
                    'po_number': inv.ref or '',
                    'state': inv.state,
                } for inv in invoices],
                
                'quotes': [{
                    'id': q.id,
                    'name': q.name,
                    'date': q.date_order.strftime('%Y-%m-%d') if q.date_order else '',
                    'amount': q.amount_total,
                    'currency': q.currency_id.name,
                    'pdf_url': f'/my/quotes/{q.id}/pdf',
                    'state': q.state,
                    'validity_date': q.validity_date.strftime('%Y-%m-%d') if q.validity_date else '',
                } for q in quotes],
                
                'certificates': [{
                    'id': c.id,
                    'name': c.name,
                    'date': c.destruction_date.strftime('%Y-%m-%d') if hasattr(c, 'destruction_date') and c.destruction_date else '',
                    'certificate_number': c.certificate_number if hasattr(c, 'certificate_number') else '',
                    'pdf_url': f'/my/certificates/{c.id}/download',
                    'linked_invoice': c.invoice_id.name if hasattr(c, 'invoice_id') and c.invoice_id else '',
                    'destruction_type': c.destruction_type if hasattr(c, 'destruction_type') else 'standard',
                } for c in certificates],
                
                'communications': [{
                    'id': m.id,
                    'subject': m.subject or 'Communication',
                    'date': m.date.strftime('%Y-%m-%d %H:%M') if m.date else '',
                    'description': m.body[:200] + '...' if m.body and len(m.body) > 200 else (m.body or ''),
                    'message_type': m.message_type,
                    'author': m.author_id.name if m.author_id else 'System',
                    'url': f'/mail/view/{m.id}',
                    'attachment_count': len(m.attachment_ids),
                } for m in communications],
                
                'access_timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': request.env.user.id,
            }
            
        except Exception as e:
            # Log access error for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'document_access_error',
                'resource_type': 'portal_documents',
                'access_date': fields.Datetime.now(),
                'error_message': str(e),
            })
            
            return {
                'success': False,
                'error': 'Unable to fetch document data',
                'message': 'Please contact support if this issue persists'
            }

    @http.route('/my/inventory/documents/data', type='json', auth="user", website=True)
    def portal_inventory_documents_data(self, **kw):
        """Granular inventory document access filtered by user/department with NAID audit logging"""
        try:
            partner = request.env.user.partner_id
            user = request.env.user
            
            # Log inventory document access for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': user.id,
                'partner_id': partner.id,
                'action': 'inventory_document_access',
                'resource_type': 'inventory_documents',
                'access_date': fields.Datetime.now(),
                'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
                'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
            })
            
            # Determine access level and build domain
            access_info = self._get_user_access_info(partner)
            domain = []
            
            if access_info['access_level'] == 'company_admin':
                # Company admin sees all company inventory documents
                domain = [('customer_id', '=', access_info['customer'].id)]
            elif access_info['department']:
                # Department user sees only department inventory documents
                domain = [
                    ('department_id', '=', access_info['department'].id),
                    ('customer_id', '=', access_info['customer'].id)
                ]
            else:
                # Default to user-specific inventory (personal documents)
                domain = [
                    ('created_by_user_id', '=', user.id),
                    ('customer_id', '=', access_info['customer'].id)
                ]
            
            # Get inventory records based on access level
            boxes = request.env['records.box'].sudo().search(domain + [('state', '!=', 'destroyed')])
            documents = request.env['records.document'].sudo().search(domain + [('state', '!=', 'destroyed')])
            
            # Get related pickup requests and service records
            pickup_requests = request.env['pickup.request'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['confirmed', 'in_progress', 'completed'])
            ])
            
            # Get destruction certificates related to user's inventory
            destruction_certs = request.env['records_management.shredding_service'].sudo().search([
                '|', 
                ('box_ids', 'in', boxes.ids),
                ('document_ids', 'in', documents.ids),
                ('state', '=', 'completed')
            ])
            
            return {
                'success': True,
                'access_level': access_info['access_level'],
                'department': access_info['department'].name if access_info['department'] else None,
                
                'boxes': [{
                    'id': box.id,
                    'name': box.name,
                    'barcode': box.barcode,
                    'location': box.location_id.name if box.location_id else '',
                    'department': box.department_id.name if box.department_id else '',
                    'created_date': box.create_date.strftime('%Y-%m-%d') if box.create_date else '',
                    'retention_date': box.retention_date.strftime('%Y-%m-%d') if box.retention_date else '',
                    'state': box.state,
                    'document_count': len(box.document_ids),
                    'last_access': box.last_access_date.strftime('%Y-%m-%d') if hasattr(box, 'last_access_date') and box.last_access_date else '',
                } for box in boxes],
                
                'documents': [{
                    'id': doc.id,
                    'name': doc.name,
                    'document_type': doc.document_type_id.name if doc.document_type_id else '',
                    'box_id': doc.box_id.id if doc.box_id else None,
                    'box_name': doc.box_id.name if doc.box_id else '',
                    'department': doc.department_id.name if doc.department_id else '',
                    'created_date': doc.create_date.strftime('%Y-%m-%d') if doc.create_date else '',
                    'retention_date': doc.retention_date.strftime('%Y-%m-%d') if doc.retention_date else '',
                    'state': doc.state,
                    'confidentiality_level': doc.confidentiality_level if hasattr(doc, 'confidentiality_level') else 'normal',
                } for doc in documents],
                
                'pickup_requests': [{
                    'id': req.id,
                    'name': req.name,
                    'request_date': req.request_date.strftime('%Y-%m-%d') if req.request_date else '',
                    'pickup_date': req.pickup_date.strftime('%Y-%m-%d') if req.pickup_date else '',
                    'state': req.state,
                    'items_count': len(req.item_ids),
                    'service_type': req.service_type if hasattr(req, 'service_type') else 'pickup',
                } for req in pickup_requests],
                
                'destruction_certificates': [{
                    'id': cert.id,
                    'name': cert.name,
                    'certificate_number': cert.certificate_number if hasattr(cert, 'certificate_number') else '',
                    'destruction_date': cert.destruction_date.strftime('%Y-%m-%d') if cert.destruction_date else '',
                    'destruction_method': cert.destruction_method if hasattr(cert, 'destruction_method') else '',
                    'boxes_destroyed': len(cert.box_ids) if hasattr(cert, 'box_ids') else 0,
                    'documents_destroyed': len(cert.document_ids) if hasattr(cert, 'document_ids') else 0,
                    'certificate_url': f'/my/certificates/{cert.id}/download',
                } for cert in destruction_certs],
                
                'summary_stats': {
                    'total_boxes': len(boxes),
                    'total_documents': len(documents),
                    'active_requests': len(pickup_requests.filtered(lambda r: r.state in ['confirmed', 'in_progress'])),
                    'completed_destructions': len(destruction_certs),
                    'expiring_soon': len(boxes.filtered(lambda b: b.retention_date and b.retention_date <= fields.Date.add(fields.Date.today(), days=30))),
                },
                
                'access_timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user.id,
                'filters_applied': {
                    'department_filter': access_info['department'].name if access_info['department'] else None,
                    'user_filter': user.name if access_info['access_level'] == 'viewer' else None,
                }
            }
            
        except Exception as e:
            # Log inventory access error for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'inventory_document_access_error',
                'resource_type': 'inventory_documents',
                'access_date': fields.Datetime.now(),
                'error_message': str(e),
            })
            
            return {
                'success': False,
                'error': 'Unable to fetch inventory document data',
                'message': 'Access denied or data unavailable'
            }

    def _get_user_access_info(self, partner):
        """Get user access information for granular document filtering"""
        # Determine if user is company admin, department admin, or regular user
        user = request.env.user
        
        # Check for company admin role
        if user.has_group('records_management.group_records_company_admin'):
            customer = partner.parent_id if partner.parent_id else partner
            return {
                'access_level': 'company_admin',
                'department': None,
                'customer': customer,
                'permissions': {
                    'can_view_inventory': True,
                    'can_add_boxes': True,
                    'can_request_services': True,
                    'can_request_deletion': True,
                    'can_approve_deletion': True,
                    'can_view_billing': True,
                }
            }
        
        # Check for department admin role
        if user.has_group('records_management.group_records_dept_admin'):
            # Find user's department
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            department = employee.department_id if employee else None
            customer = partner.parent_id if partner.parent_id else partner
            
            return {
                'access_level': 'dept_admin',
                'department': department,
                'customer': customer,
                'permissions': {
                    'can_view_inventory': True,
                    'can_add_boxes': True,
                    'can_request_services': True,
                    'can_request_deletion': True,
                    'can_approve_deletion': False,
                    'can_view_billing': True,
                }
            }
        
        # Regular user/viewer
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        department = employee.department_id if employee else None
        customer = partner.parent_id if partner.parent_id else partner
        
        return {
            'access_level': 'viewer',
            'department': department,
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

    @http.route('/my/requests/create', type='json', auth="user", website=True)
    def portal_create_request(self, **kw):
        vals = {
            'partner_id': request.env.user.partner_id.id,
            'request_type': kw.get('type'),
            'description': kw.get('description'),
        }
        request_obj = request.env['portal.request'].sudo().create(vals)
        return {'id': request_obj.id, 'message': 'Request created.'}

    @http.route('/my/inventory/add_temp', type='json', auth="user", website=True)
    def portal_add_temp_inventory(self, **kw):
        vals = {
            'partner_id': request.env.user.partner_id.id,
            'inventory_type': kw.get('type'),
            'description': kw.get('description'),
        }
        temp = request.env['temp.inventory'].sudo().create(vals)
        return {'barcode': temp.temp_barcode}

    @http.route('/my/users/import', type='http', auth="user", website=True, csrf=True)
    def portal_import_users(self, **kw):
        # Handle CSV upload/import
        file_upload = kw.get('file')
        if file_upload:
            # Parse CSV, create portal users with access levels/departments
            file_content = file_upload.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(file_content))
            
            for row in csv_reader:
                if len(row) >= 2:  # Ensure minimum columns
                    user = request.env['res.users'].sudo().create({
                        'name': row[0],
                        'login': row[1],
                        'partner_id': request.env['res.partner'].sudo().create({
                            'name': row[0],
                            'email': row[1],
                            'parent_id': request.env.user.partner_id.id,  # Child contact
                            'is_company': False,
                        }).id,
                        'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],  # Portal access
                    })
                    # Assign departments/access via HR or custom fields
                    if len(row) >= 3:  # Department column
                        employee = request.env['hr.employee'].sudo().create({
                            'name': row[0],
                            'user_id': user.id,
                            'department_id': request.env['hr.department'].sudo().search([('name', '=', row[2])], limit=1).id,
                        })
        return request.redirect('/my/users')

    # Additional routes for multi-select actions (e.g., batch destruction request)
    @http.route('/my/inventory/batch_action', type='json', auth="user", website=True)
    def portal_batch_action(self, ids, action, **kw):
        items = request.env['records.box'].sudo().browse(ids)  # Or documents
        if action == 'destruction':
            req = request.env['portal.request'].sudo().create({
                'partner_id': request.env.user.partner_id.id,
                'request_type': 'destruction',
                'description': f'Batch destruction for items: {",".join(items.mapped("name"))}',
            })
            return {'success': True, 'request_id': req.id}
        elif action == 'checkout':
            req = request.env['portal.request'].sudo().create({
                'partner_id': request.env.user.partner_id.id,
                'request_type': 'inventory_checkout',
                'description': f'Batch checkout for items: {",".join(items.mapped("name"))}',
            })
            return {'success': True, 'request_id': req.id}
        return {'success': False}

    @http.route('/my/quotes/generate', type='json', auth="user", website=True)
    def portal_generate_quote(self, **kw):
        """Generate quote PDF for customer"""
        vals = {
            'partner_id': request.env.user.partner_id.id,
            'request_type': 'quote_generate',
            'description': kw.get('description', 'Quote request'),
        }
        quote_request = request.env['portal.request'].sudo().create(vals)
        return {'success': True, 'request_id': quote_request.id}

    @http.route('/my/requests/<int:request_id>/submit', type='json', auth="user", website=True)
    def portal_submit_request(self, request_id, **kw):
        """Submit portal request with signature"""
        portal_request = request.env['portal.request'].sudo().browse(request_id)
        if portal_request.partner_id.id == request.env.user.partner_id.id:
            portal_request.action_submit()
            return {'success': True, 'message': 'Request submitted successfully'}
        return {'success': False, 'message': 'Unauthorized'}

    @http.route('/my/requests/<int:request_id>/sign', type='http', auth="user", website=True)
    def portal_sign_request(self, request_id, **kw):
        """Handle signature for portal request"""
        portal_request = request.env['portal.request'].sudo().browse(request_id)
        if portal_request.partner_id.id == request.env.user.partner_id.id:
            # Redirect to sign module for signature
            if portal_request.sign_request_id:
                return request.redirect(f'/sign/document/{portal_request.sign_request_id.id}')
        return request.redirect('/my/requests')
    
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
            ('partner_id', '=', customer.id)
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
                        request.env['records.storage.department.user'].create({
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
                ('partner_id', '=', access_info['customer'].id)
            ])
        elif access_info['department']:
            departments = [access_info['department']]
        
        values = {
            'access_info': access_info,
            'departments': departments,
        }
        
        return request.render('records_management.portal_bulk_import_users', 
                            values)

    @http.route(['/my/docs'], type='http', auth="user", website=True)
    def portal_document_center(self, **kw):
        """Enhanced centralized document center with modern JSON data loading and NAID audit logging"""
        try:
            user = request.env.user
            partner = user.partner_id
            
            # Log document center access for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': user.id,
                'partner_id': partner.id,
                'action': 'document_center_access',
                'resource_type': 'document_center',
                'access_date': fields.Datetime.now(),
                'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
                'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
            })
            
            # Get document statistics for initial load
            doc_stats = self._get_document_statistics(partner)
            
            # Get minimal data for initial page load (will be enhanced via AJAX)
            initial_data = {
                'recent_invoices': self._get_customer_invoices(partner, limit=5),
                'recent_quotes': self._get_customer_quotes(partner, limit=5),
                'recent_certificates': self._get_customer_certificates(partner, limit=5),
                'recent_communications': self._get_customer_communications(partner, limit=5),
            }
            
            values = {
                'doc_stats': doc_stats,
                'initial_data': initial_data,
                'page_name': 'document_center',
                'user': user,
                'partner': partner,
                'load_data_url': '/my/documents/data',  # Modern JSON endpoint
                'inventory_data_url': '/my/inventory/documents/data',  # Granular inventory endpoint
                'naid_audit_enabled': True,
            }
            
            return request.render("records_management.portal_centralized_docs", values)
            
        except Exception as e:
            # Log error for NAID audit
            request.env['naid.audit.log'].sudo().create({
                'user_id': request.env.user.id,
                'action': 'document_center_access_error',
                'resource_type': 'document_center',
                'access_date': fields.Datetime.now(),
                'error_message': str(e),
            })
            
            return request.render("portal.portal_error", {
                'error_message': 'Unable to load document center. Please contact support.'
            })

    def _get_document_statistics(self, partner):
        """Get document statistics for the customer"""
        domain = [('partner_id', '=', partner.id)]
        
        # Count invoices
        total_invoices = request.env['account.move'].sudo().search_count(
            domain + [('move_type', '=', 'out_invoice')]
        )
        
        # Count quotes
        total_quotes = request.env['sale.order'].sudo().search_count(
            domain + [('state', 'in', ['draft', 'sent', 'sale'])]
        )
        
        # Count certificates (from shredding services)
        total_certificates = request.env['records_management.shredding_service'].sudo().search_count(
            domain + [('state', '=', 'completed')]
        )
        
        # Count communications
        total_communications = request.env['mail.message'].sudo().search_count([
            ('partner_ids', 'in', [partner.id]),
            ('message_type', 'in', ['email', 'sms', 'notification'])
        ])
        
        return {
            'total_invoices': total_invoices,
            'total_quotes': total_quotes,
            'total_certificates': total_certificates,
            'total_communications': total_communications,
        }
    
    def _get_customer_invoices(self, partner, limit=None):
        """Get customer invoices with portal access"""
        domain = [
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ]
        return request.env['account.move'].sudo().search(
            domain, order='invoice_date desc', limit=limit
        )
    
    def _get_customer_quotes(self, partner, limit=None):
        """Get customer quotes/sales orders"""
        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['draft', 'sent', 'sale'])
        ]
        return request.env['sale.order'].sudo().search(
            domain, order='date_order desc', limit=limit
        )
    
    def _get_customer_certificates(self, partner, limit=None):
        """Get destruction certificates"""
        domain = [
            ('partner_id', '=', partner.id),
            ('state', '=', 'completed')
        ]
        return request.env['records_management.shredding_service'].sudo().search(
            domain, order='destruction_date desc', limit=limit
        )
    
    def _get_customer_communications(self, partner, limit=None):
        """Get customer communications (emails, SMS, notifications)"""
        domain = [
            ('partner_ids', 'in', [partner.id]),
            ('message_type', 'in', ['email', 'sms', 'notification'])
        ]
        return request.env['mail.message'].sudo().search(
            domain, order='date desc', limit=limit
        )

    @http.route(['/my/docs/load_tab_data'], type='json', auth="user", methods=['POST'])
    def load_tab_data(self, tab, **kw):
        """Load data for a specific tab via AJAX"""
        try:
            partner = request.env.user.partner_id
            data = {}
            
            if tab == 'invoices':
                data = self._get_customer_invoices(partner, limit=50)
            elif tab == 'quotes':
                data = self._get_customer_quotes(partner, limit=50)
            elif tab == 'certificates':
                data = self._get_customer_certificates(partner, limit=50)
            elif tab == 'communications':
                data = self._get_customer_communications(partner, limit=50)
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/docs/recent_activity'], type='json', auth="user", methods=['POST'])
    def get_recent_activity(self, **kw):
        """Get recent document activity for the customer"""
        try:
            partner = request.env.user.partner_id
            
            # Get recent activities across all document types
            recent_activities = []
            
            # Recent invoices
            recent_invoices = self._get_customer_invoices(partner, limit=5)
            for invoice in recent_invoices:
                recent_activities.append({
                    'type': 'invoice',
                    'name': invoice.name,
                    'date': invoice.invoice_date,
                    'url': f'/my/invoices/{invoice.id}'
                })
            
            # Recent quotes
            recent_quotes = self._get_customer_quotes(partner, limit=5)
            for quote in recent_quotes:
                recent_activities.append({
                    'type': 'quote',
                    'name': quote.name,
                    'date': quote.date_order,
                    'url': f'/my/quotes/{quote.id}'
                })
            
            # Sort by date
            recent_activities.sort(key=lambda x: x['date'], reverse=True)
            
            return {'recent_activities': recent_activities[:10]}
            
        except Exception as e:
            return {'recent_activities': []}

    @http.route(['/my/docs/check_updates'], type='json', auth="user", methods=['POST'])
    def check_for_updates(self, last_check, **kw):
        """Check for document updates since last check"""
        try:
            partner = request.env.user.partner_id
            last_check_dt = fields.Datetime.from_string(last_check)
            
            # Check for new documents since last check
            new_invoices = request.env['account.move'].sudo().search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('create_date', '>', last_check_dt)
            ])
            
            new_quotes = request.env['sale.order'].sudo().search_count([
                ('partner_id', '=', partner.id),
                ('create_date', '>', last_check_dt)
            ])
            
            new_communications = request.env['mail.message'].sudo().search_count([
                ('partner_ids', 'in', [partner.id]),
                ('date', '>', last_check_dt)
            ])
            
            has_updates = (new_invoices + new_quotes + new_communications) > 0
            
            return {
                'has_updates': has_updates,
                'new_invoices': new_invoices,
                'new_quotes': new_quotes,
                'new_communications': new_communications
            }
            
        except Exception as e:
            return {'has_updates': False}

    @http.route(['/my/invoices/update_po'], type='json', auth="user", methods=['POST'])
    def update_invoice_po(self, invoice_id, po_number, **kw):
        """Update PO number for an invoice"""
        try:
            invoice = request.env['account.move'].sudo().browse(int(invoice_id))
            
            # Verify access
            if invoice.partner_id != request.env.user.partner_id:
                return {'success': False, 'error': 'Access denied'}
            
            # Update PO number
            invoice.sudo().write({'ref': po_number})
            
            # Log the change
            invoice.message_post(
                body=f"PO number updated to: {po_number}",
                message_type='notification'
            )
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/docs/export_all'], type='http', auth="user", website=True)
    def export_all_documents(self, **kw):
        """Export all customer documents as a comprehensive package"""
        try:
            partner = request.env.user.partner_id
            
            # Create a zip file with all documents
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add invoices
                invoices = self._get_customer_invoices(partner)
                for invoice in invoices:
                    if invoice.attachment_ids:
                        for attachment in invoice.attachment_ids:
                            zip_file.writestr(
                                f"invoices/{invoice.name}_{attachment.name}",
                                attachment.datas
                            )
                
                # Add quotes
                quotes = self._get_customer_quotes(partner)
                for quote in quotes:
                    if quote.attachment_ids:
                        for attachment in quote.attachment_ids:
                            zip_file.writestr(
                                f"quotes/{quote.name}_{attachment.name}",
                                attachment.datas
                            )
                
                # Add certificates
                certificates = self._get_customer_certificates(partner)
                for cert in certificates:
                    if hasattr(cert, 'certificate_attachment_id') and cert.certificate_attachment_id:
                        zip_file.writestr(
                            f"certificates/{cert.name}_{cert.certificate_attachment_id.name}",
                            cert.certificate_attachment_id.datas
                        )
            
            zip_buffer.seek(0)
            
            return request.make_response(
                zip_buffer.read(),
                headers=[
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition', f'attachment; filename="documents_{partner.name}_{fields.Date.today()}.zip"')
                ]
            )
            
        except Exception as e:
            return request.render("portal.portal_error", {
                'error_message': 'Unable to export documents. Please try again.'
            })


class PortalCertificateController(http.Controller):

    @http.route(['/my/certificates/<int:visit_id>'], type='http', auth='user', website=True)
    def download_certificate(self, visit_id, **kw):
        """Download destruction certificate for a visitor's linked transaction.
        
        - Checks ownership for security (NAID/ISO compliance).
        - Renders PDF report; innovative extension: could add QR code in report for verification.
        - Logs download for NAID auditing.
        """
        visitor = request.env['frontdesk.visitor'].sudo().browse(visit_id)
        if not visitor.exists() or visitor.partner_id != request.env.user.partner_id:
            raise AccessError("You do not have access to this certificate.")
        
        if not visitor.pos_order_id:
            return request.not_found()  # Or redirect with message
        
        # Render the report (adjust action ID if your report is for a different model, e.g., frontdesk.visitor)
        pdf_content, _ = request.env.ref('records_management.action_report_destruction_certificate')._render_qweb_pdf([visitor.pos_order_id.id])
        
        # NAID audit logging for certificate download
        request.env['naid.audit.log'].sudo().create({
            'user_id': request.env.user.id,
            'partner_id': request.env.user.partner_id.id,
            'action': 'certificate_download',
            'resource_type': 'destruction_certificate',
            'access_date': fields.Datetime.now(),
            'resource_id': visit_id,
            'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
            'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
        })
        
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="Destruction_Certificate_{visitor.name}.pdf"'),
            ('Content-Length', len(pdf_content)),
        ]
        return request.make_response(pdf_content, headers=headers)
    
    # Document Retrieval Portal Routes
    
    @http.route('/my/document-retrieval', type='http', auth='user', website=True)
    def portal_document_retrieval(self, **kw):
        """Portal page for document retrieval requests with pricing"""
        partner = request.env.user.partner_id
        
        # Get customer-specific rates if available
        customer_rates = request.env['customer.retrieval.rates'].sudo().search([
            ('customer_id', '=', partner.id),
            ('active', '=', True),
            ('effective_date', '<=', fields.Date.today()),
            '|',
            ('expiry_date', '=', False),
            ('expiry_date', '>=', fields.Date.today())
        ], limit=1, order='effective_date desc')
        
        # Get base rates
        base_rates = request.env['document.retrieval.rates'].sudo().search([
            ('active', '=', True)
        ], limit=1, order='effective_date desc')
        
        if not base_rates:
            # Create default rates if none exist
            base_rates = request.env['document.retrieval.rates'].sudo().create({
                'name': 'Default Rates',
            })
        
        # Get customer's boxes and documents for selection
        boxes = request.env['records.box'].sudo().search([
            ('customer_id', '=', partner.id),
            ('state', '=', 'active')
        ], order='name')
        
        documents = request.env['records.document'].sudo().search([
            ('customer_id', '=', partner.id),
            ('state', '=', 'active')
        ], order='name')
        
        # Get existing work orders
        work_orders = request.env['document.retrieval.work.order'].sudo().search([
            ('customer_id', '=', partner.id)
        ], order='request_date desc', limit=10)
        
        values = {
            'partner': partner,
            'customer_rates': customer_rates,
            'base_rates': base_rates,
            'has_custom_rates': bool(customer_rates),
            'boxes': boxes,
            'documents': documents,
            'work_orders': work_orders,
            'page_name': 'document_retrieval',
        }
        
        return request.render('records_management.portal_document_retrieval', values)
    
    @http.route('/my/document-retrieval/calculate-price', type='json', auth='user')
    def calculate_retrieval_price(self, priority='standard', item_count=1, **kw):
        """Calculate retrieval price based on priority and item count"""
        partner = request.env.user.partner_id
        
        # Get customer-specific rates
        customer_rates = request.env['customer.retrieval.rates'].sudo().search([
            ('customer_id', '=', partner.id),
            ('active', '=', True),
            ('effective_date', '<=', fields.Date.today()),
            '|',
            ('expiry_date', '=', False),
            ('expiry_date', '>=', fields.Date.today())
        ], limit=1, order='effective_date desc')
        
        # Get base rates
        base_rates = request.env['document.retrieval.rates'].sudo().search([
            ('active', '=', True)
        ], limit=1, order='effective_date desc')
        
        if not base_rates:
            return {'error': 'No rates configured'}
        
        # Calculate pricing
        if customer_rates and customer_rates.custom_retrieval_rate > 0:
            retrieval_rate = customer_rates.custom_retrieval_rate
        else:
            retrieval_rate = base_rates.base_retrieval_rate
        
        if customer_rates and customer_rates.custom_delivery_rate > 0:
            delivery_rate = customer_rates.custom_delivery_rate
        else:
            delivery_rate = base_rates.base_delivery_rate
        
        # Base costs
        base_retrieval_cost = retrieval_rate * item_count
        base_delivery_cost = delivery_rate
        
        # Priority fees
        priority_item_fee = 0.0
        priority_order_fee = 0.0
        
        if priority == 'rush_eod':
            priority_item_fee = base_rates.rush_end_of_day_item
            priority_order_fee = base_rates.rush_end_of_day_order
        elif priority == 'rush_4h':
            priority_item_fee = base_rates.rush_4_hours_item
            priority_order_fee = base_rates.rush_4_hours_order
        elif priority == 'emergency_1h':
            priority_item_fee = base_rates.emergency_1_hour_item
            priority_order_fee = base_rates.emergency_1_hour_order
        elif priority == 'weekend':
            priority_item_fee = base_rates.weekend_item
            priority_order_fee = base_rates.weekend_order
        elif priority == 'holiday':
            priority_item_fee = base_rates.holiday_item
            priority_order_fee = base_rates.holiday_order
        
        # Apply customer multipliers
        if customer_rates:
            if priority in ['rush_eod', 'rush_4h']:
                multiplier = customer_rates.rush_multiplier
            elif priority == 'emergency_1h':
                multiplier = customer_rates.emergency_multiplier
            elif priority == 'weekend':
                multiplier = customer_rates.weekend_multiplier
            elif priority == 'holiday':
                multiplier = customer_rates.holiday_multiplier
            else:
                multiplier = 1.0
            
            priority_item_fee *= multiplier
            priority_order_fee *= multiplier
        
        priority_item_cost = priority_item_fee * item_count
        priority_order_cost = priority_order_fee
        
        total_cost = base_retrieval_cost + base_delivery_cost + priority_item_cost + priority_order_cost
        
        return {
            'base_retrieval_cost': base_retrieval_cost,
            'base_delivery_cost': base_delivery_cost,
            'priority_item_cost': priority_item_cost,
            'priority_order_cost': priority_order_cost,
            'total_cost': total_cost,
            'has_custom_rates': bool(customer_rates),
            'priority_label': dict([
                ('standard', 'Standard (48 Hours)'),
                ('rush_eod', 'Rush (End of Day)'),
                ('rush_4h', 'Rush (4 Hours)'),
                ('emergency_1h', 'Emergency (1 Hour)'),
                ('weekend', 'Weekend Service'),
                ('holiday', 'Holiday Service')
            ]).get(priority, priority)
        }
    
    @http.route('/my/document-retrieval/create', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def create_retrieval_work_order(self, **post):
        """Create a new document retrieval work order"""
        partner = request.env.user.partner_id
        
        # Get form data
        priority = post.get('priority', 'standard')
        delivery_date = post.get('delivery_date')
        delivery_address = post.get('delivery_address', '')
        delivery_contact = post.get('delivery_contact', '')
        delivery_phone = post.get('delivery_phone', '')
        retrieval_notes = post.get('retrieval_notes', '')
        
        # Create work order
        work_order_vals = {
            'customer_id': partner.id,
            'priority': priority,
            'delivery_address': delivery_address,
            'delivery_contact': delivery_contact,
            'delivery_phone': delivery_phone,
            'retrieval_notes': retrieval_notes,
            'requested_by': request.env.user.id,
        }
        
        if delivery_date:
            try:
                work_order_vals['delivery_date'] = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            except:
                pass
        
        work_order = request.env['document.retrieval.work.order'].sudo().create(work_order_vals)
        
        # Add items to retrieve
        items_data = json.loads(post.get('items', '[]'))
        for item_data in items_data:
            item_vals = {
                'work_order_id': work_order.id,
                'item_type': item_data.get('type', 'box'),
                'description': item_data.get('description', ''),
                'barcode': item_data.get('barcode', ''),
                'retrieval_notes': item_data.get('notes', ''),
            }
            
            if item_data.get('type') == 'box' and item_data.get('box_id'):
                item_vals['box_id'] = int(item_data['box_id'])
            elif item_data.get('type') == 'document' and item_data.get('document_id'):
                item_vals['document_id'] = int(item_data['document_id'])
            
            request.env['document.retrieval.item'].sudo().create(item_vals)
        
        # Send notification
        work_order.message_post(
            body=_('Work order created via customer portal. Estimated cost: $%.2f') % work_order.total_cost
        )
        
        return request.redirect('/my/document-retrieval?message=Order created successfully!')
    
    @http.route('/my/document-retrieval/<int:order_id>', type='http', auth='user', website=True)
    def view_retrieval_work_order(self, order_id, **kw):
        """View a specific work order"""
        partner = request.env.user.partner_id
        
        work_order = request.env['document.retrieval.work.order'].sudo().search([
            ('id', '=', order_id),
            ('customer_id', '=', partner.id)
        ])
        
        if not work_order:
            return request.not_found()
        
        values = {
            'work_order': work_order,
            'partner': partner,
            'page_name': 'document_retrieval_detail',
        }
        
        return request.render('records_management.portal_document_retrieval_detail', values)
