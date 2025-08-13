# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# =============================================================================
# EXISTING REPORTS - ONLY IMPORT WHAT EXISTS
# =============================================================================

# Records tag report (confirmed to exist)
from . import records_tag_report

# =============================================================================
# FUTURE REPORTS - TO BE DEVELOPED
# =============================================================================

# NOTE: The following reports are planned but not yet implemented:
# - customer_inventory_report
# - location_report
# - destruction_certificate_report
# - naid_compliance_report
# - container_movement_report
# - document_lifecycle_report
# - pickup_schedule_report
# - shredding_service_report
# - revenue_forecasting_report
# - billing_summary_report
# - customer_rates_report
# - naid_audit_trail_report
# - chain_of_custody_report
# - compliance_dashboard_report
# - management_dashboard
# - kpi_tracking_report
# - performance_analytics_report

_logger.info(
    "Records Management reports module loaded with %d report types", 1
)
