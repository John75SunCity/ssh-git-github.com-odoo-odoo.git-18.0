# -*- coding: utf-8 -*-
# FSM Route Management - Temporarily disabled until industry_fsm is available
# This file is loaded conditionally by models/__init__.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

# Temporarily create a placeholder model that doesn't use fsm.task
# This prevents the "Model 'fsm.task' does not exist in registry" error
class FsmRouteManagementPlaceholder(models.TransientModel):
    _name = "fsm.route.management.placeholder"
    _description = "Placeholder for FSM Route Management"
    
    # Simple placeholder field to make this a valid model
    name = fields.Char("Placeholder Name", default="FSM Route Management Placeholder")
    
    @api.model
    def _log_fsm_disabled(self):
        """Log that FSM features are disabled"""
        _logger.info("FSM Route Management extensions are disabled - industry_fsm module not available")

# TODO: When industry_fsm is available, restore the original FSM route management code
# The code includes reschedule_remaining_for_driver, create_follow_up_task, 
# _get_next_business_day, and other route management methods
