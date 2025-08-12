# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# =============================================================================
# CUSTOMER REPORTS AND ANALYTICS
# =============================================================================

# Customer-facing reports
from . import customer_inventory_report
from . import location_report
from . import destruction_certificate_report
from . import naid_compliance_report

# =============================================================================
# OPERATIONAL REPORTS
# =============================================================================

# Container and document reports
from . import container_movement_report
from . import document_lifecycle_report
from . import pickup_schedule_report
from . import shredding_service_report

# =============================================================================
# FINANCIAL AND BILLING REPORTS
# =============================================================================

# Revenue and billing analytics
from . import revenue_forecasting_report
from . import billing_summary_report
from . import customer_rates_report

# =============================================================================
# COMPLIANCE AND AUDIT REPORTS
# =============================================================================

# NAID and audit reports
from . import naid_audit_trail_report
from . import chain_of_custody_report
from . import compliance_dashboard_report

# =============================================================================
# MANAGEMENT DASHBOARDS AND KPIs
# =============================================================================

# Executive dashboards
from . import management_dashboard
from . import kpi_tracking_report
from . import performance_analytics_report

# =============================================================================
# CONDITIONAL REPORT IMPORTS
# =============================================================================

# Import additional report models conditionally
try:
    from . import custom_report_builder
    from . import advanced_analytics_report
    _logger.info("Advanced reporting modules loaded successfully")
except (ImportError, AttributeError) as e:
    _logger.warning("Advanced reporting not available: %s", str(e))

try:
    from . import mobile_report_access
    from . import portal_report_integration
    _logger.info("Portal reporting integration loaded successfully")
except (ImportError, AttributeError) as e:
    _logger.warning("Portal reporting extensions not available: %s", str(e))
