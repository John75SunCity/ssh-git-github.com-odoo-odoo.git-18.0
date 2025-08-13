# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

# =============================================================================
# REPORTS MODULE INITIALIZATION - RECORDS MANAGEMENT SYSTEM
# =============================================================================

# Import existing Python report models
try:
    from . import records_tag_report

    _imported_reports = ["records_tag_report"]
    _logger.info("Successfully imported records_tag_report")
except ImportError as e:
    _logger.warning("Could not import records_tag_report: %s", str(e))
    _imported_reports = []

# Import revenue forecasting report
try:
    from . import revenue_forecasting_report

    _imported_reports.append("revenue_forecasting_report")
    _logger.info("Successfully imported revenue_forecasting_report")
except ImportError as e:
    _logger.warning("Could not import revenue_forecasting_report: %s", str(e))

# =============================================================================
# FUTURE PYTHON REPORT MODELS - TO BE DEVELOPED
# =============================================================================

# NOTE: The following Python report models are planned but not yet implemented:
# from . import customer_inventory_report
# from . import container_analytics_report
# from . import naid_compliance_report
# from . import destruction_analytics_report
# from . import billing_analytics_report

_logger.info(
    "Records Management reports module loaded with %d Python report models: %s",
    len(_imported_reports),
    ", ".join(_imported_reports) if _imported_reports else "None",
)
