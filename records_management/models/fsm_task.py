# -*- coding: utf-8 -*-
# FSM Task Extensions - Temporarily disabled until industry_fsm is available
# This file is loaded conditionally by models/__init__.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Temporarily create a placeholder model that doesn't inherit from fsm.task
# This prevents the "Model 'fsm.task' does not exist in registry" error
class FsmTaskPlaceholder(models.TransientModel):
    _name = "fsm.task.placeholder"
    _description = "Placeholder for FSM Task Extensions"
    
    # Simple placeholder field to make this a valid model
    name = fields.Char("Placeholder Name", default="FSM Task Placeholder")
    
    @api.model
    def _log_fsm_disabled(self):
        """Log that FSM features are disabled"""
        _logger.info("FSM Task extensions are disabled - industry_fsm module not available")

# TODO: When industry_fsm is available, replace this with:
# class FsmTask(models.Model):
#     _inherit = "fsm.task"
#     # Include all the original FSM task extension fields and methods:
#     # - customer_balance, invoice_payment_status, company_currency_id
#     # - reschedule_reason field
#     # - _compute_customer_balance method
#     # - action_reschedule_wizard and action_reschedule_remaining_tasks methods
