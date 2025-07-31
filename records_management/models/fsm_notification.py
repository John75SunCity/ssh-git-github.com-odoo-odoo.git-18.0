# -*- coding: utf-8 -*-
# FSM Notification - Temporarily disabled until industry_fsm is available
# This file is loaded conditionally by models/__init__.py

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

# Temporarily create a placeholder model that doesn't use fsm.task
# This prevents the "Model 'fsm.task' does not exist in registry" error
class FsmNotificationPlaceholder(models.TransientModel):
    _name = "fsm.notification.placeholder"
    _description = "Placeholder for FSM Notification Manager"
    
    # Log that FSM features are disabled
    def __init__(self, pool, cr):
        super(FsmNotificationPlaceholder, self).__init__(pool, cr)
        _logger.info("FSM Notification extensions are disabled - industry_fsm module not available")

# TODO: When industry_fsm is available, restore the original FSM notification code
# The code includes send_day_of_service_notification and send_driver_nearby_notification methods
