# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class LiveMonitor(models.Model):
    _name = 'live.monitor'
    _description = 'Live Monitoring System'
    
    name = fields.Char(string='Monitor Name', required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active')
    
    def check_status(self):
        """Check monitoring status."""
        _logger.info(f"Checking status for monitor: {self.name}")
        return True
