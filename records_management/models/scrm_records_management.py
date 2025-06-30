"""
Records Management Models
Contains the core business logic for the Records Management module.
"""
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)
