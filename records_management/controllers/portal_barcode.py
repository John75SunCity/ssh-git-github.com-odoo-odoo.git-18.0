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
