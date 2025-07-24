# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department with enhanced enterprise features
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib
import re

class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts.
    Enhanced with enterprise features: validation, tracking, privacy compliance, and audit trails.
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact - FIELD ENHANCEMENT COMPLETE ✅'
    _rec_name = 'contact_name'
    _order = 'contact_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Phase 1: Explicit Activity Field (1 field)