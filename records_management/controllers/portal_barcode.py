from odoo import http, _
from odoo.http import request


class PortalBarcodeController(http.Controller):
    """JSON endpoints for portal barcode management (generate new barcodes).

    Security: restricted to internal records user/manager groups (not public portal)
    to avoid uncontrolled barcode generation. Front-end can later adapt if
    customer portal exposure is desired (would then extend access domain or add
    dedicated rule).
    """

    def _get_user_department_ids(self, partner):
        """
        Get department IDs that the current user has access to.
        
        Returns list of department IDs or empty list if no department restrictions.
        """
        department_ids = []
        
        # Check if user is linked to specific departments via records_department_users
        if hasattr(partner, 'records_department_users'):
            department_ids = partner.records_department_users.mapped('department_id.id')
        
        return department_ids

    def _check_department_access(self, record, partner, department_ids):
        """
        Check if user has access to a record based on department.
        
        If record has a department_id and user has department restrictions,
        verify the record's department is in user's accessible departments.
        
        Returns True if access allowed, False otherwise.
        """
        # If no department restrictions, allow access
        if not department_ids:
            return True
        
        # If record doesn't have department field, allow access
        if not hasattr(record, 'department_id') or not record.department_id:
            return True
        
        # Check if record's department is in user's accessible departments
        return record.department_id.id in department_ids

    # Updated for Odoo 18: type="jsonrpc" not supported -> use 'json'
    @http.route(['/records_management/portal/generate_barcode'], type='json', auth='user', methods=['POST'], csrf=True)
    def generate_portal_barcode(self, barcode_type='generic', barcode_format='code128'):
        env = request.env
        if not (request.env.user.has_group('records_management.group_records_user') or request.env.user.has_group('records_management.group_records_manager')):
            return {'success': False, 'error': _('Access denied')}

        try:
            rec = env['portal.barcode'].sudo().generate_portal_barcode(barcode_type=barcode_type, barcode_format=barcode_format)
            # Render row snippet once template exists; placeholder for now
            row_html = request.env['ir.ui.view']._render_template(
                'records_management.portal_barcode_row',
                {
                    'barcode': rec,
                }
            ) if request.env['ir.ui.view'].sudo()._views_get(['records_management.portal_barcode_row']) else ''
            return {
                'success': True,
                'barcode': {
                    'id': rec.id,
                    'name': rec.name,
                    'state': rec.state,
                    'barcode_type': rec.barcode_type,
                    'barcode_format': rec.barcode_format,
                    'last_scanned': rec.last_scanned and fields.Datetime.to_string(rec.last_scanned) or False,
                },
                'row_html': row_html,
            }
        except Exception as e:  # broad - return safe error
            return {'success': False, 'error': str(e)}

    @http.route(['/my/scan/validate'], type='json', auth='user', methods=['POST'], csrf=True)
    def validate_portal_scan(self, barcode='', scan_type='container', department_id=None, **kw):
        """
        Validate a barcode scanned from the portal camera scanner.
        
        Returns item details if found and accessible by the current user.
        Used by portal_camera_scanner.js for pickup requests, retrievals, etc.
        
        Security:
        - Only returns items belonging to the logged-in customer
        - Filters by department if user has department restrictions
        - Returns clear error if item belongs to another customer
        
        Args:
            barcode: The scanned barcode value
            scan_type: Type of item to find ('container', 'file', 'inventory')
            department_id: Optional department ID to filter by
            
        Returns:
            dict: {success: bool, item_id: int, item_name: str, message: str}
        """
        if not barcode:
            return {'success': False, 'message': _('No barcode provided')}
        
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id or partner
        
        # Get user's accessible department IDs
        user_department_ids = self._get_user_department_ids(partner)
        
        try:
            if scan_type == 'container':
                # Search for container by barcode that belongs to this customer
                # Check both partner_id and commercial_partner for parent/child relationships
                container = request.env['records.container'].sudo().search([
                    ('barcode', '=', barcode),
                    '|',
                    ('partner_id', '=', partner.id),
                    ('partner_id', '=', commercial_partner.id)
                ], limit=1)
                
                if container:
                    # Check department access
                    if not self._check_department_access(container, partner, user_department_ids):
                        return {
                            'success': False,
                            'access_denied': True,
                            'message': _('This container belongs to a different department. You do not have access.')
                        }
                    
                    # Optional: filter by specific department if provided
                    if department_id and hasattr(container, 'department_id') and container.department_id:
                        if container.department_id.id != int(department_id):
                            return {
                                'success': False,
                                'access_denied': True,
                                'message': _('This container belongs to department "%s", not the selected department.') % container.department_id.name
                            }
                    
                    return {
                        'success': True,
                        'item_id': container.id,
                        'item_name': container.name,
                        'barcode': container.barcode,
                        'location': container.location_id.name if container.location_id else '',
                        'department': container.department_id.name if hasattr(container, 'department_id') and container.department_id else '',
                        'customer': container.partner_id.name,
                        'message': _('Container found: %s') % container.name
                    }
                else:
                    # Check if container exists but belongs to someone else
                    other_container = request.env['records.container'].sudo().search([
                        ('barcode', '=', barcode)
                    ], limit=1)
                    if other_container:
                        return {
                            'success': False,
                            'access_denied': True,
                            'belongs_to_other': True,
                            'message': _('⚠️ This container does NOT belong to your account. It belongs to another customer.')
                        }
                    return {
                        'success': False,
                        'message': _('No container found with barcode: %s') % barcode
                    }
                    
            elif scan_type == 'file':
                # Search for file/document by barcode
                file_rec = request.env['records.file'].sudo().search([
                    ('barcode', '=', barcode),
                    '|',
                    ('partner_id', '=', partner.id),
                    ('partner_id', '=', commercial_partner.id)
                ], limit=1)
                
                if file_rec:
                    # Check department access
                    if not self._check_department_access(file_rec, partner, user_department_ids):
                        return {
                            'success': False,
                            'access_denied': True,
                            'message': _('This file belongs to a different department. You do not have access.')
                        }
                    
                    return {
                        'success': True,
                        'item_id': file_rec.id,
                        'item_name': file_rec.name,
                        'barcode': file_rec.barcode,
                        'container': file_rec.container_id.name if file_rec.container_id else '',
                        'department': file_rec.department_id.name if hasattr(file_rec, 'department_id') and file_rec.department_id else '',
                        'message': _('File found: %s') % file_rec.name
                    }
                else:
                    # Check if file exists but belongs to someone else
                    other_file = request.env['records.file'].sudo().search([
                        ('barcode', '=', barcode)
                    ], limit=1)
                    if other_file:
                        return {
                            'success': False,
                            'access_denied': True,
                            'belongs_to_other': True,
                            'message': _('⚠️ This file does NOT belong to your account. It belongs to another customer.')
                        }
                    return {
                        'success': False,
                        'message': _('No file found with barcode: %s') % barcode
                    }
                    
            elif scan_type == 'inventory':
                # Search customer inventory items
                inventory_item = request.env['customer.inventory.line'].sudo().search([
                    ('barcode', '=', barcode),
                    '|',
                    ('inventory_id.partner_id', '=', partner.id),
                    ('inventory_id.partner_id', '=', commercial_partner.id)
                ], limit=1)
                
                if inventory_item:
                    return {
                        'success': True,
                        'item_id': inventory_item.id,
                        'item_name': inventory_item.name or inventory_item.display_name,
                        'barcode': inventory_item.barcode,
                        'message': _('Inventory item found: %s') % (inventory_item.name or inventory_item.display_name)
                    }
                else:
                    # Check if inventory item exists but belongs to someone else
                    other_item = request.env['customer.inventory.line'].sudo().search([
                        ('barcode', '=', barcode)
                    ], limit=1)
                    if other_item:
                        return {
                            'success': False,
                            'access_denied': True,
                            'belongs_to_other': True,
                            'message': _('⚠️ This inventory item does NOT belong to your account. It belongs to another customer.')
                        }
                    return {
                        'success': False,
                        'message': _('No inventory item found with barcode: %s') % barcode
                    }
            else:
                return {
                    'success': False,
                    'message': _('Invalid scan type: %s') % scan_type
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': _('Error validating barcode: %s') % str(e)
            }

    @http.route(['/my/scan/verify_delivery'], type='json', auth='user', methods=['POST'], csrf=True)
    def verify_delivery_ownership(self, barcode='', expected_customer_id=None, expected_department_id=None, **kw):
        """
        Verify that a scanned container/file belongs to the expected customer for delivery.
        
        This endpoint is used by technicians during delivery to prevent delivering
        items to the wrong customer. The technician scans the item and the system
        verifies it matches the expected customer on the work order.
        
        Args:
            barcode: The scanned barcode value
            expected_customer_id: The customer ID from the work order/delivery
            expected_department_id: Optional department ID to verify
            
        Returns:
            dict: {
                success: bool,
                verified: bool,
                message: str,
                item_type: str,
                item_name: str,
                actual_customer: str,
                expected_customer: str
            }
        """
        if not barcode:
            return {'success': False, 'verified': False, 'message': _('No barcode provided')}
        
        if not expected_customer_id:
            return {'success': False, 'verified': False, 'message': _('Expected customer ID is required for delivery verification')}
        
        try:
            expected_customer_id = int(expected_customer_id)
            expected_partner = request.env['res.partner'].sudo().browse(expected_customer_id)
            
            if not expected_partner.exists():
                return {'success': False, 'verified': False, 'message': _('Invalid customer ID')}
            
            # Get commercial partner for parent/child matching
            expected_commercial = expected_partner.commercial_partner_id or expected_partner
            
            # Search for container first
            container = request.env['records.container'].sudo().search([
                ('barcode', '=', barcode)
            ], limit=1)
            
            if container:
                actual_customer = container.partner_id
                actual_commercial = actual_customer.commercial_partner_id or actual_customer
                
                # Check if customer matches
                customer_match = (
                    actual_customer.id == expected_customer_id or
                    actual_commercial.id == expected_commercial.id
                )
                
                if not customer_match:
                    return {
                        'success': True,
                        'verified': False,
                        'mismatch': True,
                        'item_type': 'container',
                        'item_id': container.id,
                        'item_name': container.name,
                        'actual_customer': actual_customer.name,
                        'expected_customer': expected_partner.name,
                        'message': _('⚠️ WRONG CUSTOMER! This container belongs to "%s", NOT "%s". Do not deliver!') % (
                            actual_customer.name, expected_partner.name
                        )
                    }
                
                # Check department if specified
                if expected_department_id and hasattr(container, 'department_id') and container.department_id:
                    if container.department_id.id != int(expected_department_id):
                        expected_dept = request.env['records.department'].sudo().browse(int(expected_department_id))
                        return {
                            'success': True,
                            'verified': False,
                            'department_mismatch': True,
                            'item_type': 'container',
                            'item_id': container.id,
                            'item_name': container.name,
                            'actual_department': container.department_id.name,
                            'expected_department': expected_dept.name if expected_dept.exists() else 'Unknown',
                            'message': _('⚠️ WRONG DEPARTMENT! This container belongs to department "%s", NOT "%s".') % (
                                container.department_id.name, expected_dept.name if expected_dept.exists() else 'Unknown'
                            )
                        }
                
                return {
                    'success': True,
                    'verified': True,
                    'item_type': 'container',
                    'item_id': container.id,
                    'item_name': container.name,
                    'customer': actual_customer.name,
                    'department': container.department_id.name if hasattr(container, 'department_id') and container.department_id else '',
                    'location': container.location_id.name if container.location_id else '',
                    'message': _('✅ VERIFIED: Container %s belongs to %s. OK to deliver.') % (
                        container.name, actual_customer.name
                    )
                }
            
            # Search for file if not found as container
            file_rec = request.env['records.file'].sudo().search([
                ('barcode', '=', barcode)
            ], limit=1)
            
            if file_rec:
                actual_customer = file_rec.partner_id
                actual_commercial = actual_customer.commercial_partner_id or actual_customer
                
                # Check if customer matches
                customer_match = (
                    actual_customer.id == expected_customer_id or
                    actual_commercial.id == expected_commercial.id
                )
                
                if not customer_match:
                    return {
                        'success': True,
                        'verified': False,
                        'mismatch': True,
                        'item_type': 'file',
                        'item_id': file_rec.id,
                        'item_name': file_rec.name,
                        'actual_customer': actual_customer.name,
                        'expected_customer': expected_partner.name,
                        'message': _('⚠️ WRONG CUSTOMER! This file belongs to "%s", NOT "%s". Do not deliver!') % (
                            actual_customer.name, expected_partner.name
                        )
                    }
                
                return {
                    'success': True,
                    'verified': True,
                    'item_type': 'file',
                    'item_id': file_rec.id,
                    'item_name': file_rec.name,
                    'customer': actual_customer.name,
                    'container': file_rec.container_id.name if file_rec.container_id else '',
                    'message': _('✅ VERIFIED: File %s belongs to %s. OK to deliver.') % (
                        file_rec.name, actual_customer.name
                    )
                }
            
            # Not found
            return {
                'success': False,
                'verified': False,
                'message': _('No container or file found with barcode: %s') % barcode
            }
            
        except Exception as e:
            return {
                'success': False,
                'verified': False,
                'message': _('Error verifying barcode: %s') % str(e)
            }
