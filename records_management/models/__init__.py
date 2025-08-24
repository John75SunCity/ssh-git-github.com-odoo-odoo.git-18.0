# -*- coding: utf-8 -*-
"""
Records Management Models - Essential Core Only

Clean import structure with only essential, working models.
All legacy/problematic models removed to prevent circular dependencies.
"""

import logging
_logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION AND SETTINGS
# =============================================================================
from . import res_config_settings
from . import records_config_settings

# =============================================================================
# CORE STRUCTURAL MODELS
# =============================================================================
from . import records_tag_category
from . import records_tag
from . import records_location
from . import records_center_location
from . import records_department
from . import records_department_billing_contact
from . import records_storage_department_user

# =============================================================================
# CONTAINER AND DOCUMENT FOUNDATION
# =============================================================================
from . import records_container
from . import records_container_type
from . import records_document_type
from . import records_service_type
from . import records_document

# =============================================================================
# CUSTOMER MANAGEMENT
# =============================================================================
from . import res_partner
from . import customer_category

# =============================================================================
# INVENTORY MANAGEMENT
# =============================================================================
from . import inventory_item_type
from . import inventory_item_profile
from . import inventory_item
from . import customer_inventory

# =============================================================================
# BASIC SERVICES
# =============================================================================
from . import shredding_team
from . import shredding_certificate
from . import shredding_service
from . import destruction_item

# =============================================================================
# CORE BILLING (Single System)
# =============================================================================
from . import records_billing
from . import records_billing_line
from . import records_billing_contact
from . import records_billing_config

# =============================================================================
# PICKUP AND TRANSPORTATION
# =============================================================================
from . import pickup_request
from . import pickup_request_item
from . import pickup_route

# =============================================================================
# PORTAL
# =============================================================================
from . import portal_request
from . import customer_feedback

# =============================================================================
# CONFIGURATION
# =============================================================================
from . import rm_module_configurator

_logger.info("Records Management essential models loaded successfully")
