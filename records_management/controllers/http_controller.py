# -*- coding: utf-8 -*-
"""
Records Management HTTP Controller

This controller provides HTTP endpoints for inventory management operations,
pickup requests, and customer portal interactions. It implements enterprise-grade
error handling, logging, and security controls for the Records Management System.

Key Features:
- Customer inventory display and management
- Pickup request processing with validation
- Comprehensive error handling and user feedback
- Performance optimization with pagination
- NAID compliance audit logging
"""

import logging
from odoo.http import request

from odoo import http, fields, _

from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

# Constants
CUSTOMER_FIELD = 'customer_id'
INTERNAL_USAGE = 'internal'
INVENTORY_PAGE_LIMIT = 100  # Limit for scalability


class RecordsManagementController(http.Controller):
    """
    Controller for managing inventory-related HTTP requests and portal operations.
    Handles customer inventory display, pickup requests, and service interactions.
    """

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _get_current_user(self):
        """
        Helper to get the current Odoo user.
        Returns:
            res.users recordset
        """
        return request.env.user

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
            serials = request.env['stock.lot'].search([(CUSTOMER_FIELD, '=', partner.id)])
            if not serials:
                _logger.info("No serials found for partner %s", partner.id)
                return request.env['stock.quant'].browse([])

            quants = request.env['stock.quant'].search([
                ('lot_id', 'in', serials.ids),
                ('location_id.usage', '=', INTERNAL_USAGE)
            ], limit=limit)

            _logger.info("Fetched %d inventory items for partner %s", len(quants), partner.id)
            return quants

        except Exception as e:
            _logger.error("Database error fetching inventory for partner %s: %s", partner.id, e)
            return request.env['stock.quant'].browse([])

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

    def _create_naid_audit_log(self, action_type, partner_id, item_ids=None, notes=None):
        """
        Create NAID compliance audit log for customer actions.
        Args:
            action_type (str): Type of action performed
            partner_id (int): Customer partner ID
            item_ids (list): List of affected item IDs
            notes (str): Additional notes
        """
        try:
            audit_vals = {
                "name": _("Customer Portal Action: %s") % action_type,
                "action_type": action_type,
                "partner_id": partner_id,
                "user_id": request.env.user.id,
                "action_date": fields.Datetime.now(),
                "notes": notes or "",
            }

            if item_ids:
                audit_vals['affected_item_ids'] = [(6, 0, item_ids)]

            request.env['naid.audit.log'].sudo().create(audit_vals)
            _logger.info("NAID audit log created for action: %s, partner: %s", action_type, partner_id)

        except Exception as e:
            _logger.error("Failed to create NAID audit log: %s", e)

    # ============================================================================
    # HTTP ROUTE HANDLERS
    # ============================================================================

    @http.route('/my/inventory/request_pickup', type='http', auth='user', methods=['POST'], csrf=True)
    def request_pickup(self, **post):
        """
        Handle pickup requests for inventory items.
        Enhanced logging, error handling, and user feedback.
        """
        current_user = self._get_current_user()
        partner = self._get_current_partner()

        _logger.info('Pickup request initiated by user %s (ID: %s), partner %s',
                    current_user.login, current_user.id, partner.id)

        # Validate user has permission
        if not request.env.user.has_group('base.group_portal'):
            _logger.warning("Unauthorized pickup request attempt by user %s", current_user.login)
            return request.redirect('/my/inventory?error=access_denied')

        # Parse and validate item IDs
        item_ids = self._parse_item_ids(request.httprequest.form)
        if item_ids is None:
            _logger.warning("User %s (ID: %s) provided invalid item_ids: %s",
                          current_user.login, current_user.id,
                          request.httprequest.form.getlist('item_ids'))
            return request.redirect('/my/inventory?error=invalid_item_ids')

        try:
            # Validate items belong to customer
            quants = request.env['stock.quant'].search([
                ('id', 'in', item_ids),
                ('lot_id.customer_id', '=', partner.id)
            ])

            if len(quants) != len(item_ids):
                _logger.warning("Some items don't belong to partner %s: requested %s, found %s",
                              partner.id, item_ids, quants.ids)
                return request.redirect('/my/inventory?error=unauthorized_items')

            # Create pickup request
            pickup_vals = {
                "name": _("Portal Pickup Request - %s") % partner.name,
                "partner_id": partner.id,
                "request_type": "pickup",
                "priority": "normal",
                "state": "submitted",
                "requested_by": current_user.id,
                "notes": post.get("notes", ""),
                "pickup_date": post.get("preferred_date"),
            }

            pickup_request = request.env['portal.request'].create(pickup_vals)

            # Create pickup request items
            for quant in quants:
                request.env['pickup.request.item'].create({
                    'pickup_request_id': pickup_request.id,
                    'quant_id': quant.id,
                    'product_id': quant.product_id.id,
                    'quantity': quant.quantity,
                    'location_id': quant.location_id.id,
                })

            # Create NAID audit log
            self._create_naid_audit_log(
                "pickup_request_submitted",
                partner.id,
                item_ids,
                _("Portal pickup request created: %s") % pickup_request.name,
            )

            # Send notification to operations team
            pickup_request.message_post(
                body=_("New pickup request submitted via customer portal by %s") % current_user.name,
                message_type="notification",
            )

            _logger.info('Pickup request %s created for items %s by partner %s',
                        pickup_request.name, item_ids, partner.id)

            return request.redirect('/my/inventory?success=pickup_requested')

        except ValidationError as e:
            _logger.warning("Validation error in pickup request for user %s: %s", current_user.login, e)
            return request.redirect('/my/inventory?error=validation_failed')

        except Exception as e:
            _logger.error("Error processing pickup request for user %s: %s", current_user.login, e)
            return request.redirect('/my/inventory?error=pickup_failed')

    @http.route('/my/inventory', type='http', auth='user', website=True, methods=['GET'], csrf=True)
    def my_inventory(self, **get):
        """
        Render the inventory page for the current user.
        Enhanced with pagination, user-friendly messages, and tooltips.
        """
        partner = self._get_current_partner()

        # Extract URL parameters
        error = request.params.get('error')
        success = request.params.get('success')
        page = int(request.params.get('page', 1))
        search_term = get.get('search', '').strip()

        # Handle messages
        message_ctx = self._handle_message(
            error=self._get_error_message(error),
            success=self._get_success_message(success)
        )

        # Get inventory with pagination and search
        domain = [
            ('lot_id.customer_id', '=', partner.id),
            ('location_id.usage', '=', INTERNAL_USAGE)
        ]

        if search_term:
            domain.extend(['|', '|',
                ('lot_id.name', 'ilike', search_term),
                ('product_id.name', 'ilike', search_term),
                ('location_id.name', 'ilike', search_term)
            ])

        offset = (page - 1) * INVENTORY_PAGE_LIMIT
        quants = request.env['stock.quant'].search(
            domain,
            limit=INVENTORY_PAGE_LIMIT,
            offset=offset,
            order='write_date desc'
        )

        # Get total count for pagination
        total_count = request.env['stock.quant'].search_count(domain)

        # Calculate pagination info
        total_pages = (total_count + INVENTORY_PAGE_LIMIT - 1) // INVENTORY_PAGE_LIMIT

        if not quants and not error:
            message_ctx['message'] = 'No inventory items found. If you believe this is an error, please contact support.'
            message_ctx['message_type'] = 'info'

        # Prepare context data
        inventory_tooltips = {
            'pickup': 'Request pickup for selected inventory items. Only available for items in internal locations.',
            'location': 'Current storage location of your documents.',
            'quantity': 'Number of items in this location.',
            'last_update': 'Date when this inventory record was last updated.'
        }

        context = {
            'quants': quants,
            'message': message_ctx['message'],
            'message_type': message_ctx['message_type'],
            'tooltips': inventory_tooltips,
            'page_limit': INVENTORY_PAGE_LIMIT,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'partner': partner,
            'search_term': search_term,
        }

        return request.render('records_management.inventory_template', context)

    @http.route('/my/inventory/data', type='json', auth='user', methods=['POST'])
    def get_inventory_data(self, **post):
        """
        JSON endpoint for AJAX inventory data retrieval.
        """
        partner = self._get_current_partner()

        try:
            page = int(post.get('page', 1))
            search_term = post.get('search', '').strip()

            domain = [
                ('lot_id.customer_id', '=', partner.id),
                ('location_id.usage', '=', INTERNAL_USAGE)
            ]

            # Add search filter if provided
            if search_term:
                domain.extend(['|', '|',
                    ('lot_id.name', 'ilike', search_term),
                    ('product_id.name', 'ilike', search_term),
                    ('location_id.name', 'ilike', search_term)
                ])

            offset = (page - 1) * INVENTORY_PAGE_LIMIT
            quants = request.env['stock.quant'].search(
                domain,
                limit=INVENTORY_PAGE_LIMIT,
                offset=offset,
                order='write_date desc'
            )

            # Prepare data for JSON response
            inventory_data = []
            for quant in quants:
                inventory_data.append({
                    'id': quant.id,
                    'product_name': quant.product_id.display_name,
                    'lot_name': quant.lot_id.name,
                    'location_name': quant.location_id.complete_name,
                    'quantity': quant.quantity,
                    'last_update': quant.write_date.strftime('%Y-%m-%d') if quant.write_date else '',
                })

            total_count = request.env['stock.quant'].search_count(domain)

            return {
                'success': True,
                'data': inventory_data,
                'total_count': total_count,
                'page': page,
                'page_limit': INVENTORY_PAGE_LIMIT
            }

        except Exception as e:
            _logger.error("Error fetching inventory data: %s", e)
            return {
                'success': False,
                'error': 'Failed to load inventory data'
            }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _get_error_message(self, error_code):
        """Get user-friendly error message for error code."""
        error_messages = {
            'invalid_item_ids': 'Invalid item selection. Please select valid inventory items.',
            'pickup_failed': 'An error occurred while processing your pickup request. Please try again later.',
            'access_denied': 'Access denied. Please ensure you have proper permissions.',
            'unauthorized_items': 'Some selected items do not belong to your account.',
            'validation_failed': 'Request validation failed. Please check your input and try again.',
            'request_not_found': 'The requested service request was not found or you do not have permission to view it.'
        }
        return error_messages.get(error_code)

    def _get_success_message(self, success_code):
        """Get user-friendly success message for success code."""
        success_messages = {
            'pickup_requested': 'Pickup request submitted successfully! You will receive confirmation shortly.',
            'request_updated': 'Your request has been updated successfully.',
            'feedback_submitted': 'Thank you for your feedback. We will review it shortly.'
        }
        return success_messages.get(success_code)

    @http.route('/my/requests', type='http', auth='user', website=True, methods=['GET'])
    def my_requests(self, **get):
        """
        Display customer's service requests.
        """
        partner = self._get_current_partner()
        page = int(get.get('page', 1))
        search_term = get.get('search', '').strip()

        # Build domain for customer requests
        domain = [('partner_id', '=', partner.id)]

        if search_term:
            domain.extend(['|', '|',
                ('name', 'ilike', search_term),
                ('request_type', 'ilike', search_term),
                ('state', 'ilike', search_term)
            ])

        # Get requests with pagination
        offset = (page - 1) * INVENTORY_PAGE_LIMIT
        requests = request.env['portal.request'].search(
            domain,
            limit=INVENTORY_PAGE_LIMIT,
            offset=offset,
            order='create_date desc'
        )

        total_count = request.env['portal.request'].search_count(domain)
        total_pages = (total_count + INVENTORY_PAGE_LIMIT - 1) // INVENTORY_PAGE_LIMIT

        context = {
            'requests': requests,
            'partner': partner,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'search_term': search_term,
        }

        return request.render('records_management.my_requests_template', context)

    @http.route('/my/requests/<int:request_id>', type='http', auth='user', website=True, methods=['GET'])
    def my_request_detail(self, request_id, **get):
        """
        Display detailed view of a specific request.
        """
        partner = self._get_current_partner()

        # Get request and verify ownership
        customer_request = request.env['portal.request'].search([
            ('id', '=', request_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not customer_request:
            return request.redirect('/my/requests?error=request_not_found')

        # Get related items if this is a pickup request
        pickup_items = request.env['pickup.request.item'].search([
            ('pickup_request_id.portal_request_id', '=', customer_request.id)
        ]) if customer_request.request_type == 'pickup' else request.env['pickup.request.item']

        context = {
            'request': customer_request,
            'partner': partner,
            'pickup_items': pickup_items,
            'can_cancel': customer_request.state in ['draft', 'submitted'],
        }

        return request.render('records_management.my_request_detail_template', context)

    @http.route('/my/requests/<int:request_id>/cancel', type='http', auth='user', methods=['POST'], csrf=True)
    def cancel_request(self, request_id, **post):
        """
        Cancel a customer request if allowed.
        """
        partner = self._get_current_partner()

        # Get request and verify ownership
        customer_request = request.env['portal.request'].search([
            ('id', '=', request_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not customer_request:
            return request.redirect('/my/requests?error=request_not_found')

        if customer_request.state not in ['draft', 'submitted']:
            return request.redirect('/my/requests/%d?error=cannot_cancel' % request_id)

        try:
            # Cancel the request
            customer_request.write({
                'state': 'cancelled',
                'cancellation_reason': post.get('reason', ''),
            })

            # Create audit log
            self._create_naid_audit_log(
                "request_cancelled", partner.id, notes=_("Request cancelled by customer: %s") % customer_request.name
            )

            return request.redirect('/my/requests?success=request_cancelled')

        except Exception as e:
            _logger.error("Error cancelling request %d: %s", request_id, e)
            return request.redirect('/my/requests/%d?error=cancel_failed' % request_id)

    @http.route('/my/feedback', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def submit_feedback(self, **post):
        """
        Handle customer feedback submission.
        """
        partner = self._get_current_partner()

        if request.httprequest.method == 'POST':
            try:
                feedback_vals = {
                    "name": post.get("subject", _("Feedback from %s") % partner.name),
                    "partner_id": partner.id,
                    "rating": post.get("rating"),
                    "comments": post.get("comments", ""),
                    "feedback_type": post.get("feedback_type", "general"),
                    "submitted_via": "portal",
                }

                feedback = request.env['customer.feedback'].create(feedback_vals)

                # Create audit log
                self._create_naid_audit_log(
                    "feedback_submitted", partner.id, notes=_("Customer feedback submitted: %s") % feedback.name
                )

                return request.redirect('/my/feedback?success=feedback_submitted')

            except Exception as e:
                _logger.error("Error submitting feedback: %s", e)
                return request.redirect('/my/feedback?error=submission_failed')

        # GET request - show feedback form
        error = request.params.get('error')
        success = request.params.get('success')

        message_ctx = self._handle_message(
            error=self._get_error_message(error),
            success=self._get_success_message(success)
        )

        context = {
            'partner': partner,
            'message': message_ctx['message'],
            'message_type': message_ctx['message_type'],
        }

        return request.render('records_management.feedback_form_template', context)
