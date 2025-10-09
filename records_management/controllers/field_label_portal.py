# -*- coding: utf-8 -*-
"""
Field Label Customization Portal Controller

Provides API endpoints for getting custom field labels in portal interfaces.
Supports customer-specific field label customization and transitory field
configuration for Records Management portal operations.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

# Standard library imports
import csv
import io
import logging
import re

# Third-party imports
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

from werkzeug.wrappers import Response

# Odoo core imports
from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request

# Odoo addons imports
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class FieldLabelPortalController(CustomerPortal):
    """
    Portal controller for field label customization

    Provides API endpoints for retrieving custom field labels and configurations
    for portal users, enabling customer-specific field naming conventions.
    """

    @http.route(
        ["/portal/field-labels/get"],
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def get_field_labels(self, customer_id=None, department_id=None):
        """
        API endpoint to get custom field labels for a customer/department

        Args:
            customer_id (int, optional): Customer ID for label context
            department_id (int, optional): Department ID for specific context

        Returns:
            dict: Success status and field labels or error message
        """
        try:
            # Validate portal access
            if not request.env.user.has_group("base.group_portal"):
                return {"error": _("Access denied - Portal access required")}

            # Determine customer context
            resolved_customer_id = self._resolve_customer_id(customer_id)
            if not resolved_customer_id:
                return {"error": _("No customer context available")}

            # Get field labels with proper security context
            labels = (
                request.env["field.label.customization"]
                .sudo()
                .get_labels_for_context(
                    customer_id=resolved_customer_id, department_id=department_id
                )
            )

            return {
                "success": True,
                "labels": labels,
                "customer_id": resolved_customer_id,
                "department_id": department_id,
            }

        except AccessError as e:
            _logger.warning("Access denied in get_field_labels: %s", str(e))
            return {"error": _("Access denied")}
        except Exception as e:
            _logger.error("Error in get_field_labels: %s", str(e))
            return {"error": _("Failed to retrieve field labels")}

    def _resolve_customer_id(self, provided_customer_id):
        """
        Resolve customer ID from provided value or current user context

        Args:
            provided_customer_id (int, optional): Explicitly provided customer ID

        Returns:
            int: Resolved customer ID or None
        """
        if provided_customer_id:
            return int(provided_customer_id)

        # Try to get from current user's partner context
        user_partner = request.env.user.partner_id

        if user_partner.is_company:
            return user_partner.id
        elif user_partner.parent_id:
            return user_partner.parent_id.id

        return None


class FieldLabelAdminController(http.Controller):
    """
    Administrative controller for field label management

    Provides management interface for Records Management administrators
    to preview and configure field label customizations.
    """

    @http.route(
        ["/records/admin/field-labels/preview"],
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def preview_field_labels(self, customer_id=None, department_id=None):
        """
        Preview field labels for admin users

        Args:
            customer_id (int, optional): Customer ID for preview context
            department_id (int, optional): Department ID for preview context

        Returns:
            dict: Field labels and configuration preview
        """
        try:
            # Validate manager access
            if not request.env.user.has_group(
                "records_management.group_records_manager"
            ):
                return {"error": _("Access denied - Manager access required")}

            # Get field labels for preview
            labels = request.env["field.label.customization"].get_labels_for_context(
                customer_id=customer_id, department_id=department_id
            )

            return {
                "success": True,
                "labels": labels,
                "preview_context": {
                    "customer_id": customer_id,
                    "department_id": department_id,
                },
            }

        except AccessError as e:
            _logger.warning("Access denied in preview_field_labels: %s", str(e))
            return {"error": _("Access denied")}
        except Exception as e:
            _logger.error("Error in preview_field_labels: %s", str(e))
            return {"error": _("Preview failed")}
