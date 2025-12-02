from odoo import http, _
from odoo.http import request


class PortalBarcodeController(http.Controller):
    """JSON endpoints for portal barcode management (generate new barcodes).

    Security: restricted to internal records user/manager groups (not public portal)
    to avoid uncontrolled barcode generation. Front-end can later adapt if
    customer portal exposure is desired (would then extend access domain or add
    dedicated rule).
    """

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
    def validate_portal_scan(self, barcode='', scan_type='container', **kw):
        """
        Validate a barcode scanned from the portal camera scanner.
        
        Returns item details if found and accessible by the current user.
        Used by portal_camera_scanner.js for pickup requests, retrievals, etc.
        
        Args:
            barcode: The scanned barcode value
            scan_type: Type of item to find ('container', 'file', 'inventory')
            
        Returns:
            dict: {success: bool, item_id: int, item_name: str, message: str}
        """
        if not barcode:
            return {'success': False, 'message': _('No barcode provided')}
        
        partner = request.env.user.partner_id
        
        try:
            if scan_type == 'container':
                # Search for container by barcode that belongs to this customer
                container = request.env['records.container'].sudo().search([
                    ('barcode', '=', barcode),
                    ('partner_id', '=', partner.id)
                ], limit=1)
                
                if container:
                    return {
                        'success': True,
                        'item_id': container.id,
                        'item_name': container.name,
                        'barcode': container.barcode,
                        'location': container.location_id.name if container.location_id else '',
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
                            'message': _('Container with this barcode belongs to another customer')
                        }
                    return {
                        'success': False,
                        'message': _('No container found with barcode: %s') % barcode
                    }
                    
            elif scan_type == 'file':
                # Search for file/document by barcode
                file_rec = request.env['records.file'].sudo().search([
                    ('barcode', '=', barcode),
                    ('partner_id', '=', partner.id)
                ], limit=1)
                
                if file_rec:
                    return {
                        'success': True,
                        'item_id': file_rec.id,
                        'item_name': file_rec.name,
                        'barcode': file_rec.barcode,
                        'container': file_rec.container_id.name if file_rec.container_id else '',
                        'message': _('File found: %s') % file_rec.name
                    }
                else:
                    return {
                        'success': False,
                        'message': _('No file found with barcode: %s') % barcode
                    }
                    
            elif scan_type == 'inventory':
                # Search customer inventory items
                inventory_item = request.env['customer.inventory.line'].sudo().search([
                    ('barcode', '=', barcode),
                    ('inventory_id.partner_id', '=', partner.id)
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
