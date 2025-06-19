from odoo import http
import logging

_logger = logging.getLogger(__name__)

CUSTOMER_FIELD = 'customer_id'
INTERNAL_USAGE = 'internal'
INVENTORY_PAGE_LIMIT = 100  # Limit for scalability

class MyController(http.Controller):
<<<<<<< HEAD
    """
    Controller for managing inventory-related HTTP requests.
    """

    def _get_partner_inventory(self, partner):
        """
        Fetch inventory items associated with the given partner.
        Args:
            partner: res.partner record.
        Returns:
            Recordset of stock.quant matching the criteria.
        """
        serials = http.request.env['stock.production.lot'].search([(CUSTOMER_FIELD, '=', partner.id)])
        return http.request.env['stock.quant'].search([
            ('lot_id', 'in', serials.ids),
            ('location_id.usage', '=', INTERNAL_USAGE)
        ])
=======
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
        Example:
            >>> self._get_partner_inventory(partner)
            stock.quant(1, 2, 3)
        Edge Cases:
            - Partner has no inventory: returns empty recordset.
            - Large inventory: returns only up to 'limit' records.
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
        Example:
            >>> self._parse_item_ids(form)
            [1, 2, 3]
        Edge Cases:
            - No item_ids: returns None.
            - Non-integer values: returns None.
            - Duplicates: returns unique integers.
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
>>>>>>> 46620db (Update: latest changes)

    def _parse_item_ids(self, form):
        """
        Helper to safely parse item_ids from form data.
        Args:
            form: werkzeug.form object.
        Returns:
            List of item_ids as integers, or None if parsing fails.
        """
        try:
            return [int(id) for id in form.getlist('item_ids')]
        except (ValueError, TypeError):
            return None

    @http.route('/my/inventory/request_pickup', type='http', auth='user', methods=['POST'], csrf=True)
    def request_pickup(self, **kw):
        """
<<<<<<< HEAD
        Handle inventory pickup requests for logged-in users.
        """
        user = http.request.env.user
        partner = user.partner_id
        _logger.info('Inventory accessed by partner ID %s', partner.id)

        item_ids = self._parse_item_ids(http.request.httprequest.form)
        if not item_ids:
            _logger.warning("User ID: %s provided invalid item_ids: %s", user.id, http.request.httprequest.form.getlist('item_ids'))
            # Redirect with error and user friendly message
            return http.request.redirect('/my/inventory?error=invalid_item_ids&message=Please+provide+valid+item+IDs.')

        _logger.info('Pickup requested for items %s by partner ID %s', item_ids, partner.id)
        # ...existing pickup processing code should be placed here...
        return http.request.redirect('/my/inventory?success=pickup_requested')
=======
        Handle pickup requests for inventory items.
        Enhanced logging, error handling, and user feedback.
        """
        user = self._get_current_user()
        partner = self._get_current_partner()
        _logger.info('Pickup request initiated by user %s (ID: %s), partner %s', user.login, user.id, partner.id)
        item_ids = self._parse_item_ids(http.request.httprequest.form)
        if item_ids is None:
            error_msg = (
                "Invalid item selection. Please select valid inventory items. "
                "If the problem persists, contact support."
            )
            _logger.warning("User %s (ID: %s) provided invalid item_ids: %s", user.login, user.id, http.request.httprequest.form.getlist('item_ids'))
            return http.request.redirect('/my/inventory?error=invalid_item_ids')
        try:
            # ...existing code for processing pickup...
            _logger.info('Pickup requested for items %s by partner %s', item_ids, partner.id)
            # On success:
            success_msg = "Pickup request submitted successfully for selected items."
            return http.request.redirect('/my/inventory?success=pickup_requested')
        except Exception as e:
            _logger.error("Error processing pickup request for user %s: %s", user.login, e)
            error_msg = (
                "An error occurred while processing your pickup request. "
                "Please try again later or contact support."
            )
            return http.request.redirect('/my/inventory?error=pickup_failed')
>>>>>>> 46620db (Update: latest changes)

    @http.route('/my/inventory', type='http', auth='user', website=True, methods=['GET'], csrf=True)
    def my_inventory(self, **kw):
        """
<<<<<<< HEAD
        Display inventory relevant to the logged-in user.
        """
        user = http.request.env.user
        partner = user.partner_id
        quants = self._get_partner_inventory(partner)

        # Show error message from query parameters if present
        error = http.request.params.get('error')
        message = http.request.params.get('message', '')
        success = http.request.params.get('success')
        if error:
            message = message or 'There was a problem with your request.'
        elif not quants:
            message = 'No inventory items found. Please contact support if this issue persists.'
        elif success:
            message = 'Your pickup request has been submitted.'

=======
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
        # Add tooltips/explanations for inventory actions
        inventory_tooltips = {
            'pickup': 'Request pickup for selected inventory items. Only available for items in internal locations.'
        }
>>>>>>> 46620db (Update: latest changes)
        return http.request.render(
            'records_management.inventory_template',
            {
                'quants': quants,
<<<<<<< HEAD
                'message': message
=======
                'message': message_ctx['message'],
                'message_type': message_ctx['message_type'],
                'tooltips': inventory_tooltips,
                'page_limit': INVENTORY_PAGE_LIMIT,
>>>>>>> 46620db (Update: latest changes)
            }
        )

    # ...other controller logic can be added here...
