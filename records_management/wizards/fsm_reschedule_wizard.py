# -*- coding: utf-8 -*-
# FSM Reschedule Wizard - Temporarily disabled until industry_fsm is available

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

# Temporarily create a placeholder wizard that doesn't use fsm.task
# This prevents the "Model 'fsm.task' does not exist in registry" error
class FsmRescheduleWizardPlaceholder(models.TransientModel):
    _name = "fsm.reschedule.wizard.placeholder"
    _description = "Placeholder for FSM Reschedule Wizard"
    
    # Log that FSM features are disabled
    def __init__(self, pool, cr):
        super(FsmRescheduleWizardPlaceholder, self).__init__(pool, cr)
        _logger.info("FSM Reschedule Wizard is disabled - industry_fsm module not available")

# TODO: When industry_fsm is available, restore the original FSM reschedule wizard code
# The code includes task_id Many2one field and action_confirm_reschedule method
