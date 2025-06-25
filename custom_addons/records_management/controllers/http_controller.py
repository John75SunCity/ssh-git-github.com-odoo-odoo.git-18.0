from odoo import http
import logging

_logger = logging.getLogger(__name__)

CUSTOMER_FIELD = 'customer_id'
INTERNAL_USAGE = 'internal'
INVENTORY_PAGE_LIMIT = 100  # Limit for scalability

class MyController(http.Controller):
    """
    Controller for managing inventory-related HTTP requests.
    """

    def _get_current_user(self):
        """
        Helper to get the current Odoo user.
        Returns:
            res.users recordset
        """
        return http.request.env.user

    def _get_current_partner(self):
        """
        Helper to get the current user's partner.
        Returns:
            res.partner recordset
        """
        return self._get_current_user().partner_id

    def _handle_message(self, error=None, success=None):
        """
        Modularize error and success message handling.
        Args:
            error (str): Error message.
            success (str): Success message.
        Returns:
            dict: Message context for rendering.
        """
        if error:
            return {'message': error, 'message_type': 'error'}
        if success:
            return {'message': success, 'message_type': 'success'}
        return {'message': '', 'message_type': ''}

    def _get_partner_inventory(self, partner, limit=INVENTORY_PAGE_LIMIT):
        """
        Retrieve inventory for a given partner, paginated for scalability.
        Args:
            partner: res.partner recordset.
            limit (int): Max number of records to return.
        Returns:
            stock.quant recordset.
        """
        try:
            serials = http.request.env['stock.production.lot'].search([(CUSTOMER_FIELD, '=', partner.id)])
            if not serials:
                _logger.info("No serials found for partner %s", partner.id)
                return http.request.env['stock.quant'].browse([])
            quants = http.request.env['stock.quant'].search([
                ('lot_id', 'in', serials.ids),
                ('location_id.usage', '=', INTERNAL_USAGE)
            ], limit=limit)
            _logger.info("Fetched %d inventory items for partner %s", len(quants), partner.id)
            return quants
        except Exception as e:
            _logger.error("Database error fetching inventory for partner %s: %s", partner.id, e)
            return http.request.env['stock.quant'].browse([])

    def _parse_item_ids(self, form):
        """
        Safely parse item_ids from form data.
        Args:
            form: werkzeug.form object.
        Returns:
            List of item_ids as integers, or None if parsing fails.
        """
        item_ids = form.getlist('item_ids')
        if not item_ids:
            _logger.warning("No item_ids provided in the form.")
            return None
        try:
            # Validate: only allow positive integers, remove duplicates
            parsed_ids = []
            for id_str in item_ids:
                id_int = int(id_str)
                if id_int <= 0:
                    raise ValueError("Item ID must be positive.")
                parsed_ids.append(id_int)
            unique_ids = list(set(parsed_ids))
            _logger.info("Parsed item_ids: %s", unique_ids)
            return unique_ids
        except Exception as e:
            _logger.error("Error parsing item_ids: %s. Data: %s", e, item_ids)
            return None

    @http.route('/my/inventory/request_pickup', type='http', auth='user', methods=['POST'], csrf=True)
    def request_pickup(self, **kw):
        """
        Handle pickup requests for inventory items.
        Enhanced logging, error handling, and user feedback.
        """
        user = self._get_current_user()
        partner = self._get_current_partner()
        _logger.info('Pickup request initiated by user %s (ID: %s), partner %s', user.login, user.id, partner.id)
        item_ids = self._parse_item_ids(http.request.httprequest.form)
        if item_ids is None:
            _logger.warning("User %s (ID: %s) provided invalid item_ids: %s", user.login, user.id, http.request.httprequest.form.getlist('item_ids'))
            return http.request.redirect('/my/inventory?error=invalid_item_ids')
        try:
            # ...existing code for processing pickup...
            _logger.info('Pickup requested for items %s by partner %s', item_ids, partner.id)
            # On success:
            return http.request.redirect('/my/inventory?success=pickup_requested')
        except Exception as e:
            _logger.error("Error processing pickup request for user %s: %s", user.login, e)
            return http.request.redirect('/my/inventory?error=pickup_failed')

    @http.route('/my/inventory', type='http', auth='user', website=True, methods=['GET'], csrf=True)
    def my_inventory(self, **kw):
        """
        Render the inventory page for the current user.
        Enhanced with pagination, user-friendly messages, and tooltips.
        """
        user = self._get_current_user()
        partner = self._get_current_partner()
        error = http.request.params.get('error')
        success = http.request.params.get('success')
        message_ctx = self._handle_message(
            error="Invalid item selection. Please select valid inventory items." if error == 'invalid_item_ids' else (
                "An error occurred while processing your pickup request. Please try again later." if error == 'pickup_failed' else None
            ),
            success="Pickup request submitted successfully!" if success == 'pickup_requested' else None
        )
        quants = self._get_partner_inventory(partner)
        if not quants:
            message_ctx['message'] = 'No inventory items found. If you believe this is an error, please contact support.'
            message_ctx['message_type'] = 'info'
        inventory_tooltips = {
            'pickup': 'Request pickup for selected inventory items. Only available for items in internal locations.'
        }
        return http.request.render(
            'records_management.inventory_template',
            {
                'quants': quants,
                'message': message_ctx['message'],
                'message_type': message_ctx['message_type'],
                'tooltips': inventory_tooltips,
                'page_limit': INVENTORY_PAGE_LIMIT,
            }
        )

    # ...other controller logic can be added here...
