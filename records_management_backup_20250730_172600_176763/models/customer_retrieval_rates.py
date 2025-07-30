# -*- coding: utf-8 -*-
""",
Legacy Customer Retrieval Rates - MIGRATED TO NEW RATE SYSTEM
This file maintains compatibility while redirecting to the new unified rate system:
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerRetrievalRates(models.Model):
    """,
    LEGACY MODEL - Redirects to customer.rate.profile system
    Use customer.rate.profile with service categories instead:
    """

    _name = "customer.retrieval.rates",
    _description = "Customer Retrieval Rates (Legacy - Use customer.rate.profile)",
    _inherit = ["customer.rate.profile", "mail.thread", "mail.activity.mixin"]

def create(self, vals):
        """Override to set service category to retrieval"""
        # Map legacy fields to new system
if "customer_id" in vals:
            vals["partner_id"] = vals.pop("customer_id")

        # Set default service settings for retrieval:
            vals.update(("profile_type": "service_specific", "service_category": "pickup"))

            return super().create(vals)

    # Legacy field mappings for backward compatibility:
            customer_id = fields.
                                    "profile_type": "service_specific",
                                    "service_category": "pickup",
                                    "adjustment_type": (
"percentage_discount" if rate.discount_rate else "override":
                                        ,
                                        "adjustment_value": rate.discount_rate or 0.0,
"state": "active" if rate.state == "active" else "draft",:
                                            
                                            

            # Create rate adjustments for the specific rates:
if rate.base_rate:
                                                self.env["rate.adjustment"].create(
                                                (
                                                "profile_id": rate.id,
                                                "service_type": "retrieval",
                                                "adjustment_type": "override",
                                                "adjustment_value": rate.base_rate,
                                                "description": f"Base retrieval rate: $(rate.base_rate(
                                    "profile_type": "service_specific",
                                    "service_category": "pickup",
                                    "adjustment_type": (
"percentage_discount" if rate.discount_rate else "override":
                                        ,
                                        "adjustment_value": rate.discount_rate or 0.0,
"state": "active" if rate.state == "active" else "draft",:
                                            
                                            

            # Create rate adjustments for the specific rates:
if rate.base_rate:
                                                self.env["rate.adjustment"].create(
                                                (
                                                "profile_id": rate.id,
                                                "service_type": "retrieval",
                                                "adjustment_type": "override",
                                                "adjustment_value": rate.base_rate,
                                                "description": f"Base retrieval rate: $(rate.base_rate)",
                                                "state": "active",
                                                
                                                

                                                _logger.info("Customer retrieval rates migration completed")
                                                return True)