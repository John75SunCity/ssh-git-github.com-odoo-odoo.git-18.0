# -*- coding: utf-8 -*-
"""
HR Timesheet Compatibility Patch for Odoo 18.0

This module provides compatibility patches for hr_timesheet module
API changes in Odoo 18.0, specifically addressing the _compute_domain()
method signature change in portal domain computation.

The issue: hr_timesheet calls self.env['ir.rule']._compute_domain(self._name)
but Odoo 18.0 requires: self.env['ir.rule']._compute_domain(self._name, 'read')

Author: Records Management System  
Version: 18.0.1.0.3
License: LGPL-3
"""

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class HrTimesheetCompat(models.Model):
    """Compatibility patch for hr.timesheet API changes in Odoo 18.0"""
    _inherit = 'account.analytic.line'

    def _timesheet_get_portal_domain(self):
        """
        Override to fix Odoo 18.0 API compatibility issue.
        
        The base hr_timesheet method contains:
            return self.env['ir.rule']._compute_domain(self._name)
            
        But Odoo 18.0 requires:
            return self.env['ir.rule']._compute_domain(self._name, 'read')
        """
        try:
            # Try parent method first (might work if already patched)
            return super()._timesheet_get_portal_domain()
        except TypeError as e:
            if '_compute_domain() missing 1 required positional argument' in str(e):
                _logger.info("Records Management: Applying hr_timesheet compatibility patch for Odoo 18.0")
                # Apply the fix - use 'read' mode for portal domain computation
                return self.env['ir.rule']._compute_domain(self._name, 'read')
            else:
                # Different error - re-raise
                raise
